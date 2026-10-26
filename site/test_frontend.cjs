// DOM-level functional checks; no corpus or model calls.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const candidate=__dirname+'/standalone/index.html';
const html=fs.readFileSync(fs.existsSync(candidate)?candidate:__dirname+'/dist/index.html','utf8');
const payload=html.match(/<script id="dataset" type="application\/json">([\s\S]*?)<\/script>/)[1];
const code=html.match(/<script>([\s\S]*?)<\/script>/)[1];
class Node {constructor(){this.children=[];this.value='';this.dataset={};this.classList={toggle(){},add(){}};this.textContent='';this.hidden=false;this.isConnected=true;this.byId={};}append(...n){this.children.push(...n)}replaceChildren(...n){this.children=n;}setAttribute(k,v){this[k]=v;}removeAttribute(k){delete this[k]}addEventListener(){}querySelector(id){return this.byId[id]||(this.byId[id]=new Node())} }
const nodes={};const document={getElementById(id){if(!nodes[id])nodes[id]=new Node();return nodes[id]},createElement(){return new Node()},querySelectorAll(){return []},documentElement:{}};
document.getElementById('dataset').textContent=payload;
const mem={};const window={};
const context={document,window,localStorage:{getItem:k=>mem[k]||null,setItem:(k,v)=>mem[k]=v},fetch:async()=>{throw Error('no network in test')},navigator:{},console,setTimeout,clearTimeout,crypto:global.crypto,location:{pathname:'/index.html'}};
vm.runInNewContext(code,context);const app=window.REGIONAL_TRAINER;
assert.equal(app.words.length,94);assert.equal(new Set(app.words.map(w=>w.lemma)).size,94);assert.equal(app.originalCards.length,40);
for (const language of ['ru','en']) {app.setLang(language);for(let i=0;i<app.words.length;i++){app.selectWord(i);app.mode('recognition');assert.equal(nodes.activity.children[1].children.length,4);const w=app.words[i],correct=w.definition[language];const choices=nodes.activity.children[1].children;assert.equal(choices.filter(b=>b.textContent===correct).length,1);choices.find(b=>b.textContent===correct).onclick();assert.equal(nodes.answerbox.hidden,false);assert(nodes.answerbox.innerHTML.includes(w.example.ru));app.mode('recall');const row=nodes.activity.children[2];row.children[0].value=w.lemma;row.children[1].onclick();assert.equal(nodes.answerbox.hidden,false);app.mode('evidence');assert.equal(nodes.activity.children[1].children.length,4);assert(app.groundedPrompt().includes(w.lemma));}}
assert.equal(nodes.wordlist.children.length,94);
console.log('PASS: 94 words × RU/EN × recognition/recall/evidence; prompt grounding and 40 preserved legacy cards.');
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function checkProgress({existing=false,close=false,error=false,legacy=false}={}){
 const calls=[],panel=new Node(),pop={closed:false,document:{createElement:()=>new Node()},addEventListener(){},fetch:async(path,options)=>{
  calls.push({path,method:options.method,body:options.body});
  let data,status=200;
  if(path==='/api/config')data={csrf_token:'fixture-token',collector_available:true,execution_mode:legacy?'background':'foreground_steps'};
  else if(path==='/api/jobs')data={id:'job-fixture',status:'ready',requests_completed:0,processed_candidates:0,qualified_words:0,pool_size:20};
  else if(path.endsWith('/step')){
   const n=calls.filter(c=>c.path.endsWith('/step')).length;
   if(error){status=504;data={error:{code:'UPSTREAM_TIMEOUT',message:'upstream fixture timeout'}};}
   else {data={id:'job-fixture',status:n===2?'complete':'ready',requests_completed:n,processed_candidates:n,qualified_words:n,pool_size:20};if(close)pop.closed=true;}
  }else data={id:'job-fixture',status:legacy?'complete':'ready',requests_completed:0,processed_candidates:0,qualified_words:0,pool_size:20};
  return {ok:status===200,json:async()=>data};
 }};
 app.progressApp(pop,'Финляндия','en',existing?'job-fixture':null,panel);
 await flush();await flush();
 assert.equal(calls.filter(c=>c.method==='POST').length,0,'Opening progress/config must not start a collection');
 if(existing){assert(calls.some(c=>c.path==='/api/jobs/job-fixture'));assert.equal(calls.filter(c=>c.path.endsWith('/step')).length,0,'Reopening saved foreground job is read only');return;}
 await panel.querySelector('#start').onclick();
 assert.equal(calls.filter(c=>c.path==='/api/jobs'&&c.method==='POST').length,1);
 const steps=calls.filter(c=>c.path.endsWith('/step'));
 assert.equal(steps.length,error||close?1:2);
 assert(steps.every(c=>c.method==='POST'),'Each advancing step must be an explicit POST');
 if(error){await flush();assert.equal(calls.filter(c=>c.path.endsWith('/step')).length,1,'API failure must not be automatically retried');assert.equal(panel.querySelector('#resume').hidden,false);}
}
(async()=>{await checkProgress();await checkProgress({existing:true});await checkProgress({close:true});await checkProgress({error:true});await checkProgress({existing:true,legacy:true});console.log('PASS: foreground POST steps, no advancement before Start/on reopen, close pauses, API failures stop without replay, legacy reads retained.');})().catch(e=>{console.error(e);process.exitCode=1});
