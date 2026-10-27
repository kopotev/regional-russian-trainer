import {test} from 'node:test';
import assert from 'node:assert/strict';
import {webcrypto} from 'node:crypto';
import {createRuntime,checkedCount,qualifies,RNC_ORIGIN,RNC_RESOURCE} from './runtime.mjs';
if(!globalThis.crypto)globalThis.crypto=webcrypto;

// R2 documents conditional PUT returning null on a failed precondition and
// strongly consistent writes. This fixture reproduces that contract, including
// wildcard If-None-Match and quoted If-Match headers (not a non-atomic lock).
class Bucket{
  data=new Map();version=0;
  async get(key){const x=this.data.get(key);return x?{etag:x.etag,json:async()=>JSON.parse(x.text),text:async()=>x.text}:null;}
  async put(key,text,options={}){
    const old=this.data.get(key),condition=options.onlyIf;
    if(condition instanceof Headers){
      const match=condition.get('If-Match'),none=condition.get('If-None-Match');
      if(match&&(!old||match!==('"'+old.etag+'"')))return null;
      if(none==='*'&&old)return null;
    }else if(condition){throw Error('Expected documented conditional Headers');}
    const etag='etag-'+(++this.version);this.data.set(key,{text:String(text),etag});return{etag};
  }
  async delete(key){this.data.delete(key);}
}
const json=(value,status=200,headers={})=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json',...headers}});
const row=(hits=40,texts=20,words=1000000)=>({ok:true,hits,texts,denominatorWords:words,denominatorSource:'subcorpus',ipm:hits*1e6/words,emptyQueryStatsInterpretedAsZero:false});
const envelope=r=>({jsonrpc:'2.0',id:'test',result:{structuredContent:{results:[r]}}});
function harness({pool=[{lemma:'слово',pos:'S'},{lemma:'другой',pos:'A'}],network,words=[{lemma:'слово',pos:'S',definition:{ru:'слово',en:'word'}}]}={}){
  const bucket=new Bucket(),calls=[];let clock=Date.parse('2026-10-26T20:00:00Z');
  const fetchImpl=async(url,init)=>{
    calls.push({url,init});
    if(network){const answer=await network(url,init,calls);if(answer)return answer;}
    if(url.endsWith('/oauth/register'))return json({client_id:'public-client'},201);
    if(url.endsWith('/oauth/token'))return json({access_token:'private-access',refresh_token:'private-refresh',expires_in:3600});
    if(url===RNC_RESOURCE)return json(envelope(row()));
    throw Error('Unexpected URL '+url);
  };
  const app=createRuntime({html:'<!doctype html><h1>Trainer</h1>',words,candidates:pool,fetchImpl,now:()=>clock});
  const env={BUCKET:bucket,SESSION_SECRET:'test-session-secret'};
  async function req(path,{method='GET',body={},user='owner',token,headers={}}={}){
    const h={'oai-authenticated-user-id':user,...headers};
    if(method==='POST'){h.Origin='https://trainer.example';h['Content-Type']='application/json';if(token)h['X-CSRF-Token']=token;}
    const res=await app.fetch(new Request('https://trainer.example'+path,{method,headers:h,...(method==='POST'?{body:JSON.stringify(body)}:{})}),env);
    let data;try{data=await res.clone().json();}catch{data=await res.clone().text();}return {res,data};
  }
  async function config(user='owner'){return (await req('/api/config',{user})).data;}
  async function connect(user='owner'){
    const cfg=await config(user),start=await req('/api/rnc/connect',{method:'POST',token:cfg.csrf_token,user});
    const auth=new URL(start.data.authorize_url),callback='/api/rnc/callback?'+new URLSearchParams({state:auth.searchParams.get('state'),code:'valid-code',iss:RNC_ORIGIN});
    const done=await req(callback,{user});assert.equal(done.res.status,303);return {cfg,auth,callback};
  }
  async function create(target=1,country='Финляндия',idem='request-key-123',user='owner'){
    const cfg=await config(user);return req('/api/jobs',{method:'POST',user,token:cfg.csrf_token,headers:{'Idempotency-Key':idem},body:{country,target_words:target}});
  }
  async function action(id,name,user='owner'){const cfg=await config(user);return req('/api/jobs/'+id+'/'+name,{method:'POST',token:cfg.csrf_token,user});}
  return {app,env,bucket,calls,req,config,connect,create,action,now:()=>clock,setClock:v=>clock=v,advance:v=>clock+=v};
}

