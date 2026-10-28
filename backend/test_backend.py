import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer
from server import Store, APIError, make_handler

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.now=1000.0
        self.path=Path(self.tmp.name)/'test.sqlite3'
        self.store=Store(self.path,clock=lambda:self.now)
        self.body=dict(stop_id='A',device_id='rain-A-01',session_id='boot-1',sequence=1,
                       status='wet',raw=1800,calibrated=True,observation_age_ms=0)
    def tearDown(self):
        self.tmp.cleanup()
    def test_no_data_unknown(self):
        self.assertEqual(self.store.weather()['reason'],'no_reading')
    def test_wet_and_dry(self):
        self.store.accept(self.body)
        self.assertEqual(self.store.weather()['status'],'wet')
        self.store.accept(dict(self.body,sequence=2,status='dry',raw=12))
        self.assertEqual(self.store.weather()['status'],'dry')
    def test_stale_expiry_and_recovery(self):
        self.store.accept(self.body)
        self.now+=10
        self.assertEqual(self.store.weather()['reason'],'stale')
        self.assertEqual(self.store.weather()['valid_for_ms'],0)
        self.store.accept(dict(self.body,sequence=2))
        self.assertEqual(self.store.weather()['status'],'wet')
    def test_original_age_respected(self):
        self.store.accept(dict(self.body,observation_age_ms=9000))
        self.assertLessEqual(self.store.weather()['valid_for_ms'],1000)
        self.now+=1
        self.assertEqual(self.store.weather()['status'],'unknown')
    def test_duplicate_does_not_refresh(self):
        self.store.accept(self.body)
        self.now+=9
        with self.assertRaises(APIError) as result:
            self.store.accept(self.body)
        self.assertEqual(result.exception.status,409)
        self.now+=1
        self.assertEqual(self.store.weather()['reason'],'stale')
    def test_out_of_order(self):
        self.store.accept(dict(self.body,sequence=8))
        with self.assertRaises(APIError):
            self.store.accept(dict(self.body,sequence=7))
    def test_restart_retires_session(self):
        self.store.accept(self.body)
        self.store.accept(dict(self.body,session_id='boot-2',status='unknown',calibrated=False))
        self.assertEqual(self.store.weather()['reason'],'not_calibrated')
        with self.assertRaises(APIError):
            self.store.accept(dict(self.body,sequence=2))
    def test_persistent_restart_does_not_refresh(self):
        self.store.accept(self.body)
        self.now+=20
        restarted=Store(self.path,clock=lambda:self.now)
        self.assertEqual(restarted.weather()['reason'],'stale')
    def test_invalid_payloads(self):
        changes=[{'raw':5000},{'sequence':True},{'observation_age_ms':10000},
                 {'status':'raining-heavy'},{'calibrated':'true'},
                 {'calibrated':False},{'device_id':'another-device'},
                 {'session_id':'../test'}]
        for update in changes:
            with self.subTest(update=update), self.assertRaises(APIError):
                self.store.accept(dict(self.body,**update))
    def test_unknown_is_not_dry(self):
        self.store.accept(dict(self.body,status='unknown',raw=None))
        self.assertEqual(self.store.weather()['status'],'unknown')
    def test_clock_backwards(self):
        self.store.accept(self.body)
        self.now-=5
        self.assertEqual(self.store.weather()['reason'],'clock_changed')
    def test_http_end_to_end(self):
        token='test-token-only-not-a-real-credential'
        server=ThreadingHTTPServer(('127.0.0.1',0),make_handler(self.store,token))
        worker=threading.Thread(target=server.serve_forever,daemon=True)
        worker.start()
        base='http://127.0.0.1:'+str(server.server_port)
        try:
            with urlopen(base+'/health',timeout=3) as response:
                self.assertEqual(json.load(response)['status'],'ok')
            headers={'Content-Type':'application/json'}
            request=Request(base+'/api/sensor-readings',data=json.dumps(self.body).encode(),headers=headers)
            with self.assertRaises(HTTPError) as result:
                urlopen(request,timeout=3)
            self.assertEqual(result.exception.code,401)
            headers['Authorization']='Bearer '+token
            request=Request(base+'/api/sensor-readings',data=json.dumps(self.body).encode(),headers=headers)
            with urlopen(request,timeout=3) as response:
                self.assertEqual(response.status,201)
            with urlopen(base+'/api/stops/A/weather',timeout=3) as response:
                self.assertEqual(response.headers['Cache-Control'],'no-store')
                self.assertEqual(json.load(response)['status'],'wet')
            bad=Request(base+'/api/sensor-readings',data=b'{',headers=headers)
            with self.assertRaises(HTTPError) as result:
                urlopen(bad,timeout=3)
            self.assertEqual(result.exception.code,400)
            with urlopen(base+'/api/stops',timeout=3) as response:
                stop=json.load(response)['stops'][0]
                self.assertEqual(stop['occupancy']['status'],'unknown')
                self.assertEqual(stop['weather']['status'],'wet')
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

if __name__=='__main__':
    unittest.main(verbosity=2)
