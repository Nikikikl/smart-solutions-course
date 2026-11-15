"""Flask application for the Lab 2 high-level job post-office."""

from datetime import timezone
import os
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

from .auth import atom_auth_required, user_auth_required
from .store import JobStore, StateConflict, device_status, iso_utc, utc_now
from .validation import ValidationError, validate_job_request, validate_poll, validate_result


def _environment_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError("%s must be an integer." % name) from exc


def _development_bind():
    bind = os.environ.get("POST_OFFICE_BIND", "127.0.0.1").strip()
    if bind not in {"127.0.0.1", "0.0.0.0"}:
        raise RuntimeError("POST_OFFICE_BIND must be 127.0.0.1 or 0.0.0.0.")
    return bind


def _json_error(status, code, message):
    return jsonify(error={"code": code, "message": message}), status


def create_app(test_config=None, clock=None):
    app = Flask(__name__)
    default_db = Path(__file__).resolve().parent / "post_office.sqlite3"
    app.config.from_mapping(
        DATABASE_PATH=os.environ.get("POST_OFFICE_DB", str(default_db)),
        ATOM_API_KEY=os.environ.get("ATOM_API_KEY"),
        USER_USERNAME=os.environ.get("POST_OFFICE_USER", "lab-user"),
        USER_PASSWORD=os.environ.get("POST_OFFICE_PASSWORD"),
        DEFAULT_TTL_SECONDS=_environment_int("JOB_TTL_SECONDS", 60),
        MAX_TTL_SECONDS=_environment_int("JOB_MAX_TTL_SECONDS", 3600),
        ATOM_STALE_SECONDS=_environment_int("ATOM_STALE_SECONDS", 10),
        ATOM_OFFLINE_SECONDS=_environment_int("ATOM_OFFLINE_SECONDS", 30),
        CLAIM_LEASE_SECONDS=_environment_int("CLAIM_LEASE_SECONDS", 3),
    )
    if test_config:
        app.config.update(test_config)

    if not app.config.get("ATOM_API_KEY"):
        raise RuntimeError("ATOM_API_KEY is required; no insecure fallback key is provided.")
    if not app.config.get("USER_PASSWORD"):
        raise RuntimeError("POST_OFFICE_PASSWORD is required; no insecure fallback password is provided.")
    if app.config["ATOM_STALE_SECONDS"] >= app.config["ATOM_OFFLINE_SECONDS"]:
        raise RuntimeError("ATOM_STALE_SECONDS must be lower than ATOM_OFFLINE_SECONDS.")
    if app.config["DEFAULT_TTL_SECONDS"] > app.config["MAX_TTL_SECONDS"]:
        raise RuntimeError("JOB_TTL_SECONDS must not exceed JOB_MAX_TTL_SECONDS.")

    db_path = Path(app.config["DATABASE_PATH"])
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.extensions["job_store"] = JobStore(db_path, clock=clock or utc_now)
    app.extensions["clock"] = clock or utc_now

    def store():
        return app.extensions["job_store"]

    def now():
        return app.extensions["clock"]().astimezone(timezone.utc)

    def atom_summary():
        return device_status(
            store().get_device(),
            now(),
            app.config["ATOM_STALE_SECONDS"],
            app.config["ATOM_OFFLINE_SECONDS"],
        )

    def parse_json_body():
        if not request.is_json:
            raise ValidationError("json_required", "Content-Type application/json is required.")
        payload = request.get_json(silent=True)
        if payload is None:
            raise ValidationError("invalid_json", "Request body must contain valid JSON.")
        return payload

    def create_validated_job(payload):
        validated = validate_job_request(
            payload,
            app.config["DEFAULT_TTL_SECONDS"],
            app.config["MAX_TTL_SECONDS"],
        )
        return store().create_job(
            validated["job"], validated["arg"], validated["ttl_seconds"]
        )

    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return _json_error(400, error.code, error.message)

    @app.get("/health")
    def health():
        return jsonify(ok=True, service="lab2-post-office")

    @app.get("/")
    @user_auth_required
    def index():
        return render_template(
            "index.html",
            jobs=store().list_jobs(),
            atom=atom_summary(),
            default_ttl=app.config["DEFAULT_TTL_SECONDS"],
            error=request.args.get("error"),
        )

    @app.post("/jobs")
    @user_auth_required
    def create_job_form():
        try:
            ttl = int(request.form.get("ttl_seconds", ""))
        except ValueError:
            return redirect(url_for("index", error="TTL must be an integer."))
        try:
            job_type = request.form.get("job", "letter")
            if job_type == "display_image":
                # Inactive legacy fields may be present when JavaScript is disabled.
                if set(request.form) - {"job", "image_id", "letter", "routine", "ttl_seconds"}:
                    raise ValidationError("unexpected_field", "request contains unsupported form fields.")
                if len(request.form.getlist("image_id")) != 1:
                    raise ValidationError(
                        "invalid_image", "display_image image_id must be 'lab2_logo' or 'lab2_check'.",
                    )
                argument = {"image_id": request.form.get("image_id", "")}
            elif job_type == "letter":
                argument = {"letter": request.form.get("letter", "")}
            else:
                argument = {"routine": request.form.get("routine", "")}
            create_validated_job(
                {"job": job_type, "arg": argument, "ttl_seconds": ttl}
            )
        except ValidationError as error:
            return redirect(url_for("index", error=error.message))
        return redirect(url_for("index"))

    @app.route("/api/jobs", methods=["GET", "POST"])
    @user_auth_required
    def jobs_api():
        if request.method == "GET":
            return jsonify(jobs=store().list_jobs(), atom=atom_summary())
        job = create_validated_job(parse_json_body())
        return jsonify(job), 201

    @app.get("/api/jobs/<job_id>")
    @user_auth_required
    def job_api(job_id):
        job = store().get_job(job_id)
        if job is None:
            return _json_error(404, "job_not_found", "Job was not found.")
        return jsonify(job)

    @app.get("/api/status")
    @user_auth_required
    def status_api():
        return jsonify(atom=atom_summary(), server_time=iso_utc(now()))

    @app.post("/api/atom/poll")
    @atom_auth_required
    def atom_poll():
        poll = validate_poll(parse_json_body())
        store().update_heartbeat(poll)
        job = store().claim_next(lease_seconds=app.config["CLAIM_LEASE_SECONDS"])
        return jsonify(job=job, server_time=iso_utc(now()))

    @app.get("/api/atom/jobs/<job_id>")
    @atom_auth_required
    def atom_job(job_id):
        job = store().get_job(job_id)
        if job is None:
            return _json_error(404, "job_not_found", "Job was not found.")
        return jsonify(job)

    @app.post("/api/atom/result")
    @atom_auth_required
    def atom_result():
        result = validate_result(parse_json_body())
        try:
            job, duplicate = store().record_result(
                result["id"], result["status"], result["result"], result["reason"]
            )
        except KeyError:
            return _json_error(404, "job_not_found", "Job was not found.")
        except StateConflict as error:
            return _json_error(409, "state_conflict", str(error))
        return jsonify(job=job, duplicate=duplicate)

    return app


def main():
    app = create_app()
    app.run(host=_development_bind(), port=5001)


if __name__ == "__main__":
    main()
