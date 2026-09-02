# Windows 11 quick setup

## Prerequisites
1. Install Python 3.12.x 64-bit and tick **Add Python to PATH**.
2. Install the Microsoft Visual C++ Redistributable / Build Tools if a native Python package asks for it.
3. A working webcam is required for live attendance and enrollment.

## First run
Double-click `setup_windows.bat`.

The script creates `venv`, installs `requirements.txt`, and copies `.env.example` to `.env`.
When prompted, create an admin password of at least 8 characters. Put the printed `FRAS_ADMIN_HASH=...` line into `.env`.

Then double-click `start_windows.bat`.

Open: http://127.0.0.1:5000/login
Default username: `admin` (unless you change `FRAS_ADMIN_USER` in `.env`).

## Enrollment
After login, click **Enroll Person**. Allow browser camera access and capture at least 3 face samples. The app stores multiple embeddings and rebuilds its recognition index.

## Data location
All local data is stored under `instance/`:
- `attendance.db` — SQLite database
- `enrolled_faces/` — enrollment photos
- `exports/` — generated exports
- `logs/` — application logs

## Notes
- The first InsightFace startup can download its model files and therefore needs internet access.
- Recognition/liveness is not a certified biometric security system; use it as an attendance aid and test it with your actual camera and lighting.
- Never commit `.env`, the database, or enrolled face images to GitHub.
