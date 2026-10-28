"""TeduhLink local sensor API. Standard Python only; not an internet-facing server."""
from contextlib import contextmanager
import argparse
import hmac
import json
import os
from pathlib import Path
import secrets
import sqlite3
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent
TTL_MS = 10000

class APIError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message

class Store:
    def __init__(self, path, clock=time.time):
        self.path, self.clock = str(path), clock
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY, received_at REAL NOT NULL,
                    observed_at REAL NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY, last_sequence INTEGER NOT NULL,
                    active INTEGER NOT NULL);
            ''')
    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        try:
            with db:
                yield db
        finally:
            db.close()
    def accept(self, body):
        required = {'stop_id','device_id','session_id','sequence','status',
                    'raw','calibrated','observation_age_ms'}
        if not isinstance(body, dict) or set(body) != required:
            raise APIError(422, 'Required fields: ' + ', '.join(sorted(required)))
        if body['stop_id'] != 'A' or body['device_id'] != 'rain-A-01':
            raise APIError(422, 'Only Stop A / rain-A-01 is configured.')
        sid = body['session_id']
        if not isinstance(sid,str) or not 1 <= len(sid) <= 64 or not all(
                c.isascii() and (c.isalnum() or c in '-_') for c in sid):
            raise APIError(422, 'Invalid session_id; use letters, digits, hyphens or underscores.')
        seq = body['sequence']
        if type(seq) is not int or not 0 <= seq <= 9007199254740991:
            raise APIError(422, 'sequence must be a nonnegative integer.')
        age = body['observation_age_ms']
        if type(age) is not int or not 0 <= age < TTL_MS:
            raise APIError(422, 'Reading must be less than 10000 ms old.')
        raw = body['raw']
        if raw is not None and (type(raw) is not int or not 0 <= raw <= 4095):
            raise APIError(422, 'raw must be null or an integer from 0 to 4095.')
        if type(body['calibrated']) is not bool:
            raise APIError(422, 'calibrated must be boolean.')
        if body['status'] not in ('wet','dry','unknown'):
            raise APIError(422, 'status must be wet, dry or unknown.')
        if body['status'] != 'unknown' and (not body['calibrated'] or raw is None):
            raise APIError(422, 'Wet/dry requires calibration and a raw reading.')
        now = self.clock()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            old = db.execute('SELECT last_sequence,active FROM sessions WHERE session_id=?',(sid,)).fetchone()
            if old and not old[1]:
                raise APIError(409, 'Retired session; use current device session.')
            if old and seq <= old[0]:
                raise APIError(409, 'Duplicate or older sequence; timestamp not refreshed.')
            if not old:
                db.execute('UPDATE sessions SET active=0')
                db.execute('INSERT INTO sessions VALUES (?,?,1)',(sid,seq))
            else:
                db.execute('UPDATE sessions SET last_sequence=? WHERE session_id=?',(seq,sid))
            db.execute('INSERT INTO readings(received_at,observed_at,payload) VALUES (?,?,?)',
                       (now,now-age/1000,json.dumps(body)))
            db.execute('DELETE FROM readings WHERE id <= (SELECT COALESCE(MAX(id),0)-10000 FROM readings)')
        return {'accepted':True,'session_id':sid,'sequence':seq,'received_at_unix_ms':int(now*1000)}
    def weather(self):
        result = dict(stop_id='A',device_id='rain-A-01',source='rain_plate',status='unknown',
                      reason='no_reading',raw=None,calibrated=False,session_id=None,sequence=None,
                      observation_age_ms=None,valid_for_ms=0)
        with self.connect() as db:
            row = db.execute('SELECT observed_at,payload FROM readings ORDER BY id DESC LIMIT 1').fetchone()
        if row is None:
            return result
        observed, saved = row
        payload = json.loads(saved)
        age = int((self.clock()-observed)*1000)
        result.update({k:payload[k] for k in ('calibrated','session_id','sequence')})
        if age < 0:
            result['reason']='clock_changed'
            return result
        result['observation_age_ms']=age
        if age >= TTL_MS:
            result['reason']='stale'
        elif not payload['calibrated']:
            result['reason']='not_calibrated'
        elif payload['status']=='unknown':
            result['reason']='sensor_unknown'
        else:
            result.update(status=payload['status'],reason='fresh',raw=payload['raw'],valid_for_ms=TTL_MS-age)
        return result

class OccupancyStore(Store):
    def accept_count(self, body):
        fields = {'stop_id','session_id','sequence','estimated_count','observation_age_ms'}
        if not isinstance(body, dict) or set(body) != fields or body['stop_id'] != 'A':
            raise APIError(422, 'Invalid occupancy fields or stop ID.')
        count = body['estimated_count']
        if count is not None and (type(count) is not int or not 0 <= count <= 4095):
            raise APIError(422, 'estimated_count must be null or a nonnegative integer <=4095.')
        # Reuse the tested freshness/session machinery in a separate database.
        return self.accept(dict(stop_id='A', device_id='rain-A-01',
            session_id=body['session_id'], sequence=body['sequence'], raw=count,
            calibrated=count is not None,
            status='unknown' if count is None else 'wet' if count >= 3 else 'dry',
            observation_age_ms=body['observation_age_ms']))
    def occupancy(self):
        value = self.weather()
        status = {'wet':'at_limit','dry':'below_limit','unknown':'unknown'}[value['status']]
        return dict(stop_id='A',source='camera_ml',capacity=3,status=status,
            estimated_count=value['raw'] if status != 'unknown' else None,
            reason='warming_up_or_unavailable' if value['reason']=='not_calibrated' else value['reason'],
            session_id=value['session_id'],sequence=value['sequence'],
            observation_age_ms=value['observation_age_ms'],valid_for_ms=value['valid_for_ms'])

def make_handler(store, token, occupancy_store=None):
    class Handler(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)
        def respond(self,status,data):
            encoded=json.dumps(data,allow_nan=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type','application/json; charset=utf-8')
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Content-Length',str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        def do_GET(self):
            path=self.path.split('?',1)[0]
            if path in ('/','/health'):
                self.respond(200,dict(service='TeduhLink local prototype',status='ok',
                    weather_url='/api/stops/A/weather',stops_url='/api/stops'))
            elif path=='/api/stops/A/weather':
                self.respond(200,store.weather())
            elif path=='/api/stops/A/occupancy' and occupancy_store is not None:
                self.respond(200,occupancy_store.occupancy())
            elif path=='/api/stops':
                self.respond(200,{'stops':[dict(stop_id='A',name='Stop A - demonstration area',
                    deployment='controlled_demo',access='unknown',
                    occupancy=occupancy_store.occupancy() if occupancy_store is not None else dict(status='unknown',estimated_count=None),weather=store.weather())]})
            else:
                self.respond(404,{'error':'Endpoint not found.'})
        def do_POST(self):
            if self.path not in ('/api/sensor-readings','/api/occupancy-readings') or (self.path=='/api/occupancy-readings' and occupancy_store is None):
                self.respond(404,{'error':'Endpoint not found.'})
                return
            if not hmac.compare_digest(self.headers.get('Authorization','').encode(),('Bearer '+token).encode()):
                self.respond(401,{'error':'Valid Bearer token required.'})
                return
            try:
                if self.headers.get('Transfer-Encoding'):
                    raise APIError(400,'Use Content-Length; chunked uploads are not supported.')
                try:
                    size=int(self.headers.get('Content-Length','0'))
                except ValueError:
                    raise APIError(400,'Invalid Content-Length.')
                if not 0<size<=4096:
                    raise APIError(413,'Body must contain 1-4096 bytes.')
                if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
                    raise APIError(415,'Use application/json.')
                raw=self.rfile.read(size)
                if len(raw)!=size:
                    raise APIError(400,'Incomplete request.')
                try:
                    body=json.loads(raw)
                except (ValueError,UnicodeDecodeError):
                    raise APIError(400,'Invalid JSON.')
                self.respond(201,occupancy_store.accept_count(body) if self.path=='/api/occupancy-readings' else store.accept(body))
            except APIError as err:
                self.respond(err.status,{'error':err.message})
            except (TimeoutError,OSError):
                self.close_connection=True
    return Handler

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='127.0.0.1')
    parser.add_argument('--port',type=int,default=8000)
    args=parser.parse_args()
    data=ROOT/'data'
    data.mkdir(exist_ok=True)
    token_path=data/'device-token.txt'
    token=os.environ.get('TEDUHLINK_DEVICE_TOKEN','').strip()
    if not token:
        if not token_path.exists():
            token_path.write_text(secrets.token_urlsafe(32),encoding='utf-8')
        token=token_path.read_text(encoding='utf-8').strip()
    if len(token)<24:
        raise SystemExit('Device token must be at least 24 characters.')
    store=Store(data/'teduhlink.sqlite3')
    server=ThreadingHTTPServer((args.host,args.port),make_handler(store,token,OccupancyStore(data/'occupancy.sqlite3')))
    print('TeduhLink backend is running. Keep this window open.',flush=True)
    print('On this laptop: http://127.0.0.1:%s/health'%args.port,flush=True)
    print('Private device token file: '+str(token_path),flush=True)
    print('Local HTTP prototype only. Do not expose directly to the internet.',flush=True)
    print('Press Ctrl+C to stop.',flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__=='__main__':
    main()
