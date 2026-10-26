import csv, importlib.util, json, os, tempfile, threading, time, unittest
from pathlib import Path
from unittest.mock import patch
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
spec=importlib.util.spec_from_file_location('collector',Path(__file__).with_name('server.py'));s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
def count(hits=40,texts=20,words=1000000,**extra):
    return {'structuredContent':{'results':[{'id':'test','ok':True,'hits':hits,'texts':texts,'denominatorWords':words,'denominatorSource':'subcorpus','ipm':hits*1e6/words,'emptyQueryStatsInterpretedAsZero':False,**extra}]}}
class Client:
    configured=True
    def __init__(self,items):self.items=iter(items);self.calls=[]
    def call(self,q):
        self.calls.append(q);value=next(self.items)
        if isinstance(value,Exception):raise value
        return value
class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.pool=self.root/'pool.csv';self.pool.write_text('lemma,pos\nслово,S\nдругой,A\n')
    def tearDown(self):self.tmp.cleanup()
    def manager(self,items):return s.JobManager(self.root/'state',self.pool,Client(items))
    def finish(self,m):m.worker.join(3);self.assertFalse(m.worker.is_alive());return next(iter(m.jobs.values()))
    def test_serial_singleton_and_target_stop(self):
        m=self.manager([count(),count(hits=10,texts=10)]);m.create('Финляндия',1);j=self.finish(m)
        self.assertEqual(j['status'],'complete');self.assertEqual(j['qualified_words'],1);self.assertEqual(len(m.client.calls),2)
        for q in m.client.calls:self.assertEqual(len(q['queries']),1)
        self.assertEqual(m.client.calls[0]['queries'][0]['query']['subcorpus']['sectionValues'][1]['conditionValues'][0]['text']['v'],'Финляндия')
        self.assertTrue((m.path(j)/'final.csv').exists())
    def test_low_target_skips_reference(self):
        m=self.manager([count(5,3),count(8,4)]);m.create('Канада',2);j=self.finish(m)
        self.assertEqual(j['status'],'exhausted');self.assertEqual(len(m.client.calls),2);self.assertEqual(j['completed_comparisons'],0)
    def test_same_lemma_different_pos_does_not_inflate_words(self):
        self.pool.write_text('lemma,pos\nслово,S\nслово,A\n')
        m=self.manager([count(),count(10,10),count(),count(10,10)]);m.create('Канада',2);j=self.finish(m)
        self.assertEqual(j['qualified_words'],1);self.assertEqual(j['status'],'exhausted')
    def test_error_stops_and_resume_skips_failed_query(self):
        m=self.manager([count(),s.ServiceError('HTTP_429','Rate limit','0')]);m.create('Канада',2);j=self.finish(m)
        self.assertEqual(j['status'],'paused_error');self.assertEqual(len(m.client.calls),2)
        # Target success is reused; failed reference is not resent; next candidate follows.
        m.client=Client([count(5,3)]);m.resume(j['id']);self.finish(m)
        self.assertEqual(len(m.client.calls),1);self.assertEqual(j['requests_attempted'],3);self.assertEqual(j['status'],'exhausted')
    def test_unconfirmed_zero_never_imported(self):
        m=self.manager([count(0,0,emptyQueryStatsInterpretedAsZero=True)]);m.create('Канада',1);j=self.finish(m)
        self.assertEqual(j['status'],'paused_error');self.assertEqual(j['counts'],{});self.assertEqual(j['error']['code'],'UNCONFIRMED_ZERO')
    def test_invalid_denominator_and_ipm(self):
        for raw in [count(1,1,denominatorSource='corpus'),count(1,1,ipm=8),count(1,2)]:
            with self.assertRaises(s.ServiceError):s.checked_count(raw)
    def test_restart_does_not_replay_in_flight(self):
        m=self.manager([s.ServiceError('TIMEOUT','timeout')]);m.create('Канада',1);j=self.finish(m)
        j['status']='running';m.save(j);again=s.JobManager(m.root,self.pool,Client([count(),count(10,10)]))
        restored=again.get(j['id']);self.assertEqual(restored['status'],'interrupted');again.resume(j['id']);self.finish(again)
        self.assertEqual(restored['requests_attempted'],3);self.assertEqual(restored['qualified_words'],1)
    def test_pool_mutation_blocks_resume(self):
        m=self.manager([s.ServiceError('TIMEOUT','timeout')]);m.create('Канада',1);j=self.finish(m);self.pool.write_text('lemma,pos\nновый,A\n')
        with self.assertRaises(ValueError):m.resume(j['id'])
    def test_country_validation(self):
        for c in ('Россия','x','../x','Канада\nРоссия','Канада/Россия'):
            with self.assertRaises(ValueError):s.country_name(c)
    def test_fraction_boundary_not_rounding(self):
        self.assertTrue(s.qualifies({'hits':20,'texts':10,'denominatorWords':3},{'hits':10,'denominatorWords':3}))
        self.assertFalse(s.qualifies({'hits':20,'texts':10,'denominatorWords':4},{'hits':10,'denominatorWords':3}))
    def test_eta_does_not_claim_target_time(self):
        m=self.manager([count(5,3),count(8,4)]);m.create('Канада',2);j=self.finish(m);p=m.public(j)
        self.assertIsNone(p['eta']['target_completion_seconds']);self.assertEqual(p['eta']['basis'],'full_remaining_queue_not_target_words')
    def test_chat_transmits_history_without_key_in_output(self):
        response={'id':'r1','status':'completed','model':'chosen','output':[{'type':'message','content':[{'type':'output_text','text':'Как вы употребите это слово?'}]}]}
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-secret','OPENAI_MODEL':'chosen'}),patch.object(s,'json_http',return_value=(response,{})) as http:
            result=s.tutor({'messages':[{'role':'user','content':'Привет'}],'card':{'lemma':'акимақ','semantic_status':'not_semantically_verified'}})
        args=http.call_args.args;self.assertEqual(args[0],'https://api.openai.com/v1/responses');self.assertFalse(args[1]['store']);self.assertEqual(args[1]['input'][0]['content'],'Привет');self.assertNotIn('test-secret',json.dumps(result))
    def test_chat_unconfigured_is_explicit(self):
        with patch.dict(os.environ,{},clear=True):
            with self.assertRaises(s.ServiceError) as caught:s.tutor({'messages':[]})
        self.assertEqual(caught.exception.code,'CHAT_NOT_CONFIGURED')
    def test_publish_only_final_frequency_data(self):
        import base64
        m=self.manager([count(),count(10,10)]);m.create('Канада',1);j=self.finish(m)
        calls=[]
        def transport(url,body,headers,**kw):
            calls.append((url,body,kw))
            if kw['method']=='GET':raise s.ServiceError('HTTP_404','Not found')
            return {'content':{'html_url':'https://github.com/owner/repo/blob/main/data/result.json'}},{}
        with patch.dict(os.environ,{'GITHUB_TOKEN':'secret','GITHUB_REPOSITORY':'owner/repo'}),patch.object(s,'json_http',side_effect=transport):
            result=s.publish_job(m,j['id']);again=s.publish_job(m,j['id'])
        published=json.loads(base64.b64decode(calls[1][1]['content']))
        self.assertEqual(len(calls),2);self.assertTrue(again['already_published']);self.assertEqual(published['selected_words'],1)
        self.assertEqual(published['semantic_status'],'not_semantically_verified');self.assertNotIn('private_raw',json.dumps(published));self.assertNotIn('secret',json.dumps(published))
    def test_uncertain_publish_is_not_replayed(self):
        m=self.manager([count(),count(10,10)]);m.create('Канада',1);j=self.finish(m)
        def transport(url,body,headers,**kw):
            if kw['method']=='GET':raise s.ServiceError('HTTP_404','Not found')
            raise s.ServiceError('TIMEOUT','Unknown write outcome')
        with patch.dict(os.environ,{'GITHUB_TOKEN':'secret','GITHUB_REPOSITORY':'owner/repo'}),patch.object(s,'json_http',side_effect=transport) as http:
            with self.assertRaises(s.ServiceError):s.publish_job(m,j['id'])
            with self.assertRaises(s.ServiceError) as caught:s.publish_job(m,j['id'])
            self.assertEqual(http.call_count,2);self.assertEqual(caught.exception.code,'PUBLISH_UNCERTAIN')
    def test_http_requires_cookie_origin_and_csrf(self):
        m=self.manager([]);server=ThreadingHTTPServer(('127.0.0.1',0),s.make_handler(m,self.root));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/api/session') as r:token=json.load(r)['csrf_token'];cookie=r.headers['Set-Cookie'].split(';')[0]
            for headers in ({},{'Cookie':cookie},{'Cookie':cookie,'Origin':base,'X-CSRF-Token':'wrong'}):
                req=Request(base+'/api/chat',b'{}',{'Content-Type':'application/json',**headers})
                with self.assertRaises(HTTPError) as caught:urlopen(req)
                self.assertEqual(caught.exception.code,403)
        finally:server.shutdown();server.server_close();thread.join()
    def test_private_files_never_served(self):
        m=self.manager([]);(self.root/'backend').mkdir();(self.root/'backend'/'secret.py').write_text('secret')
        server=ThreadingHTTPServer(('127.0.0.1',0),s.make_handler(m,self.root));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with self.assertRaises(HTTPError) as caught:urlopen('http://127.0.0.1:'+str(server.server_port)+'/backend/secret.py')
            self.assertEqual(caught.exception.code,404)
        finally:server.shutdown();server.server_close();thread.join()
if __name__=='__main__':unittest.main(verbosity=2)
