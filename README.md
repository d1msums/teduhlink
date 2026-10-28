<div align="center">
        
# 🌧️ TeduhLink
## Connected Shelter Information for Cyberjaya Riders

### *Know the conditions. See the crowding. Choose your stop.*

**Cyberjaya 5G Innovation Challenge**  
*5G Connected & Safe Last-Mile Mobility*

![Status](https://img.shields.io/badge/Status-Working_Prototype-A3E635?style=for-the-badge)
![IoT](https://img.shields.io/badge/IoT-ESP32-00979D?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Person_Detection-7C3AED?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-Python-3776AB?style=for-the-badge)
![Location](https://img.shields.io/badge/Location-Cyberjaya-111827?style=for-the-badge)

[Explore the Project](#-project-overview) ·
[How It Works](#-how-it-works) ·
[Prototype Scope](#-prototype-scope) 

</div>

---

## 🌍 Project Overview

**TeduhLink is an IoT and computer-vision prototype that helps riders compare potential stopping places using recent local wetness observations and estimated crowding.**

The project explores a practical question:

> Before heading to a stop, can a rider see whether its monitored area is wet and whether many people are already there?

TeduhLink combines an ESP32-connected moisture sensor, camera-based person detection and a shared backend. A planned rider-facing interface presents this information alongside stop locations and facilities.

---

## 🛵 The Problem We Address

A map can show where a place is, but a static listing does not necessarily tell riders:

- Whether a monitored sensor at that location is currently wet.
- Whether the observed shelter area appears busy.
- When the information was last updated.
- Whether live information has become unavailable.

TeduhLink explores how these observations can help riders make more informed stopping decisions around Cyberjaya.

The prototype demonstrates the technical concept. Citywide demand, location suitability and operational arrangements still require field validation.

---

## 💡 Our Solution

TeduhLink brings two independent observations together:

### 🌧️ Local Wetness

An **ESP32 and MH-RD resistive plate** detect moisture contacting the sensor plate.

The backend receives the readings and makes the latest condition available to the application.

### 👥 Estimated Crowding

A camera and pretrained person-detection model estimate the number of people visible inside the monitored area.

The interface translates the count into simple categories:

- **No people detected**
- **Some people detected**
- **Busy**
- **Crowding unavailable**

### 📱 Rider Interface

The interface is designed to show:

- Stop names and locations.
- Local wetness observations.
- Estimated crowding.
- Separate update times for each observation.
- Clearly labelled live, simulated and unavailable information.
- Directions to eligible, verified real-world destinations.

---

## 🔄 How It Works

```text
MH-RD Sensor Plate
        │
        ▼
      ESP32 ─────── Wetness readings ──────┐
                                         │
                                         ▼
                                  Python Backend
                                         │
Camera ──► Person Detection ──────────────┘
                                         │
                                         ▼
                                  Stop Status API
                                         │
                                         ▼
                               Rider App / Web Interface
```

1. Water contacting the plate changes its electrical reading.
2. The ESP32 sends the reading to the backend.
3. The camera model estimates how many people are visible.
4. The backend tracks the latest observations and their timestamps.
5. The interface displays the conditions for the selected stop.
6. If a reading becomes stale, its status becomes unavailable.

**Wetness and crowding are independent:** a camera outage should not hide a wetness reading that is still arriving.

---

## ✨ What Makes TeduhLink Different?

### Information before arrival

The concept helps riders assess a stop before reaching it.

### Physical observations, not only static listings

The prototype connects actual sensor readings and camera estimates to a shared backend.

### Clear information freshness

An old observation should not remain on-screen as if it were current.

### Simple crowding categories

Riders see an understandable summary rather than needing to interpret a camera feed.

### A repeatable deployment model

The same structure could support additional stops, each with its own identifier, observations and location information.

Expansion would require suitable sites, permissions, connectivity, power and maintenance.

---

## 📡 Where 5G Fits

The proposed deployment uses a **5G router or phone hotspot as the internet connection** between field equipment and the hosted service.

```text
ESP32 / Camera Gateway
          │
     Local Wi-Fi
          │
     5G Router / Phone
          │
       Internet
          │
    Hosted Backend
          │
       Rider App

---

## 🧪 Prototype Scope

### Implemented and initially tested

- ESP32 moisture-sensor readings.
- Wet and dry calibration.
- Sensor uploads to the local backend.
- Backend weather status and stale-reading handling.
- Local person detection tested with one person.

### In progress or awaiting verification

- Multi-person counting and crowding-category tests.
- Complete camera-to-backend integration.
- Connecting the designed interface to live API responses.
- Public backend deployment.
- End-to-end demonstration over a 5G connection.

### Outside the current prototype

- Rain arrival-time prediction.
- Rainfall intensity measurement.
- Road friction or skid-risk measurement.
- Motorcycle parking-bay detection.
- Shelter reservations.
- Guaranteed capacity or availability.
- Citywide operational deployment.

---

## 👥 Crowding Categories

For the controlled demonstration:

- **0 detected people:** No people detected.
- **1–2 detected people:** Some people detected.
- **3 or more detected people:** Busy.
- **Missing or stale observations:** Crowding unavailable.

These are demonstration thresholds, not certified facility-capacity limits.

A count of zero means the model detected no people in the monitored area. It does not guarantee that the entire location is empty.

The model detects people—not rider identities, motorcycles or available parking bays.

---

## 📍 Real Locations and Demonstration Data

The interface may use real Cyberjaya location names to illustrate the intended rider experience.

**Using a real place name does not mean equipment has been installed there or that the site owner has endorsed the project.**

For the current demonstration:

- Physical sensor and camera testing takes place in a controlled environment.
- Any association with a real stop is labelled as a demonstration.
- Simulated alternative stops are identified explicitly.
- Facilities and access arrangements must be verified before being presented as confirmed.
- Directions are disabled for fictional destinations or indoor test areas.

---

## 🧰 Technology and Equipment

### Hardware

- ESP32 development board.
- MH-RD resistive moisture plate and compatible circuitry.
- USB power/data cable.
- Jumper wires and breadboard.
- Camera or laptop webcam.
- Laptop for the backend and person-detection process.
- Phone hotspot or router for connectivity.

### Software

- Arduino IDE for ESP32 firmware.
- Python backend.
- SQLite for prototype data storage.
- Pretrained YOLO person detection.
- Google Stitch for interface design.
- Git and GitHub for version control.

The exported interface still needs application code to connect it to the backend.

---

## 📂 Repository Structure

```text
teduhlink/
├── backend/       # API, sensor ingestion and stop-status logic
├── ml/            # Camera-based person detection
├── .gitignore
└── README.md
```

Frontend and firmware source can be added when prepared for sharing.

Do not commit Wi-Fi passwords, device tokens, private configuration, local databases or identifiable camera recordings.

---

## 🔌 Backend Interfaces

The prototype backend includes:

- `GET /health` — service health.
- `GET /api/stops` — stop information.
- `GET /api/stops/A/weather` — Stop A wetness status.
- `GET /api/stops/A/occupancy` — Stop A crowding status.
- `POST /api/sensor-readings` — receive sensor readings.
- `POST /api/occupancy-readings` — receive person-count observations.

Device upload credentials must remain private and must not be included in public frontend code.

---

## 🎬 Demonstration Walkthrough

1. Open the application and select the demonstration stop.
2. Show a dry sensor plate and its latest backend status.
3. Apply a small amount of water to the plate.
4. Show the wetness update reaching the interface.
5. Have a person enter the monitored camera area.
6. Show the crowding estimate change.
7. Add participants to demonstrate the “Busy” category.
8. Stop camera updates and show crowding becoming unavailable.
9. Show wetness continuing to update independently.
10. Explain how the same approach could extend to approved Cyberjaya sites.

Any simulated screen, location or data source is labelled during the demonstration.

---

## 🚀 Next Steps

- [ ] Complete multi-person testing.
- [ ] Verify camera uploads to the backend.
- [ ] Integrate the exported interface.
- [ ] Test wetness and crowding freshness separately.
- [ ] Deploy and test the hosted backend.
- [ ] Demonstrate and measure the 5G connection.
- [ ] Validate candidate stop facilities and access.
- [ ] Gather rider feedback.
- [ ] Record the final demonstration.

---

<div align="center">

### 🌧️ TeduhLink
**Recent observations. Clearer stop choices.**

*A student prototype exploring connected last-mile mobility in Cyberjaya.*

</div>
