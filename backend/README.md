# TeduhLink sensor backend

This is a working local prototype receiver for Sofea's ESP32 rain plate. It uses Python's built-in HTTP server and SQLite database, with no pip packages. Camera inference, occupancy uploads, rider app screens and official weather feeds are not implemented in this package.

## Start on Sofea's Windows laptop

1. Open this folder in File Explorer.
2. Double-click START_BACKEND.cmd. Keep its window open.
3. Open http://127.0.0.1:8000/health in your browser. Expect status: ok.
4. Open http://127.0.0.1:8000/api/stops/A/weather. Before uploads, expect status: unknown and reason: no_reading.
5. Stop the server with Ctrl+C in its window.

The launcher uses the Python runtime already installed with Codex on Sofea's laptop. On another Windows laptop it falls back to `py -3`, requiring an installed Python 3 interpreter. It binds to all local network interfaces so an ESP32 on the same trusted network can reach it. If Windows asks, permit the server only on the trusted network you use for testing. Do not disable the firewall globally.

If port 8000 is already occupied, stop the other server or change the launcher's --port value and use that port in all URLs.

## Generated files

Starting the server creates:
- data/device-token.txt: private upload credential. Do not commit, screenshot or publish it.
- data/teduhlink.sqlite3: local database of the latest 10,000 accepted readings and device sessions.

The data folder is excluded by .gitignore. If sharing a ZIP or copying the folder, exclude data/ manually. The token can alternatively be supplied in TEDUHLINK_DEVICE_TOKEN before launch.

## Addresses

- GET /health: confirms this backend is running.
- POST /api/sensor-readings: authenticated upload from the ESP32.
- GET /api/stops/A/weather: latest usable wetness reading, or unknown with a reason.
- GET /api/stops: Stop A demonstration metadata plus weather. Occupancy and access remain unknown until their features are implemented and verified.

Read endpoints expose only aggregate prototype information and do not require the device credential. No camera image is exposed.

For the ESP32, replace 127.0.0.1 with the laptop's Wi-Fi IPv4 address. On Windows run ipconfig and find IPv4 Address under the Wi-Fi adapter connected to the same hotspot as the ESP32. An example URL is http://192.168.43.100:8000/api/sensor-readings; replace the address with your actual value. The laptop address is different from the ESP32 address used in the previous exercise. 127.0.0.1 on an ESP32 points to itself, not your laptop.

The ESP32's current sketch only serves local browser requests. It must be updated to POST to this receiver; starting this backend does not automatically connect it.

## Upload contract

Headers:

    Content-Type: application/json
    Authorization: Bearer YOUR_PRIVATE_DEVICE_TOKEN

Example JSON (sample values, not actual measurements):

    {
      "stop_id": "A",
      "device_id": "rain-A-01",
      "session_id": "boot-unique-id",
      "sequence": 1,
      "status": "wet",
      "raw": 1800,
      "calibrated": true,
      "observation_age_ms": 0
    }

- All eight fields are required; extra fields are rejected to catch interface mistakes.
- status: wet, dry or unknown. Wet/dry requires calibrated=true and raw=0..4095.
- A new unique session_id is required per ESP32 boot. Sequence must increase for each measurement in that session, including unknown readings.
- observation_age_ms is elapsed time from sampling to sending, never an invented zero for an old measurement.
- Proposed device interval: send the latest sample every two seconds. Do not queue old samples after failure. Use short bounded connection timeouts.
- An accepted reading returns HTTP 201 with accepted=true, session_id and sequence.
- HTTP 401: missing/wrong token. 409: duplicate, older sequence or retired session. 422: invalid fields or a reading already at least 10 seconds old.
- Restarting the backend preserves sessions and readings without refreshing their timestamps.

The single-device receiver retires the previous session when a new unique session arrives. It rejects later packets from known retired sessions. Do not generate a new session per request, replay old recordings with new identities, or run two uploaders using rain-A-01. Reprovisioning and multi-device session registration are future deployment work.

## Data freshness

The server subtracts observation_age_ms from its receipt time, then expires data after 10 seconds. Unknown or uncalibrated readings have zero usable validity. A read request, duplicate upload or backend restart does not extend a measurement's life. A backward clock step causing a future observation makes it unknown.

This prototype does not precisely measure network transit time. Use fresh samples and short timeouts; for a remote pilot, add synchronised capture timestamps and a defined transit/clock uncertainty allowance. Keep the laptop clock synchronised.

The rider app must honour valid_for_ms and its own connection failures. A browser tab displaying plain JSON may retain an old response when disconnected; the page is not an automatic freshness-aware UI. Re-fetching is required.

A disconnected resistive plate may look dry electrically. Backend freshness detects missing uploads, not every physical sensor fault. Wet means water detected on the plate; it is not a rainfall forecast or intensity measurement.

## Integration test sequence

1. Backend starts with unknown/no_reading.
2. ESP32 uploads a fresh calibrated wet reading; weather endpoint shows wet.
3. Dry the plate; a higher sequence reports dry.
4. Stop uploads for at least 10 seconds; endpoint shows unknown/stale.
5. Send a fresh higher sequence; status recovers.
6. Repeat an already accepted sequence; it must return 409 and not refresh data.
7. Restart ESP32 with a new session. Until recalibrated, send unknown/calibrated=false.
8. Check the rider app eventually displays the same status and handles expiry locally.

## Run automated tests

Run RUN_TESTS.cmd, or `python -m unittest -v test_backend.py` from this folder. Tests use isolated temporary databases, not the real sensor database. They include a localhost HTTP test, which requires local network permission.

## Deployment boundary

HTTP here is only for a trusted local prototype network. The token is not encrypted in transit. Do not port-forward or expose this Python development server directly to the internet. A remote 5G demonstration needs an authorised HTTPS deployment or proxy, verified TLS on the ESP32, credential handling and an updated deployment review. Cross-origin rider-app access is not enabled; serve it through the same origin or configure a specific allowed origin during integration.

Moving to a maintained production web framework, per-device credentials, secure device registration, rate limiting, backups and monitoring is future pilot work. Local hotspot traffic alone is not evidence of a 5G uplink.
