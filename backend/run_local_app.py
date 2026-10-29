import os
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parent
token_file = ROOT / "data" / "device-token.txt"

if not os.environ.get("TEDUHLINK_DEVICE_TOKEN"):
    if not token_file.exists():
        raise SystemExit(
            "Device token file not found. Start your existing backend "
            "once first, then stop it and run this launcher."
        )
    os.environ["TEDUHLINK_DEVICE_TOKEN"] = (
        token_file.read_text(encoding="utf-8").strip()
    )

from wsgi import application

print("TeduhLink local app is running.")
print("App: http://localhost:8000/stop_a_details_teduhlink/code.html")
print("Health: http://localhost:8000/health")
print("Press Ctrl+C to stop.")

with make_server("0.0.0.0", 8000, application) as server:
    server.serve_forever()