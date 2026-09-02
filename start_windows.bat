@echo off
setlocal
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
  echo Virtual environment not found. Run setup_windows.bat first.
  pause
  exit /b 1
)
call venv\Scripts\activate.bat
start "Face Attendance Browser" cmd /c "timeout /t 3 /nobreak >nul & start http://127.0.0.1:5000/login"
python app.py
pause
