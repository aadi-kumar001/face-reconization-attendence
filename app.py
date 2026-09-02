"""
Application entrypoint. `python app.py` starts the dashboard + live video
feed + REST API together.
"""
from __future__ import annotations

import datetime as dt

from flask import Flask, render_template, Response, jsonify, redirect, request

from config import Config
from core.database import init_db
from core.attendance_service import AttendanceService
from core.camera_stream import CameraStream
from core import analytics
from api.routes import api_bp
from utils.logger import get_logger

log = get_logger(__name__)


def create_app() -> Flask:
    Config.ensure_dirs()
    init_db()

    app = Flask(__name__, template_folder="dashboard/templates", static_folder="dashboard/static")
    app.config.from_object(Config)

    # Built once, shared by both the video loop and the REST enroll endpoint
    # so there is exactly one FAISS index / model in memory, not two.
    service = AttendanceService()
    stream = CameraStream(service=service)
    app.config["ATTENDANCE_SERVICE"] = service
    app.config["CAMERA_STREAM"] = stream

    app.register_blueprint(api_bp)

    @app.route("/")
    def index():
        if not request.cookies.get("fras_token"):
            return redirect("/login")
        return render_template("dashboard.html")

    @app.route("/enroll")
    def enroll_page():
        if not request.cookies.get("fras_token"):
            return redirect("/login")
        return render_template("enroll.html")

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/video_feed")
    def video_feed():
        cam = app.config["CAMERA_STREAM"]
        if not cam._running:
            try:
                cam.start()
            except RuntimeError as exc:
                log.error("Camera start failed: %s", exc)
                return jsonify({"error": str(exc)}), 500
        return Response(cam.mjpeg_generator(), mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/api/live_results")
    def live_results():
        cam = app.config["CAMERA_STREAM"]
        results = cam.get_latest_results()
        return jsonify([{
            "employee_name": r.employee_name,
            "confidence": r.confidence,
            "liveness_passed": r.liveness_passed,
            "just_marked": r.just_marked,
        } for r in results])

    @app.teardown_appcontext
    def _shutdown_camera(exception=None):
        # Only stop on actual interpreter shutdown, handled in __main__ below;
        # per-request teardown intentionally leaves the stream running.
        pass

    return app


app = create_app()

if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG, threaded=True, use_reloader=False)
    finally:
        app.config["CAMERA_STREAM"].stop()
