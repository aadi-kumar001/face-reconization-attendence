# Face Recognition Attendance System — Advanced Edition

A rebuilt, production-shaped version of the original 5-feature concept
(OpenCV + face_recognition + CSV logging + live feed + admin dashboard),
with the gaps in that design closed and several capabilities added that
aren't in typical beginner builds of this project.

## What's new vs. the original design

| Area | Original | This build |
|---|---|---|
| Embeddings | Single dlib model implied | Pluggable: **ArcFace via InsightFace** (512-d, high accuracy) with automatic fallback to `face_recognition` |
| Matching at scale | Implicit linear scan per frame | **FAISS** nearest-neighbour index (NumPy cosine fallback if FAISS isn't installed) + similarity-margin check to reject ambiguous matches |
| Spoofing | None mentioned — a printed photo marks attendance | **Liveness detection**: blink (Eye-Aspect-Ratio), texture (Laplacian variance), and moire/screen-replay detection (2D FFT), fused by majority vote |
| Storage | CSV/Excel logging | **SQLite via SQLAlchemy** — proper schema, unique constraint prevents double-marking, CSV/Excel kept only as an *export* format |
| Performance | Single-threaded implied | Threaded camera capture decoupled from inference, frame-skip tuning, FPS counter |
| Identity across frames | None | Lightweight centroid **tracker** so liveness state (blinks) accumulates per face over time |
| Dashboard | "Admin dashboard" bullet, unspecified | Flask dashboard with **live MJPEG feed**, Chart.js analytics (daily trend, department breakdown), CSV export |
| API | None | REST API for enrollment, attendance queries, and a non-webcam "mark from image" endpoint |
| Auth | None | JWT-based admin login (no more open access to attendance data) |
| Notifications | None | Optional email / Telegram push on each attendance mark |
| Audit trail | None | Every mark, spoof-block, and low-confidence match is logged to an `audit_events` table |
| Deployment | None | Dockerfile + docker-compose |
| Tests | None | Unit tests for liveness math, tracker identity persistence, and the match index |

## Architecture

```
app.py                  Flask app factory, video feed, page routes
config.py                All tunables in one place
core/
  face_engine.py          Detection + embeddings (InsightFace/face_recognition) + FAISS index
  liveness.py              Blink / texture / moire anti-spoofing
  tracker.py               Centroid tracker (per-face identity across frames)
  attendance_service.py    Orchestrates detect -> liveness -> match -> mark -> notify
  camera_stream.py         Threaded capture + MJPEG streaming
  database.py              SQLAlchemy models (Employee, FaceEmbedding, AttendanceLog, AuditEvent)
  analytics.py             Daily/weekly summaries, department breakdown, CSV export
  notifier.py              Email / Telegram notifications
api/routes.py             REST API (auth, employees, enrollment, attendance, export)
utils/
  auth.py                  JWT issue/verify, login_required decorator
  logger.py                Rotating file + console logging
dashboard/                 Templates + CSS/JS for the admin UI
tests/                     Unit tests (liveness math, tracker, match index)
scripts/create_admin.py    Generates the admin password hash for .env
```

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Pick ONE face backend if you didn't install both:
#   pip install insightface onnxruntime      (recommended)
#   pip install face_recognition dlib        (fallback, needs cmake)

cp .env.example .env
python scripts/create_admin.py     # paste the printed FRAS_ADMIN_HASH into .env

python app.py                      # http://localhost:5000
```

First run creates `instance/attendance.db` and the enrollment/export/log
folders automatically.

### Enroll an employee (REST)

```bash
curl -X POST http://localhost:5000/api/employees \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"employee_code": "E001", "full_name": "Jane Doe", "department": "Engineering"}'

curl -X POST http://localhost:5000/api/employees/1/enroll \
  -H "Authorization: Bearer <token>" -H "Content-Type: application/json" \
  -d '{"images": ["<base64 jpg 1>", "<base64 jpg 2>", "<base64 jpg 3>"]}'
```

Enrolling 3–5 images per person (different angles/lighting) is strongly
recommended — this is what the multi-embedding schema is for.

## Docker

```bash
docker compose up --build
```

Remove the `devices:` line in `docker-compose.yml` if you're running this
on a server without a physical webcam and only need the REST
"mark from image" endpoint.

## Notes on the liveness check

No single anti-spoofing signal is bulletproof — a determined attacker
with a video replay can beat blink detection alone, and a very smooth
webcam can occasionally trip the texture check. That's why this build
fuses three independent, cheap signals rather than relying on one; treat
it as raising the bar against casual spoofing (printed photo / static
image on a phone), not as a certified biometric anti-spoof system. For
high-security deployments, pair this with a depth camera or a commercial
liveness SDK.

## Testing

`sqlalchemy`, `insightface`, and `faiss` need network access to install,
so in a fully offline sandbox only the dependency-light modules can be
exercised directly:

```bash
pytest tests/ -v
```

covers the liveness math (EAR/texture/moire), the centroid tracker, and
the FAISS/NumPy-fallback match index. `core/database.py`, `core/attendance_service.py`,
`app.py`, and `api/routes.py` are syntax-verified (`py_compile`) but need
the full dependency set installed to run end-to-end.
