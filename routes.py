"""
REST API. Not present at all in the original design, which only implies a
GUI dashboard — this lets the system integrate with an existing HR/ERP
tool, a mobile app, or a kiosk that isn't running the Flask templates.
"""
from __future__ import annotations

import base64
import datetime as dt
import io
import os

import numpy as np
from flask import Blueprint, request, jsonify, send_file, current_app

from config import Config
from core import analytics
from core.database import get_session, Employee, FaceEmbedding, AttendanceLog
from utils.auth import login_required, verify_password, issue_token
from utils.logger import get_logger

log = get_logger(__name__)
api_bp = Blueprint("api", __name__, url_prefix="/api")


# ---------------------------------------------------------------- auth ----
@api_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    password = data.get("password", "")

    if username != Config.ADMIN_USERNAME or not Config.ADMIN_PASSWORD_HASH:
        return jsonify({"error": "Invalid credentials"}), 401
    if not verify_password(password, Config.ADMIN_PASSWORD_HASH):
        return jsonify({"error": "Invalid credentials"}), 401

    token = issue_token(username)
    resp = jsonify({"token": token})
    resp.set_cookie("fras_token", token, httponly=True, samesite="Lax")
    return resp


# ------------------------------------------------------------ employees ---
@api_bp.route("/employees", methods=["GET"])
@login_required
def list_employees():
    session = get_session()
    try:
        rows = session.query(Employee).all()
        return jsonify([{
            "id": e.id, "employee_code": e.employee_code, "full_name": e.full_name,
            "department": e.department, "active": e.active,
            "enrolled_faces": len(e.embeddings),
        } for e in rows])
    finally:
        session.close()


@api_bp.route("/employees", methods=["POST"])
@login_required
def create_employee():
    data = request.get_json(force=True)
    required = {"employee_code", "full_name"}
    if not required.issubset(data):
        return jsonify({"error": f"Missing fields: {required - set(data)}"}), 400

    session = get_session()
    try:
        if session.query(Employee).filter_by(employee_code=data["employee_code"]).first():
            return jsonify({"error": "employee_code already exists"}), 409
        emp = Employee(
            employee_code=data["employee_code"],
            full_name=data["full_name"],
            department=data.get("department"),
            email=data.get("email"),
            phone=data.get("phone"),
        )
        session.add(emp)
        session.commit()
        return jsonify({"id": emp.id}), 201
    finally:
        session.close()


@api_bp.route("/employees/<int:employee_id>/enroll", methods=["POST"])
@login_required
def enroll_face(employee_id: int):
    """
    Accepts one or more base64 JPEG/PNG images (`images`: [str, ...]) and
    stores an embedding for each — multi-shot enrollment materially
    improves match recall vs. the original's implied single-photo design.
    """
    import cv2

    data = request.get_json(force=True)
    images_b64 = data.get("images", [])
    if not images_b64:
        return jsonify({"error": "No images provided"}), 400

    engine = current_app.config["ATTENDANCE_SERVICE"].engine
    session = get_session()
    try:
        emp = session.get(Employee, employee_id)
        if not emp:
            return jsonify({"error": "Employee not found"}), 404

        os.makedirs(Config.ENROLL_IMAGES_DIR, exist_ok=True)
        saved = 0
        for i, b64 in enumerate(images_b64):
            try:
                raw = base64.b64decode(b64.split(",")[-1])
                arr = np.frombuffer(raw, dtype=np.uint8)
                frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                if frame is None:
                    continue
                faces = engine.detect(frame)
                if not faces:
                    continue
                # Largest face in the enrollment photo is assumed to be the subject.
                faces.sort(key=lambda f: (f.box[2]-f.box[0])*(f.box[3]-f.box[1]), reverse=True)
                best = faces[0]

                img_path = os.path.join(
                    Config.ENROLL_IMAGES_DIR, f"{emp.employee_code}_{i}.jpg"
                )
                cv2.imwrite(img_path, frame)

                session.add(FaceEmbedding(
                    employee_id=emp.id,
                    vector=FaceEmbedding.pack_vector(best.embedding),
                    dim=len(best.embedding),
                    source_image_path=img_path,
                ))
                saved += 1
            except Exception:
                log.exception("Failed to process enrollment image %d", i)

        session.commit()
        current_app.config["ATTENDANCE_SERVICE"].reload_index()
        return jsonify({"embeddings_saved": saved})
    finally:
        session.close()


# ------------------------------------------------------------ attendance --
@api_bp.route("/attendance/today", methods=["GET"])
@login_required
def attendance_today():
    return jsonify(analytics.daily_summary(dt.date.today()))


@api_bp.route("/attendance/trend", methods=["GET"])
@login_required
def attendance_trend():
    days = int(request.args.get("days", 7))
    return jsonify(analytics.weekly_trend(dt.date.today(), days=days))


@api_bp.route("/attendance/departments", methods=["GET"])
@login_required
def attendance_departments():
    day_str = request.args.get("date")
    day = dt.date.fromisoformat(day_str) if day_str else dt.date.today()
    return jsonify(analytics.department_breakdown(day))


@api_bp.route("/attendance/export", methods=["GET"])
@login_required
def attendance_export():
    day_str = request.args.get("date")
    day = dt.date.fromisoformat(day_str) if day_str else dt.date.today()
    csv_bytes = analytics.export_csv_bytes(day)
    return send_file(
        io.BytesIO(csv_bytes),
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"attendance_{day.isoformat()}.csv",
    )


@api_bp.route("/attendance/mark", methods=["POST"])
def mark_from_image():
    """
    Non-webcam integration path: POST a single base64 image, get back the
    recognition + attendance result. Useful for a turnstile camera or a
    mobile enrollment kiosk that isn't using the live MJPEG stream.
    """
    import cv2

    data = request.get_json(force=True)
    b64 = data.get("image")
    if not b64:
        return jsonify({"error": "No image provided"}), 400

    raw = base64.b64decode(b64.split(",")[-1])
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return jsonify({"error": "Could not decode image"}), 400

    service = current_app.config["ATTENDANCE_SERVICE"]
    results = service.process_frame(frame)
    return jsonify([{
        "employee_id": r.employee_id,
        "employee_name": r.employee_name,
        "confidence": r.confidence,
        "liveness_passed": r.liveness_passed,
        "just_marked": r.just_marked,
    } for r in results])


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": dt.datetime.utcnow().isoformat()})