test('anonymous users and cross-origin POSTs cannot use server operations',async()=>{
  const h=harness();const missing=await h.app.fetch(new Request('https://trainer.example/api/config'),h.env);assert.equal(missing.status,401);
  const cfg=await h.config();const res=await h.app.fetch(new Request('https://trainer.example/api/rnc/connect',{method:'POST',headers:{'oai-authenticated-user-id':'owner','Origin':'https://evil.example','Content-Type':'application/json','X-CSRF-Token':cfg.csrf_token},body:'{}'}),h.env);assert.equal(res.status,403);assert.equal(h.calls.length,0);
});
test('OAuth public-client PKCE state is bound to the Site visitor and single-use',async()=>{
  const h=harness(),cfg=await h.config();assert.equal(cfg.collector_available,false);
  const result=await h.req('/api/rnc/connect',{method:'POST',token:cfg.csrf_token});const auth=new URL(result.data.authorize_url);
  assert.equal(auth.origin,RNC_ORIGIN);assert.equal(auth.searchParams.get('resource'),RNC_RESOURCE);assert.equal(auth.searchParams.get('code_challenge_method'),'S256');assert.equal(auth.searchParams.get('scope'),'rnc:read offline_access');
  const registration=JSON.parse(h.calls[0].init.body);assert.equal(registration.token_endpoint_auth_method,'none');assert.deepEqual(registration.redirect_uris,['https://trainer.example/api/rnc/callback']);
  const callback='/api/rnc/callback?'+new URLSearchParams({state:auth.searchParams.get('state'),code:'code',iss:RNC_ORIGIN});
  assert.equal((await h.req(callback,{user:'intruder'})).res.status,400);
  assert.equal((await h.req(callback)).res.status,303);assert.equal((await h.req(callback)).res.status,400);
  const ready=await h.config();assert.equal(ready.rnc_connected,true);assert.equal(ready.execution_mode,'foreground_steps');assert.ok(!JSON.stringify(ready).includes('private-'));
  const exchange=new URLSearchParams(h.calls.find(c=>c.url.endsWith('/oauth/token')).init.body);const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(exchange.get('code_verifier')));
  assert.equal(Buffer.from(digest).toString('base64url'),auth.searchParams.get('code_challenge'));
  assert.ok(h.calls.every(c=>!c.init.headers.Origin));
});
test('OAuth issuer mismatch and expired state are rejected without token exchange',async()=>{
  const h=harness(),cfg=await h.config();const start=await h.req('/api/rnc/connect',{method:'POST',token:cfg.csrf_token});const auth=new URL(start.data.authorize_url),state=auth.searchParams.get('state');
  assert.equal((await h.req('/api/rnc/callback?'+new URLSearchParams({state,code:'x',iss:'https://evil.example'}))).res.status,400);
  h.advance(601000);assert.equal((await h.req('/api/rnc/callback?'+new URLSearchParams({state,code:'x',iss:RNC_ORIGIN}))).res.status,400);assert.equal(h.calls.length,1);
});
test('no count is sent by job creation, GET status, or an unconnected visitor',async()=>{
  const h=harness();assert.equal((await h.create()).res.status,409);await h.connect();const created=await h.create();assert.equal(created.res.status,201);
  await h.req('/api/jobs/'+created.data.id);await h.req('/api/jobs');assert.equal(h.calls.filter(c=>c.url===RNC_RESOURCE).length,0);
  assert.equal((await h.req('/api/jobs/'+created.data.id,{user:'other'})).res.status,404);
});
test('each step issues only one singleton count and preserves exact query selection',async()=>{
  let counts=0;const h=harness({network:(url)=>url===RNC_RESOURCE?json(envelope(++counts===1?row(40,20,1000000):row(10,10,1000000))):null});await h.connect();const j=(await h.create()).data;
  let s=await h.action(j.id,'step');assert.equal(s.data.requests_completed,1);assert.equal(s.data.processed_candidates,0);assert.equal(s.data.status,'ready');
  s=await h.action(j.id,'step');assert.equal(s.data.requests_completed,2);assert.equal(s.data.qualified_words,1);assert.equal(s.data.status,'complete');
  const calls=h.calls.filter(c=>c.url===RNC_RESOURCE);assert.equal(calls.length,2);
  for(const call of calls){const body=JSON.parse(call.init.body);assert.equal(body.params.name,'batchCount');assert.equal(body.params.arguments.queries.length,1);assert.equal(body.params.arguments.queries[0].query.corpus.type,'GICR');}
  assert.ok(calls[0].init.body.includes('Финляндия'));assert.ok(calls[1].init.body.includes('Россия'));
  const final=(await h.req('/api/jobs/'+j.id+'/final.json')).data;assert.equal(final.words.length,1);assert.equal(final.semantic_status,'not_semantically_verified');assert.ok(!JSON.stringify(final).includes('private-access'));
});
test('low target counts skip the reference count',async()=>{
  const h=harness({pool:[{lemma:'редкий',pos:'A'}],network:url=>url===RNC_RESOURCE?json(envelope(row(19,10))):null});await h.connect();const j=(await h.create()).data,s=await h.action(j.id,'step');assert.equal(s.data.status,'exhausted');assert.equal(s.data.requests_completed,1);assert.equal(s.data.completed_comparisons,0);assert.equal((await h.req('/api/jobs/'+j.id+'/final.json')).data.words.length,0);
});
test('a repeated lemma with different POS does not inflate distinct passing words',async()=>{
  let n=0;const h=harness({pool:[{lemma:'слово',pos:'S'},{lemma:'слово',pos:'A'}],network:url=>url===RNC_RESOURCE?json(envelope(row(++n%2?40:10,10))):null});await h.connect();const j=(await h.create(2)).data;let s;for(let i=0;i<4;i++)s=await h.action(j.id,'step');assert.equal(s.data.status,'exhausted');assert.equal(s.data.qualified_words,1);assert.equal(s.data.completed_comparisons,2);
});
test('unconfirmed zero stops the job and explicit resume skips its unresolved candidate',async()=>{
  let n=0;const h=harness({network:url=>url===RNC_RESOURCE?json(envelope(++n===1?{...row(0,0),emptyQueryStatsInterpretedAsZero:true}:row(5,5))):null});await h.connect();const j=(await h.create()).data;
  const first=await h.action(j.id,'step');assert.equal(first.data.status,'paused_error');assert.equal(first.data.requests_completed,0);assert.equal(first.data.error.code,'UNCONFIRMED_ZERO');
  await h.action(j.id,'step');assert.equal(n,1);const resumed=await h.action(j.id,'resume');assert.equal(resumed.data.unresolved_candidates,1);assert.equal(resumed.data.processed_candidates,1);
  const last=await h.action(j.id,'step');assert.equal(n,2);assert.equal(last.data.status,'exhausted');const calls=h.calls.filter(c=>c.url===RNC_RESOURCE);assert.ok(calls[1].init.body.includes('другой'));assert.ok(!calls[1].init.body.includes('слово'));
});
test('HTTP 429 saves the response and honours Retry-After before explicit resume',async()=>{
  const h=harness({network:url=>url===RNC_RESOURCE?json({error:'slow down'},429,{'Retry-After':'60'}):null});await h.connect();const j=(await h.create()).data;
  const stopped=await h.action(j.id,'step');assert.equal(stopped.data.status,'paused_error');assert.equal(stopped.data.error.code,'HTTP_429');assert.equal((await h.action(j.id,'resume')).res.status,429);
  assert.ok([...h.bucket.data.values()].some(x=>x.text.includes('slow down')));h.advance(61000);assert.equal((await h.action(j.id,'resume')).res.status,200);assert.equal(h.calls.filter(c=>c.url===RNC_RESOURCE).length,1);
});
test('R2 conditional user lease prevents two isolates and two jobs from overlapping calls',async()=>{
  let release,entered;const busy=new Promise(r=>entered=r),blocked=new Promise(r=>release=r);let n=0;
  const h=harness({network:async(url)=>{if(url===RNC_RESOURCE){n++;entered();await blocked;return json(envelope(row(5,5)));}return null;}});await h.connect();const j1=(await h.create(1,'Финляндия','first-job')).data,j2=(await h.create(1,'Швеция','second-job')).data;
  const one=h.action(j1.id,'step');await busy;
  const secondApp=createRuntime({html:'',candidates:[{lemma:'слово',pos:'S'},{lemma:'другой',pos:'A'}],fetchImpl:async()=>{throw Error('Overlap must not reach provider');},now:h.now});
  const cfg=await h.config();const res=await secondApp.fetch(new Request('https://trainer.example/api/jobs/'+j2.id+'/step',{method:'POST',headers:{Origin:'https://trainer.example','Content-Type':'application/json','X-CSRF-Token':cfg.csrf_token,'oai-authenticated-user-id':'owner'},body:'{}'}),h.env);
  assert.equal(res.status,409);assert.equal(n,1);release();await one;
});
test('explicit nested MCP Retry-After stops collection until its deadline',async()=>{
  const h=harness({network:url=>url===RNC_RESOURCE?json(envelope({ok:false,error:{code:'RATE_LIMITED',details:{retryAfterSeconds:35}}})):null});await h.connect();const j=(await h.create()).data;
  const stopped=await h.action(j.id,'step');assert.equal(stopped.data.status,'paused_error');assert.equal(stopped.data.error.retry_after,35);assert.equal((await h.action(j.id,'resume')).res.status,429);h.advance(36000);assert.equal((await h.action(j.id,'resume')).res.status,200);assert.equal(h.calls.filter(c=>c.url===RNC_RESOURCE).length,1);
});
test('a malformed HTTP200 body is preserved privately and never becomes a zero',async()=>{
  const h=harness({network:url=>url===RNC_RESOURCE?new Response('BROKEN-MCP-JSON',{status:200,headers:{'Content-Type':'application/json'}}):null});await h.connect();const j=(await h.create()).data;
  const stopped=await h.action(j.id,'step');assert.equal(stopped.data.status,'paused_error');assert.equal(stopped.data.error.code,'INVALID_RESPONSE');assert.equal(stopped.data.requests_completed,0);assert.ok([...h.bucket.data.values()].some(x=>x.text.includes('BROKEN-MCP-JSON')));assert.ok(!JSON.stringify(stopped.data).includes('BROKEN-MCP-JSON'));
});
test('cancel during a count saves that response then stops before another request',async()=>{
  let release,entered;const busy=new Promise(r=>entered=r),blocked=new Promise(r=>release=r);let n=0;
  const h=harness({network:async(url)=>{if(url===RNC_RESOURCE){n++;entered();await blocked;return json(envelope(row(30,10)));}return null;}});await h.connect();const j=(await h.create()).data;const one=h.action(j.id,'step');await busy;const stopping=await h.action(j.id,'cancel');assert.equal(stopping.data.status,'cancelling');release();const stopped=await one;assert.equal(stopped.data.status,'cancelled');assert.equal(stopped.data.requests_completed,1);await h.action(j.id,'step');assert.equal(n,1);
});
test('full persisted response is recovered after state-write failure without a provider replay',async()=>{
  let n=0;const h=harness({network:url=>url===RNC_RESOURCE?(n++,json(envelope(row(5,5)))):null});await h.connect();const j=(await h.create()).data;
  const original=h.bucket.put.bind(h.bucket);let failed=false;
  h.bucket.put=async(key,text,options)=>{if(!failed&&key.endsWith('/jobs/'+j.id)&&JSON.parse(text).requests_completed===1){failed=true;throw Error('Simulated unavailable state save');}return original(key,text,options);};
  await h.action(j.id,'step');assert.equal(n,1);const resumed=await h.action(j.id,'resume');assert.equal(n,1);assert.equal(resumed.data.requests_completed,1);
});
test('valid saved response from interrupted in-flight state is recovered, never re-issued',async()=>{
  const h=harness();await h.connect();const j=(await h.create()).data;
  const [stateKey,state]=[...h.bucket.data.entries()].find(([k])=>k.endsWith('/jobs/'+j.id));const value=JSON.parse(state.text);value.status='running';value.inflight={number:1,query_id:j.id+'_1',phase:'target',candidate_index:0};value.requests_attempted=1;await h.bucket.put(stateKey,JSON.stringify(value));
  const prefix=stateKey.split('jobs/')[0];await h.bucket.put(prefix+'raw/'+j.id+'/1.response',JSON.stringify({response:envelope(row(5,5)),timing:{duration_seconds:1}}));
  const recovered=await h.action(j.id,'step');assert.equal(recovered.data.requests_completed,1);assert.equal(h.calls.filter(c=>c.url===RNC_RESOURCE).length,0);
});
test('refresh tokens are renewed only server-side and never exposed in public state',async()=>{
  const h=harness();await h.connect();h.advance(3600000);const j=(await h.create()).data;await h.action(j.id,'step');const refresh=h.calls.filter(c=>c.url.endsWith('/oauth/token'));assert.equal(refresh.length,2);assert.equal(new URLSearchParams(refresh[1].init.body).get('grant_type'),'refresh_token');assert.ok(!(await h.req('/api/jobs/'+j.id)).data.access_token);
});
test('dialogue is a ChatGPT handoff and never calls a model provider, even with stale model configuration',async()=>{
  const h=harness();Object.assign(h.env,{OPENAI_API_KEY:'stale-unused-key',OPENAI_MODEL:'stale-unused-model'});
  const cfg=await h.config();assert.equal(cfg.chat_available,false);assert.equal(cfg.dialogue_mode,'chatgpt_handoff');assert.equal(cfg.api_key_required,false);
  const answer=await h.req('/api/chat',{method:'POST',token:cfg.csrf_token,body:{card:{lemma:'слово'},messages:[{role:'user',content:'Объясни слово.'}]}});
  assert.equal(answer.res.status,410);assert.equal(answer.data.error.code,'CHATGPT_HANDOFF_ONLY');assert.equal(h.calls.length,0);assert.ok(!JSON.stringify(answer.data).includes('stale-unused-key'));
  delete h.env.OPENAI_API_KEY;delete h.env.OPENAI_MODEL;
  assert.equal((await h.req('/api/chat',{method:'POST',token:cfg.csrf_token,body:{}})).res.status,410);assert.equal(h.calls.length,0);
});
test('count validation rejects invalid denominators/rates and ratio arithmetic is exact BigInt',()=>{
  assert.throws(()=>checkedCount(envelope({...row(),denominatorSource:'corpus'})));assert.throws(()=>checkedCount(envelope({...row(),ipm:0})));assert.throws(()=>checkedCount(envelope({...row(),hits:1.2})));
  const a={hits:900719925,texts:20,denominatorWords:9007199254740991},b={hits:450359962,texts:20,denominatorWords:9007199254740990};assert.equal(qualifies(a,b),true);
});
