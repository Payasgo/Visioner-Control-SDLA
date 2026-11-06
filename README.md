# Visioner-Control-SDLA

**AI Driving Coach & Smart Traffic-Law Assistance | Designed with Indian roads in mind**

Visioner-Control-SDLA is a Python-based driver-assistance and driving-lesson project. It combines a Flask dashboard, simulated or OBD-oriented vehicle telemetry, driver-skill feedback, safety coaching, and violation-recording APIs. The repository also contains optional computer-vision, camera, audio, and machine-learning components.

> **Project status:** The web dashboard, simulator-oriented API, automated tests, and Docker image build are the currently testable baseline. Hardware-dependent features require compatible devices, optional dependencies, configuration, and real-world validation. This project is a prototype/driver-assistance aid—not an autonomous-driving system, certified enforcement device, or substitute for attentive driving.

## Contents

- [Highlights](#highlights)
- [Project status and limitations](#project-status-and-limitations)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Run with Docker](#run-with-docker)
- [Configuration](#configuration)
- [HTTP API](#http-api)
- [Optional hardware and ML features](#optional-hardware-and-ml-features)
- [Tests and code quality](#tests-and-code-quality)
- [Deployment](#deployment)
- [Roadmap and future improvements](#roadmap-and-future-improvements)
- [Contributing](#contributing)
- [License](#license)

## Highlights

| Component | Current purpose |
|---|---|
| Web dashboard | Flask dashboard for driver skill, speed, lesson progress, coaching tips, and recent violations |
| Telemetry simulator | Supplies sample vehicle data for development without a connected vehicle |
| Driver-skill classifier | Rule-based Beginner / Medium / Pro classification |
| Driving lesson tracker | Tracks elapsed lesson time, telemetry samples, and detected mistakes |
| ADAS utilities | Speed-limit guidance, gear advice, and lane-deviation/correction logic |
| Violation API | Validates and records violation events in SQLite, with indexed history and summary statistics |
| Session lifecycle | Explicit start, pause, resume, and end actions; only ingested telemetry counts as a sample |
| Evidence utilities | Saves timestamped image evidence when called with a valid image frame |
| Voice coaching | Provides driving tips, with optional text-to-speech support |
| Optional computer vision | Camera and driver-monitoring scripts that require additional packages and model assets |

## Project status and limitations

The repository includes both runnable software and integrations that need external hardware or model files.

- **Dashboard/API:** covered by the automated CI test and Docker build workflow.
- **Container publishing:** the GitHub Actions workflow builds and pushes an image to GitHub Container Registry (GHCR).
- **Server deployment:** requires valid SSH deployment secrets and a reachable server; a successful image push alone does not mean the application has been deployed.
- **OBD-II:** use a compatible ELM327/OBD-II adapter and verify vehicle/protocol compatibility. Simulator data is not live vehicle data.
- **Camera and drowsiness detection:** require a supported camera, optional vision dependencies, and the appropriate landmark/model assets.
- **ML classification:** requires installing the ML extra and supplying a trained model. The rule-based classifier is the baseline.
- **Lane correction and speed guidance:** are advisory software outputs. They are not connected to a certified steering/braking controller and must not be treated as control authority.

Always test integrations in a safe, stationary, controlled environment before any vehicle use. Do not interact with the dashboard while driving.

## Architecture

The main entry point is `run.py`.

```text
Visioner-Control-SDLA/
├── app/
│   ├── __init__.py              # Flask application factory
│   ├── routes_full.py           # Dashboard and JSON API routes
│   ├── adas/                    # Speed, gear, and lane-assistance logic
│   ├── behavior/                # Skill classification, lesson tracking, coaching
│   ├── enforcement/             # Evidence capture and violation logging
│   ├── hardware/                # Camera and hardware-facing helpers
│   ├── telemetry/               # Simulator and OBD-oriented interfaces
│   └── utils/                   # Application configuration and utilities
├── modules/                     # Reusable project modules
├── scripts/                     # Runnable pipeline and utility scripts
├── model/                       # Model training utilities
├── tests/                       # Automated tests
├── requirements-ci.txt          # Lightweight CI/container dependencies
├── requirements.txt             # Broader project dependency list
├── pyproject.toml               # Package metadata and optional extras
├── Dockerfile
├── docker-compose.yml
└── run.py                       # Application entry point
```

## Requirements

- Python 3.10 or newer (the Docker image uses Python 3.11).
- pip.
- Git.
- Optional: Docker Engine and Docker Compose.
- Optional hardware: supported camera, OBD-II adapter, microphone/speaker, and compatible Linux device.

## Quick start

### 1. Clone the repository

```bash
git clone https://github.com/Payasgo/Visioner-Control-SDLA.git
cd Visioner-Control-SDLA
```

### 2. Create and activate a virtual environment

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install the core application and development tools

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

This installs the dependencies declared in `pyproject.toml` plus pytest. The broader `requirements.txt` includes heavier integrations such as audio, OCR, and deep-learning packages; install those only when the corresponding feature is needed and your platform supports them.

### 4. Start the dashboard

```bash
python run.py web
```

Open [http://localhost:5000](http://localhost:5000).

For local development only, enable Flask's debug/reloader mode:

```bash
python run.py web --debug
```

Do not enable debug mode on a public or production server.

### 5. Run simulator mode

```bash
python run.py simulator
```

The simulator is intended for development and demonstration. It does not represent readings from a real vehicle.

## Run with Docker

Build and start the dashboard:

```bash
docker compose up --build
```

Open [http://localhost:5000](http://localhost:5000). Stop the service with:

```bash
docker compose down
```

The container uses Gunicorn behind the WSGI entry point and runs as a non-root user. Docker Compose persists SQLite data in the `visioner-data` named volume and includes an HTTP health check. Keep the service behind a trusted reverse proxy and add authentication/authorization before exposing it publicly.

## Configuration

The current driving thresholds are defined in `app/utils/config.py`:

```python
CONFIG = {
    "mode": "simulator",          # "simulator" or "obd"
    "max_speed_beg": 40,          # km/h
    "max_speed_med": 60,          # km/h
    "max_speed_pro": 80,          # km/h
    "min_gear_change_speed": 20,  # km/h
}
```

These are project defaults, not legal speed limits. Actual road limits depend on location, vehicle class, signage, and applicable law. Do not use these values as a replacement for posted road signs or official regulations.

## HTTP API

The Flask application exposes the following endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Dashboard HTML |
| `/api/health` | GET | Basic application health response |
| `/api/telemetry` | GET | Read the latest telemetry snapshot without changing lesson counters |
| `/api/telemetry` | POST | Ingest one validated telemetry event; requires a unique `event_id` |
| `/api/session` | GET | Current skill band, lesson progress, and coaching tip |
| `/api/session` | POST | Start, pause, resume, or end a lesson session |
| `/api/violations?n=20` | GET | Recent violation records; `n` must be between 1 and 200 |
| `/api/violations` | POST | Validate and record a violation |
| `/api/violations/stats` | GET | Total violations, counts by type, and recent records |

### Health check

```bash
curl http://localhost:5000/api/health
```

Returns a JSON object containing a status and UTC timestamp.

### Telemetry

```bash
curl http://localhost:5000/api/telemetry
```

The response includes `telemetry`, `skill`, `tip`, and `progress`. Telemetry fields are supplied by the configured telemetry source; in the default development setup this is simulated data.

### Record a violation

```bash
curl -X POST http://localhost:5000/api/violations \
  -H "Content-Type: application/json" \
  -d '{
    "violation_type": "SPEEDING",
    "license_plate": "TEST-123",
    "speed_kmh": 75,
    "confidence": 0.95,
    "location": "Test location"
  }'
```

The API validates the JSON object and numeric ranges before recording the event. A successful creation returns HTTP `201`; a retry using the same `event_id` returns the existing record; invalid input returns HTTP `400`. Records are stored in `data/logs/violations.sqlite3`. Existing `violations.csv` records are imported once when the SQLite database is first initialized. Do not submit real personal or vehicle-identifying data to an unauthenticated/public instance.

### Ingest telemetry

Dashboard reads do not create samples. A simulator or sensor integration must explicitly submit each new event with a stable event ID:

```bash
curl -X POST http://localhost:5000/api/telemetry \\
  -H 'Content-Type: application/json' \\
  -d '{"event_id":"demo-0001","speed":42,"brake_events":0,"lane_offset":0.1}'
```

Supported fields include `speed` (0–300 km/h), `brake_events` (integer 0–100), `lane_offset` (-10–10), `steering_angle` (-720–720), `harsh_acceleration` (0–100), and `speed_limit` (0–300). The same event ID is accepted only once per active lesson. A new session clears its event history and counters.

### Session controls

```bash
curl -X POST http://localhost:5000/api/session -H 'Content-Type: application/json' -d '{"action":"start"}'
# Supported actions: start, pause, resume, end
```

The driver-coaching band is a conservative rule-based heuristic using behaviour signals; it is not a validated assessment of driving skill. Speed alone never grants a higher band.

## Optional hardware and ML features

The project declares optional extras in `pyproject.toml`:

```bash
# ML model support
python -m pip install -e ".[ml]"

# Camera/voice-related hardware support
python -m pip install -e ".[hardware]"

# Development and all optional extras
python -m pip install -e ".[dev,ml,hardware]"
```

Some scripts may need additional system packages or assets not installed by these extras. For example, dlib-based facial landmark detection requires a compatible landmark predictor file. Follow the relevant script's instructions and configure its model path (for example, with `DLIB_PREDICTOR_PATH`) before running it.

The full `requirements.txt` includes additional packages for OCR, object detection, audio input, and TensorFlow. These can be difficult to install on some operating systems and single-board computers; install only what you need, and check each dependency's platform support.

## Tests and code quality

Install the development extra and run:

```bash
python -m pytest -v
```

The GitHub Actions CI workflow also compiles Python modules, runs the test suite, and builds the Docker image. The CI dependency set is intentionally lightweight and does not validate physical camera, audio, OBD-II, or vehicle-control hardware.

Before opening a pull request, please run the tests locally and include tests for new behavior.

## Deployment

The CD workflow publishes the container image to:

```text
ghcr.io/payasgo/visioner-control:latest
```

The optional SSH deployment step expects these GitHub Actions repository secrets:

- `SERVER_IP` — hostname or IP address of the deployment server.
- `SERVER_USER` — SSH login username.
- `SERVER_SSH_KEY` — private SSH key authorized on that server.

The server must have Docker installed and network access to GHCR. If the GHCR package is private, configure a suitable server-side package-read credential (with least-privilege `read:packages`) or make the package public; do not rely on a short-lived workflow token for persistent server access. Never commit credentials, private keys, or tokens to the repository.

The current deployment workflow should be considered configured only after the SSH step completes successfully and the deployed service passes a health check.

## Roadmap and future improvements

The following are planned improvements, not claims that these capabilities are already complete.

### Reliability and security
- [ ] Add authentication and role-based authorization to dashboard and violation-management APIs (required before public deployment).
- [ ] Add API rate limiting, request-size limits, security headers, and production CORS policy.
- [x] Move violation records to SQLite with indexes and one-time import of existing CSV history.
- [ ] Persist lesson/session history in SQLite; the current lesson tracker is process-local.
- [ ] Add structured, rotating logs and robust handling of concurrent writes.
- [ ] Add persistent Docker volumes, backup/restore procedures, and deployment health checks.
- [ ] Add deployment rollback and immutable image tags tied to Git commit SHAs.

### Driving lessons and telemetry
- [x] Separate telemetry ingestion from dashboard reads; ingestion requires an event ID and duplicate IDs are ignored.
- [x] Add session start, pause, resume, and end controls.
- [ ] Run a dedicated simulator/sensor ingestion loop so the dashboard receives continuously refreshed telemetry without generating events from page reads.
- [ ] Add timestamped telemetry storage, session identifiers, and accurate per-session summaries.
- [ ] Implement and validate live OBD-II/ELM327 readings, connection recovery, and supported PID discovery.
- [ ] Add GPS integration and a verified source for location-aware road speed limits.
- [ ] Support multiple driver profiles and configurable lesson plans.

### Computer vision and safety
- [ ] Add camera reconnect handling, frame validation, and configurable camera selection.
- [ ] Evaluate drowsiness detection across lighting conditions, camera positions, and diverse users.
- [ ] Add model versioning, confidence thresholds, and documented validation datasets for ML features.
- [ ] Measure lane-detection accuracy and clearly separate advisory steering suggestions from actual vehicle control.
- [ ] Add a privacy-conscious evidence retention policy, access controls, and configurable deletion.

### Dashboard and developer experience
- [ ] Add live charts, historical trends, and downloadable session reports.
- [ ] Replace periodic polling with WebSockets or Server-Sent Events where appropriate.
- [x] Run the web container with Gunicorn, a non-root user, persistent data volume, and health check.
- [ ] Improve mobile accessibility and dashboard responsiveness.
- [ ] Add API schema documentation (OpenAPI), integration tests, and test coverage reporting.
- [ ] Add dependency vulnerability scanning, formatting, linting, and type checking to CI.

### Validation and release readiness
- [ ] Add hardware-in-the-loop tests for camera, audio, and OBD-II integrations.
- [ ] Add safe simulator scenarios for sensor failures, stale telemetry, and disconnected devices.
- [ ] Document supported Raspberry Pi/Linux versions and tested hardware combinations.
- [ ] Establish measurable acceptance criteria before describing any feature as production-ready.

## Contributing

Contributions, bug reports, and improvement suggestions are welcome.

1. Fork the repository.
2. Create a focused branch: `git checkout -b feature/your-improvement`.
3. Make the change and add or update tests.
4. Run `python -m pytest -v`.
5. Open a pull request describing the problem, solution, tests, and any hardware required.

Please avoid committing generated evidence, personal data, model weights, credentials, or large temporary files.

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for the full license text.

Copyright (c) 2026 **Kranthi kumar yaralagadda**.
