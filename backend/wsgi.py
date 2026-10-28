"""Public demo entry point. Run behind Render HTTPS using Gunicorn."""
import hmac
import json
import mimetypes
import os
from pathlib import Path
from server import Store, OccupancyStore, APIError

ROOT = Path(__file__).resolve().parent
DATA = Path(os.environ.get('TEDUHLINK_DATA_DIR', str(ROOT/'data')))
DATA.mkdir(parents=True,exist_ok=True)
TOKEN = os.environ.get('TEDUHLINK_DEVICE_TOKEN','').strip()
if len(TOKEN) < 24:
    raise RuntimeError('Set TEDUHLINK_DEVICE_TOKEN to a private random token of at least 24 characters.')
weather = Store(DATA/'teduhlink.sqlite3')
counts = OccupancyStore(DATA/'occupancy.sqlite3')
FRONTEND = (ROOT.parent/'frontend').resolve()

def application(environ, start_response):
    status = 200
    content_type = 'application/json; charset=utf-8'
    method = environ.get('REQUEST_METHOD','GET')
    path = environ.get('PATH_INFO','/')
    try:
        if method == 'GET' and path == '/health':
            data = {'status':'ok','service':'TeduhLink demo'}
        elif method == 'GET' and path == '/api/stops/A/weather':
            data = weather.weather()
        elif method == 'GET' and path == '/api/stops/A/occupancy':
            data = counts.occupancy()
        elif method == 'GET' and path == '/api/stops':
            data = {'stops':[{'stop_id':'A','name':'Stop A - demonstration area',
                'data_source':'indoor_demo','access':'unknown',
                'weather':weather.weather(),'occupancy':counts.occupancy()}]}
        elif method == 'POST' and path in ('/api/sensor-readings','/api/occupancy-readings'):
            expected=('Bearer '+TOKEN).encode()
            supplied=environ.get('HTTP_AUTHORIZATION','').encode()
            if not hmac.compare_digest(expected,supplied):
                raise APIError(401,'Valid device token required.')
            try:
                size=int(environ.get('CONTENT_LENGTH','0') or '0')
            except ValueError:
                raise APIError(400,'Invalid content length.')
            if not 0 < size <= 4096:
                raise APIError(413,'Body must be 1-4096 bytes.')
            if environ.get('CONTENT_TYPE','').split(';')[0]!='application/json':
                raise APIError(415,'Use application/json.')
            try:
                body=json.loads(environ['wsgi.input'].read(size))
            except (ValueError,UnicodeDecodeError):
                raise APIError(400,'Invalid JSON.')
            data=weather.accept(body) if path=='/api/sensor-readings' else counts.accept_count(body)
            status=201
        elif method=='GET' and not path.startswith('/api/'):
            target=(FRONTEND/('index.html' if path=='/' else path.lstrip('/'))).resolve()
            if not target.is_relative_to(FRONTEND) or not target.is_file() or any(p.startswith('.') for p in target.relative_to(FRONTEND).parts):
                raise APIError(404,'Page not found. Export frontend/index.html first.')
            payload=target.read_bytes()
            content_type=mimetypes.guess_type(str(target))[0] or 'application/octet-stream'
            start_response('200 OK',[('Content-Type',content_type),('Content-Length',str(len(payload))),('X-Content-Type-Options','nosniff')])
            return [payload]
        else:
            raise APIError(404,'Endpoint not found.')
    except APIError as error:
        status=error.status
        data={'error':error.message}
    payload=json.dumps(data,allow_nan=False).encode()
    labels={200:'OK',201:'Created',400:'Bad Request',401:'Unauthorized',404:'Not Found',409:'Conflict',413:'Content Too Large',415:'Unsupported Media Type',422:'Unprocessable Content'}
    start_response(str(status)+' '+labels.get(status,'Error'),[('Content-Type',content_type),('Cache-Control','no-store'),('Content-Length',str(len(payload))),('X-Content-Type-Options','nosniff')])
    return [payload]
