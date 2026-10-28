// TeduhLink local-network sensor uploader.
// Hardware: plate from 3V3 to GPIO34, 10k resistor from GPIO34 to GND.
// This sketch uses HTTP ONLY on a trusted local network. Remote deployment needs TLS.
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_system.h>

// Fill these in privately. Do not share a sketch containing real credentials.
const char* WIFI_NAME = "HUAWEI Pura 70";
const char* WIFI_PASSWORD = "sfczcute";
const char* DEVICE_TOKEN = "G_7v9u6a6wlz450UMNGt5X5FTIfWYGwRdUgJXoWWkho";
const char* UPLOAD_URL = "http://192.168.43.55:8000/api/sensor-readings";

const int SENSOR_PIN = 34;
const unsigned long SAMPLE_MS = 500;
const unsigned long UPLOAD_MS = 2000;

int dryReading = -1;
int wetReading = -1;
int currentState = -1;  // -1 unknown, 0 dry, 1 wet
int candidate = -1;
int candidateCount = 0;
int latestRaw = 0;
bool hasSample = false;
bool wasConnected = false;
unsigned long sampledAt = 0;
unsigned long lastUploadAt = 0;
unsigned long lastReconnectAt = 0;
uint32_t sequence = 0;
String sessionId;

int readAverage() {
  long sum = 0;
  for (int i = 0; i < 20; i++) {
    sum += analogRead(SENSOR_PIN);
    delay(2);
  }
  return sum / 20;
}

bool calibrated() {
  return dryReading >= 0 && wetReading >= 0 && wetReading - dryReading >= 100;
}

void resetState() {
  currentState = -1;
  candidate = -1;
  candidateCount = 0;
}

void takeSample() {
  // After a long pause, rebuild the stable status from new samples.
  if (hasSample && millis() - sampledAt > 2500UL) resetState();
  latestRaw = readAverage();
  sampledAt = millis();
  hasSample = true;
  sequence++;

  if (!calibrated()) {
    resetState();
  } else {
    int span = wetReading - dryReading;
    int proposed = -1;
    if (latestRaw <= dryReading + span * 40 / 100) proposed = 0;
    else if (latestRaw >= dryReading + span * 60 / 100) proposed = 1;
    if (proposed == -1) {
      candidate = -1;
      candidateCount = 0;
    } else {
      if (proposed == candidate) candidateCount++;
      else { candidate = proposed; candidateCount = 1; }
      if (candidateCount >= 3) { currentState = proposed; candidateCount = 3; }
    }
  }
  Serial.print("Raw: "); Serial.print(latestRaw);
  Serial.print(" | ");
  Serial.println(currentState == 1 ? "WET" : currentState == 0 ? "DRY" : "UNKNOWN");
}

void uploadLatest() {
  if (WiFi.status() != WL_CONNECTED || !hasSample) return;
  if (String(DEVICE_TOKEN) == "PASTE_DEVICE_TOKEN_HERE" || strlen(DEVICE_TOKEN) < 24) {
    Serial.println("Upload skipped: fill DEVICE_TOKEN with the private backend token.");
    return;
  }
  unsigned long age = millis() - sampledAt;
  if (age >= 5000UL) {
    Serial.println("Upload skipped: sample too old; waiting for a new sample.");
    return;
  }
  const char* status = currentState == 1 ? "wet" : currentState == 0 ? "dry" : "unknown";
  String body;
  body.reserve(320);
  body = "{\"stop_id\":\"A\",\"device_id\":\"rain-A-01\",\"session_id\":\"";
  body += sessionId;
  body += "\",\"sequence\":"; body += String(sequence);
  body += ",\"status\":\""; body += status;
  body += "\",\"raw\":"; body += String(latestRaw);
  body += ",\"calibrated\":"; body += calibrated() ? "true" : "false";
  body += ",\"observation_age_ms\":"; body += String(age);
  body += "}";

  WiFiClient client;
  HTTPClient http;
  http.setConnectTimeout(1500);
  http.setTimeout(1500);
  http.setReuse(false);
  if (!http.begin(client, UPLOAD_URL)) {
    Serial.println("Could not initialise upload URL.");
    return;
  }
  http.addHeader("Content-Type", "application/json");
  http.addHeader("Authorization", String("Bearer ") + DEVICE_TOKEN);
  int code = http.POST(body);
  if (code == 201) {
    Serial.print("UPLOAD OK (201) | "); Serial.print(status);
    Serial.print(" | sequence "); Serial.println(sequence);
  } else if (code > 0) {
    Serial.print("UPLOAD REJECTED | HTTP "); Serial.println(code);
    Serial.println(http.getString());
  } else {
    Serial.print("UPLOAD FAILED | "); Serial.println(HTTPClient::errorToString(code));
  }
  http.end();
  // No backlog: the next attempt sends a newly sampled reading.
}

void setup() {
  Serial.begin(115200);
  pinMode(SENSOR_PIN, INPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(SENSOR_PIN, ADC_11db);
  delay(1000);
  WiFi.mode(WIFI_STA);
  WiFi.setAutoReconnect(true);
  WiFi.begin(WIFI_NAME, WIFI_PASSWORD);
  char session[40];
  snprintf(session, sizeof(session), "boot-%08lx%08lx%08lx%08lx",
           (unsigned long)esp_random(), (unsigned long)esp_random(),
           (unsigned long)esp_random(), (unsigned long)esp_random());
  sessionId = session;
  Serial.println("\nTeduhLink rain uploader - local prototype");
  Serial.println("Dry the plate and send d. Wet the plate and send w.");
  Serial.println("Calibration is lost on restart. Unknown is uploaded until ready.");
  Serial.print("Destination: "); Serial.println(UPLOAD_URL);
}

void loop() {
  bool connected = WiFi.status() == WL_CONNECTED;
  if (connected && !wasConnected) {
    Serial.print("Wi-Fi connected. ESP32 IP: "); Serial.println(WiFi.localIP());
  }
  if (!connected && wasConnected) Serial.println("Wi-Fi lost; uploads paused.");
  wasConnected = connected;
  if (!connected && millis() - lastReconnectAt >= 15000UL) {
    lastReconnectAt = millis();
    WiFi.reconnect();
  }
  while (Serial.available() > 0) {
    char command = Serial.read();
    if (command == 'd' || command == 'w') {
      int reference = readAverage();
      if (command == 'd') dryReading = reference;
      else wetReading = reference;
      resetState();
      hasSample = false;
      Serial.print(command == 'd' ? "Saved DRY: " : "Saved WET: ");
      Serial.println(reference);
    }
  }
  if (!hasSample || millis() - sampledAt >= SAMPLE_MS) takeSample();
  if (millis() - lastUploadAt >= UPLOAD_MS) {
    uploadLatest();
    lastUploadAt = millis();
  }
  delay(2);
}
