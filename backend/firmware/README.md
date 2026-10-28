# ESP32 rain uploader: local integration

Open TeduhLink_Rain_Upload/TeduhLink_Rain_Upload.ino in Arduino IDE.

1. Keep a backup of your earlier sensor sketch.
2. Fill WIFI_NAME, WIFI_PASSWORD, and DEVICE_TOKEN locally. Copy the token text from ../../data/device-token.txt after the backend has started. Do not include the word Bearer in DEVICE_TOKEN.
3. UPLOAD_URL is already http://192.168.43.55:8000/api/sensor-readings. Update it if the laptop's Wi-Fi IP changes.
4. Start START_BACKEND.cmd, keep it open, and connect laptop and ESP32 to the same trusted 2.4 GHz hotspot.
5. Select ESP32 Dev Module and the correct COM port; upload. Open Serial Monitor at 115200.
6. Dry the plate and send d. Add drops across adjacent tracks, wait for readings to settle, and send w. Calibration resets on every reboot.
7. Expect UPLOAD OK (201). Unknown uploads before calibration are correct.
8. View http://192.168.43.55:8000/api/stops/A/weather and refresh manually. Expect wet, then dry after drying the plate.
9. Unplug the ESP32, wait at least 10 seconds, refresh: expect unknown/stale. Plain JSON does not update without refresh.
10. Reconnect, recalibrate and confirm recovery. Run only one uploader using rain-A-01.

The sketch no longer serves the previous ESP32 /status page. Read the backend weather URL instead. Do not browse the upload URL to test it: a browser sends GET, whereas uploading requires POST.

Troubleshooting:
- HTTP 401: token mismatch. Recopy the private token, without whitespace or Bearer prefix.
- HTTP 409: older/retired session or duplicate; stop other rain-A-01 uploaders and restart this board.
- HTTP 422: inspect the returned explanation; check calibration/status and payload.
- Connection failed: server window, laptop IP, port 8000, firewall permission for your trusted network, and hotspot client isolation. Do not disable the firewall globally.
- Constant unknown: set both reference values; wet must exceed dry by at least 100 counts for this sketch.

Prototype limitations: local HTTP, not TLS; never expose directly to the internet. Wi-Fi-to-laptop traffic is not proof of a 5G uplink. HTTP requests are synchronous with short connection/read timeouts, so failed uploads can delay sampling. Recovery rebuilds the stable status after a long sample gap. No old-reading backlog is sent. Sensor cable disconnection can look dry electrically; freshness only detects missing uploads. Continuous DC on a wet resistive plate encourages corrosion; disconnect after testing. Before remote deployment, use HTTPS, strengthen capture-time accounting and review reconnect behaviour.

Validation: payload field names/types and Arduino HTTPClient API were checked against the backend and official documentation. No Arduino CLI/compiler was available in the creation session, so compilation and physical hardware verification must be done in Arduino IDE.
