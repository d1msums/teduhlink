<div align="center">

# 🌧️ TeduhLink
## Find Shelter. Check the Crowding. Choose Your Stop.

### *Connected shelter information for Cyberjaya riders*

**Cyberjaya 5G Innovation Challenge**  
*5G Connected & Safe Last-Mile Mobility*

![Status](https://img.shields.io/badge/Status-Prototype_in_Development-A3E635?style=for-the-badge)
![IoT](https://img.shields.io/badge/IoT-ESP32-00979D?style=for-the-badge)
![AI](https://img.shields.io/badge/AI-Person_Detection-7C3AED?style=for-the-badge)
![Backend](https://img.shields.io/badge/Backend-Python-3776AB?style=for-the-badge)
![Location](https://img.shields.io/badge/Location-Cyberjaya-111827?style=for-the-badge)

[Project Overview](#-project-overview) ·
[Local Context](#-inspiration-and-local-context) ·
[How It Works](#-how-it-works) ·
[Prototype Status](#-prototype-status) 

</div>

---

## 🌍 Project Overview

**TeduhLink helps riders find nearby shelter during rain and compare estimated crowding before choosing where to stop.**

The project explores a practical question:

> When rain interrupts a journey, how can a rider find a suitable nearby shelter and see whether its monitored area appears busy?

TeduhLink combines:

- A shelter directory and map.
- An ESP32-connected rain-contact sensor.
- Camera-based person detection.
- A Python backend.
- A rider-facing web app.

Riders can browse shelters at any time, including when the rain sensor is dry or unavailable.

---

## 💡 Inspiration and Local Context

TeduhLink is an independent student prototype inspired by the TEDUH rider-rest initiative and its relevance to Cyberjaya.

### A local connection

Media Selangor reported in September 2025 that MPSepang planned a TEDUH hub off Jalan Teknokrat 6 in Cyberjaya.

This provides local context for the project. The historical report alone does not establish the facility’s current operating status.

[Source: Selangor councils get RM30,000 each to build delivery rider rest stops — Media Selangor, September 2025](https://mediaselangor.com/en/2025/09/320927)

### Riders’ shelter needs

A September 2026 Media Selangor report describes riders seeking covered places to rest and dealing with unpredictable weather. The interviews concern Petaling Jaya and the wider Klang Valley.

[Source: TEDUH gives Selangor riders respite from sun, rain and the road — Media Selangor, 4 September 2026](https://mediaselangor.com/en/2026/09/393885)

### What we are exploring

These sources support the importance of suitable rider rest and shelter facilities.

TeduhLink explores whether a digital service combining shelter discovery and recent crowding estimates could help riders choose a stopping place.

**TeduhLink is not an official TEDUH or MPSepang service. No partnership or endorsement is claimed.**

---

## 🛵 The Rider Experience

1. A rider encounters rain or notices a rain-sensor prompt.
2. They open **Find Shelter**.
3. They explore listed locations and available facility information.
4. They compare crowding estimates where monitoring is available.
5. They inspect a stop and open directions where the destination is verified.
6. They decide where to stop.

Crowding information helps inform that decision. It does not reserve space or guarantee availability.

---

## 🧩 Main Features

### 🏠 Shelter Discovery

A directory and map present proposed Cyberjaya stopping locations.

Facility descriptions, access arrangements and coordinates must be verified before being presented as confirmed.

### 🌧️ Rain-Contact Prompt

An ESP32 reads an MH-RD resistive plate and uploads observations to the backend.

When water contacts the plate, the app can display:

> Rain sensor activated — Need shelter? Compare nearby stops and crowding.

For outdoor use, the plate would be positioned where rainfall can reach it.

The sensor detects water contact. It can remain wet after rain stops and does not prove that rain is currently falling.

### 👥 Estimated Crowding

A camera and pretrained person-detection model estimate people visible inside the monitored area.

The app presents simple categories:

- **No people detected**
- **Some people detected**
- **Busy**
- **Crowding unavailable**

### ⏱️ Information Freshness

Rain-sensor and camera observations have independent update times.

When an observation expires, the app should show it as unavailable rather than continuing to present it as current.

---

## 🔄 How It Works

```text
Rain-contact plate
        │
        ▼
      ESP32 ───── Sensor readings ──────┐
                                      │
                                      ▼
                               Python Backend
                                      ▲
                                      │
Camera ──► Person Detection ── Counts ──┘
                                      │
                                      ▼
                               TeduhLink App
                                      │
                                      ▼
                         Rider explores shelter options
```

The current demonstration runs on a local network.

The ESP32 sends sensor readings to the backend. The camera process is designed to upload person-count observations separately. The app retrieves the latest status for each stream.

---

## 🌧️ What the Rain Sensor Means

The rain plate supports a local rain-related prompt.

It does not measure:

- Shelter-floor wetness.
- Road friction.
- Rainfall intensity.
- Future rain arrival.
- Weather across all of Cyberjaya.

A dry plate does not prove that it is not raining elsewhere.

One exposed rain-contact sensor is sufficient for the current demonstration. Future sensor placement should depend on coverage needs, maintenance and field validation.

---

## 👥 Crowding Categories

The controlled demonstration uses these thresholds:

- **0 detected people:** No people detected.
- **1–2 detected people:** Some people detected.
- **3 or more detected people:** Busy.
- **Missing or expired observation:** Crowding unavailable.

These are demonstration thresholds, not certified shelter-capacity limits.

A zero count means the model detected no people in its monitored view. It does not guarantee that the entire location is empty.

The system does not identify riders or count available motorcycle parking bays.

---

## 📡 Proposed Role of 5G

The proposed outdoor deployment uses a 5G router or phone hotspot to connect monitoring equipment to an online service.

```text
ESP32 / Camera Gateway
          │
      Local connection
          │
      5G Router
          │
        Internet
          │
     Hosted Service
          │
      Rider Apps
```

The ESP32 itself is not a 5G device.

5G could provide connectivity for distributed monitoring locations where fixed internet access is inconvenient. A future implementation could also evaluate camera uploads for remote inference.

The current local demonstration does not establish a 5G performance advantage.

Small status messages can also operate over other networks. Any claim about lower delay, higher reliability or greater capacity requires a measured comparison.

---

## 🧪 Prototype Status

### Confirmed so far

- ESP32 sensor readings and dry/wet calibration.
- Sensor uploads to the local Python backend.
- Rain-sensor readings displayed on the local web interface.
- Backend handling for expired sensor readings.
- Initial local person-detection testing with one person.
- Exported Stitch interface screens.

### Still to verify or complete

- Camera-to-backend-to-app integration.
- Multi-person counting and crowding-category transitions.
- Camera-disconnection behaviour in the app.
- Final interface consistency and layout.
- Complete demonstration recording.
- Public interactive demo.
- Any proposed public live-data deployment.
- End-to-end 5G evaluation.

This section reflects development progress and should be updated after each completed test.

---

## 📍 Locations and Demonstration Data

Real Cyberjaya place names may appear in the interface to illustrate the intended experience.

Their inclusion does not mean that:

- Monitoring equipment is installed there.
- The owner has approved the project.
- The location is an official project partner.
- Shelter access or available space is guaranteed.

Current physical testing takes place indoors.

The interface distinguishes:

- **Indoor prototype feed**
- **Simulated alternative**
- **No monitoring**

Distances, journey times, facilities and directions should be labelled as examples or unverified when they have not been validated.

---

## 🧰 Technology

### Hardware

- ESP32 development board.
- MH-RD rain-contact plate and associated wiring.
- USB power/data cable.
- Breadboard and jumper wires.
- Camera or laptop webcam.
- Laptop for the backend and person-detection process.
- Local Wi-Fi connection.

### Software

- Arduino IDE.
- Python backend.
- SQLite prototype storage.
- Pretrained YOLO person detection.
- HTML, CSS and JavaScript interface exported from Google Stitch.
- Git and GitHub.

---

## 📂 Repository Structure

```text
teduhlink/
├── backend/       # API, data storage and sensor ingestion
├── ml/            # Camera and person-detection code
├── frontend/      # Rider interface and live-data connection
├── .gitignore
└── README.md
```

Local credentials, device tokens, runtime databases and downloaded model weights should not be committed.

Firmware containing private Wi-Fi or device credentials must be sanitised before sharing.

---

## 🔌 Backend API

The prototype includes:

- `GET /health` — service health.
- `GET /api/stops` — stop information.
- `GET /api/stops/A/weather` — rain-plate observation.
- `GET /api/stops/A/occupancy` — crowding observation.
- `POST /api/sensor-readings` — authenticated sensor uploads.
- `POST /api/occupancy-readings` — authenticated count uploads.

The weather endpoint describes a local sensor observation, not a weather forecast.

Private upload credentials must not appear in public frontend code.

---

## 🎬 Demonstration Plan

1. Introduce the rider’s shelter problem and TEDUH inspiration.
2. Show the shelter directory and selected-stop screen.
3. Show the dry rain plate and corresponding app status.
4. Apply water and show the app update.
5. Demonstrate camera counts as people enter and leave.
6. Show the “Busy” category during the multi-person test.
7. Stop camera updates and show crowding becoming unavailable.
8. Show the rain sensor continuing independently.
9. Explain the proposed 5G deployment and remaining validation.

AI-generated introductory footage is labelled as illustrative. Simulated data is identified separately from actual hardware observations.

---

## 🚀 Next Steps

- [ ] Verify camera-to-app updates.
- [ ] Complete multi-person tests.
- [ ] Check independent stale-data behaviour.
- [ ] Finish interface layout and wording.
- [ ] Record the complete demonstration.
- [ ] Publish a clearly labelled interactive demo.
- [ ] Gather rider feedback.
- [ ] Verify candidate shelter access and facilities.
- [ ] Seek permission for any outdoor pilot.
- [ ] Evaluate connectivity and maintenance requirements.

---

<div align="center">

### 🌧️ TeduhLink

**Find shelter. Check the crowding. Choose your stop.**

*An independent student prototype for connected last-mile mobility in Cyberjaya.*

</div>
