"""Start the local app on a fresh checkout; keep private state on this PC."""
import os
from pathlib import Path
import secrets
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parent


def prepare_token():
    path = ROOT / 'data' / 'device-token.txt'
    path.parent.mkdir(parents=True, exist_ok=True)
    token = os.environ.get('TEDUHLINK_DEVICE_TOKEN', '').strip()
    if not token:
        if not path.exists():
            path.write_text(secrets.token_urlsafe(32), encoding='utf-8')
        token = path.read_text(encoding='utf-8').strip()
    if len(token) < 24:
        raise SystemExit('Device token must contain at least 24 characters.')
    os.environ['TEDUHLINK_DEVICE_TOKEN'] = token


if __name__ == '__main__':
    prepare_token()
    from wsgi import application
    print('Keep this window open. Start 3_START_CONNECTED_CAMERA.cmd next.', flush=True)
    print('App: http://127.0.0.1:8000/stop_a_details_teduhlink/code.html', flush=True)
    print('Health: http://127.0.0.1:8000/health', flush=True)
    print('Local demonstration only. Ctrl+C to stop.', flush=True)
    try:
        with make_server('127.0.0.1', 8000, application) as server:
            server.serve_forever()
    except KeyboardInterrupt:
        pass
