# Visioner-Control-SDLA

**AI Driving Coach + Smart Traffic Enforcement | Built for Indian Roads**

An ADAS-powered Self-Driving Lesson Assistant and Driver Behaviour System that provides real-time coaching, skill classification, lane correction, and safety alerts — all from a Raspberry Pi or any Linux machine with a webcam.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Optional Dependencies](#optional-dependencies)
- [Running Tests](#running-tests)
- [Docker](#docker)
- [Bug Fixes & Improvements (v1.1.0)](#bug-fixes--improvements-v110)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Features

| Module | What it does |
|---|---|
| **Driver Monitoring** | Eye-aspect-ratio drowsiness detection via webcam + dlib |
| **OBD Telemetry** | Real-time speed, gear, and braking data; simulator fallback when no adapter is present |
| **ADAS – Speed Control** | Per-skill-level speed limits with console and API warnings |
| **ADAS – Gear Advisor** | Gear-shift suggestions based on current speed |
| **ADAS – Auto Lane Correction** | Detects lane offset and computes a steering correction |
| **Skill Classifier** | Rule-based Beginner / Medium / Pro classification (ML model optional) |
| **Voice Coach** | Text-to-speech driving tips; graceful fallback to logging on headless systems |
| **Lesson Tracker** | Per-session mistake counting and duration tracking |
| **Web Dashboard** | Flask UI with live-polling telemetry, skill badge, tips, and progress table |

---

## Architecture

```
run.py                        # Entry point: web or simulator mode
│
├── app/
│   ├── __init__.py           # Flask application factory
│   ├── routes.py             # Web routes + JSON API
│   ├── main.py               # Simulator loop (CLI mode)
│   ├── adas/
│   │   ├── auto_correction.py  # Lane-deviation detection & correction
│   │   ├── gear_alert.py       # Gear-shift advisor
│   │   └── speed_control.py    # Speed-limit enforcer per skill level
│   ├── behavior/
│   │   ├── classifier.py       # Beginner / Medium / Pro rule classifier
│   │   ├── lesson_tracker.py   # Session duration & mistake counter
│   │   └── voice_coach.py      # Text coaching tips
│   ├── telemetry/
│   │   ├── obd_interface.py    # OBD-II serial adapter (mock-ready)
│   │   └── simulator_interface.py  # Random telemetry for offline dev
│   ├── hardware/
│   │   ├── pi_camera.py        # OpenCV camera wrapper
│   │   └── android_auto.py     # Android Auto stub
│   └── utils/
│       ├── config.py           # Centralised speed/gear thresholds
│       └── logger.py           # Structured logging setup
│
├── modules/                  # Standalone reusable helpers
│   ├── coaching.py           # TTS-backed voice coach
│   ├── driver_skill.py       # TensorFlow ML classifier (optional)
│   ├── progress_tracker.py   # JSON-file lesson persistence
│   ├── safety_parking.py     # Steering correction + parking sensor logic
│   └── speed_gear.py         # Speed-limit & gear-shift utilities
│
├── scripts/                  # Runnable entry points
│   ├── main.py               # Full pipeline: camera → monitor → coach → score
│   ├── driver_monitor.py     # dlib eye-tracking & drowsiness detection
│   ├── coaching_engine.py    # TTS coaching rules
│   ├── obd_simulator.py      # Fake OBD readings for development
│   ├── skill_scorer.py       # Session score tracker (class-based)
│   └── start_simulation.py   # Shortcut to simulator mode
│
├── model/
│   └── train_model.py        # TensorFlow model trainer (outputs model/driver_skill_model.h5)
│
├── static/
│   ├── templates/dashboard.html
│   ├── css/style.css
│   └── js/main.js            # Live-polling dashboard updater
│
└── tests/
    ├── test_adas.py
    └── test_behavior.py
```

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/your-org/Visioner-Control-SDLA.git
cd Visioner-Control-SDLA
python -m pip install -r requirements.txt
```

### 2. Run the web dashboard

```bash
python run.py
# Open http://localhost:5000
```

Add `--debug` to enable Flask's reloader during development:

```bash
python run.py web --debug
```

### 3. Run in simulator mode (CLI, no browser)

```bash
python run.py simulator
```

### 4. Run the full camera pipeline

```bash
# Install hardware deps first
pip install ".[hardware]"

# Download the dlib landmark predictor
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2

# Run (set env var if the .dat file is not in the project root)
DLIB_PREDICTOR_PATH=/path/to/shape_predictor_68_face_landmarks.dat \
  python -m scripts.main
```

---

## Configuration

All tunable thresholds live in `app/utils/config.py`:

```python
CONFIG = {
    "mode":                   "simulator",  # "simulator" | "obd"
    "max_speed_beg":          40,           # km/h ceiling for Beginner
    "max_speed_med":          60,           # km/h ceiling for Medium
    "max_speed_pro":          80,           # km/h ceiling for Pro
    "min_gear_change_speed":  20,           # km/h threshold for downshift warning
}
```

Change any value here and all ADAS modules pick it up automatically — no other files need editing.

---

## API Reference

| Endpoint | Method | Response |
|---|---|---|
| `/` | GET | HTML dashboard (server-rendered) |
| `/api/telemetry` | GET | `{ telemetry, skill, tip, progress }` |
| `/api/health` | GET | `{ status: "ok" }` |

### `/api/telemetry` example response

```json
{
  "telemetry": {
    "speed": 47.0,
    "gear": 3,
    "brake_events": 1,
    "lane_offset": -0.12,
    "steering_angle": 4.5
  },
  "skill": "Medium",
  "tip": "Watch your mirrors and maintain a steady pace.",
  "progress": {
    "Duration (min)": 5,
    "Mistakes": 2,
    "Progress": "In Progress"
  }
}
```

---

## Optional Dependencies

```bash
# TensorFlow ML model (training + inference)
pip install ".[ml]"

# Hardware support (camera drowsiness detection + TTS voice coach)
pip install ".[hardware]"

# All optional extras
pip install ".[ml,hardware]"
```

---

## Running Tests

```bash
pytest -v
```

All tests are self-contained and require only the base `requirements.txt` — no camera, TTS engine, or TensorFlow needed.

---

## Docker

```bash
docker compose up --build
# Open http://localhost:5000
```

---

## Bug Fixes & Improvements (v1.1.0)

The following issues were identified and resolved in this release.

### Bug Fixes

**1. `scripts/main.py` — broken imports when run from project root**
Bare `from driver_monitor import ...` only worked if the working directory was `scripts/`. Fixed by inserting the project root into `sys.path` at startup and switching to `from scripts.X import ...`, so the script runs correctly as `python -m scripts.main` from anywhere.

**2. `scripts/skill_scorer.py` — mutable global leaked state between sessions**
`score = 100` at module level meant the score never reset across test runs or multiple sessions. Replaced with a `SkillScorer` class that stores state on the instance and exposes an explicit `reset()` method.

**3. `scripts/driver_monitor.py` — module import crashed if `.dat` file was missing**
`dlib.shape_predictor(path)` was called at the top level, so any `import driver_monitor` raised `FileNotFoundError` before any code ran. Moved to a lazy `_load_models()` helper, added a `DLIB_PREDICTOR_PATH` environment-variable override, and replaced the generic error with a descriptive message pointing to the download URL.

**4. `app/behavior/classifier.py` — incorrect Pro/Medium boundary**
A driver at 70 km/h with 5 harsh brake events was classified as "Pro" because the Pro check only tested speed. Fixed to also require `brake_events <= 1`, so aggressive brakers at speed are correctly kept at Medium.

**5. `app/adas/auto_correction.py` — Left/Right labels were swapped**
A positive `lane_offset` (drifting right) printed "Left deviation", and vice-versa. Corrected the direction mapping: `lane_offset > 0` → "Right deviation", `lane_offset < 0` → "Left deviation".

**6. `app/__init__.py` — fragile relative `template_folder` path**
`template_folder="../static/templates"` resolved correctly only when the process was started from the project root. Replaced with an `os.path.abspath`-based path so the app works regardless of current working directory.

**7. `app/routes.py` — module-level singletons caused double-counting and test pollution**
`TelemetrySimulator`, `DriverClassifier`, `LessonTracker`, and `VoiceCoach` were instantiated at import time, meaning their state (especially `LessonTracker`) accumulated across every request and persisted between test cases. Moved inside `register_routes()` so they are scoped to the application instance. The `/api/telemetry` endpoint no longer calls `tracker.update()` to avoid counting the same loop twice when the JS dashboard polls alongside normal page loads.

**8. `modules/progress_tracker.py` — `os.makedirs` crashed on a plain filename**
When `filepath="progress.json"` (no directory component), `os.path.dirname` returns `""` and `os.makedirs("")` raises `FileNotFoundError`. Added a guard: `if dir_name: os.makedirs(dir_name, exist_ok=True)`.

**9. `app/hardware/pi_camera.py` — camera open failure was silently ignored**
`cv2.VideoCapture(index)` never raises an exception; you must call `.isOpened()` to detect failure. Added the check in `__init__` with a descriptive `CameraError`. Also added context-manager (`__enter__`/`__exit__`) support for safe resource cleanup.

**10. `app/telemetry/obd_interface.py` — bare `Exception` on connection error**
A bare `raise Exception("OBD not connected.")` is uncatchable by type. Replaced with a typed `OBDConnectionError(RuntimeError)` so callers can catch it specifically without swallowing other errors.

**11. `modules/coaching.py` — `pyttsx3.init()` in `__init__` crashed headless servers**
Constructing the TTS engine eagerly in `__init__` meant instantiating `VoiceCoach` on any machine without audio hardware (CI, Docker, Raspberry Pi Lite) raised an exception. TTS initialisation is now lazy and wrapped in `try/except`, falling back to `logging.info` when unavailable.

**12. `model/train_model.py` vs `modules/driver_skill.py` — model path mismatch**
The trainer saved to `model/driver_skill_model.h5` but the classifier tried to load from `models/skill_classifier.h5` (different directory name, different filename). Unified to `model/driver_skill_model.h5` and added a `DEFAULT_MODEL_PATH` constant shared between both files.

**13. `run.py` — `debug=True` hardcoded in the production entrypoint**
Flask's debug mode enables the interactive debugger and auto-reloader, both of which are security risks in production. Moved to an explicit `--debug` flag: `python run.py web --debug`.

**14. `static/js/main.js` — live polling only updated the skill badge**
The `fetch("/api/telemetry")` loop refreshed the skill badge but never updated the driving tip or the progress table, leaving them stale after the initial page load. Fixed to update all three sections. Added minimal HTML escaping on server-returned strings to prevent XSS.

**15. `app/utils/config.py` — missing `max_speed_med` key**
`SpeedController` had a magic hardcoded `60` for the Medium skill ceiling. Extracted to `CONFIG["max_speed_med"]` for consistency with the other thresholds.

**16. `scripts/main.py` — no camera cleanup on error**
`cap.release()` and `cv2.destroyAllWindows()` were only called on clean exit. A crash mid-loop left the camera handle open. Wrapped the main loop in `try/finally` to guarantee cleanup.

### General Improvements

- **Type annotations** added throughout (`-> str | None`, `-> dict`, etc.) for IDE support and early error detection.
- **Docstrings** added or expanded on every public class and method.
- **Named constants** (`DEVIATION_THRESHOLD`, `CORRECTION_GAIN`, `EAR_THRESHOLD`, etc.) replace magic numbers.
- **`app/utils/logger.py`** format string updated to include the logger name, making multi-module log output easier to trace.
- **`modules/driver_skill.py`** model loading is now lazy (deferred to first `predict_skill()` call) so the rest of the app starts even when TensorFlow is not installed.
- **`modules/safety_parking.py`** `parking_logic` now handles a missing `distance` key gracefully instead of returning a misleading "Parking clear" message.
- **`modules/speed_gear.py`** `check_speed_limit` warning message now includes the current speed alongside the limit for clearer feedback.
- **`scripts/start_simulation.py`** emoji removed from `print()` to avoid encoding errors on Windows terminals and some SSH sessions.
- **Tests expanded** — added cases for unknown skill level in `SpeedController`, Medium classification with high brake events, missing telemetry keys in `DriverClassifier`, and "In Progress" vs "Completed" progress states.

---

## Roadmap

- [ ] Real OBD-II integration via `pyOBD` / ELM327 adapter
- [ ] GPS-based speed-limit lookup for Indian road zones
- [ ] Persistent session history with SQLite
- [ ] Mobile-responsive dashboard with Chart.js telemetry graphs
- [ ] Multi-driver profile support
- [ ] WebSocket push (replace polling with `flask-socketio`)

---

## Contributing

1. Fork this repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Make your changes with tests: `pytest -v`
4. Open a Pull Request with a clear description

Please keep PRs focused — one fix or feature per PR.

---

## License

MIT — see [LICENSE](LICENSE) for full terms.
