import pytest

from server.app import create_app


def claim(client, atom_headers, valid_poll):
    return client.post("/api/atom/poll", headers=atom_headers, json=valid_poll)


def test_valid_letter_job_creation_normalizes_letter(create_letter):
    response = create_letter("a")
    assert response.status_code == 201
    job = response.get_json()
    assert job["job"] == "letter"
    assert job["arg"] == {"letter": "A"}
    assert job["status"] == "queued"
    assert job["created_at"].endswith("Z")
    assert job["expires_at"].endswith("Z")


def test_invalid_job_type_is_rejected(client, user_headers):
    response = client.post(
        "/api/jobs",
        headers=user_headers,
        json={"job": "move_robot", "arg": {}, "ttl_seconds": 60},
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "unknown_job"


def test_valid_pick_place_job_creation(create_pick_place):
    response = create_pick_place()
    assert response.status_code == 201
    assert response.get_json()["arg"] == {"routine": "source_to_finished"}


def display_request(image_id="lab2_logo", **changes):
    payload = {"job": "display_image", "arg": {"image_id": image_id}, "ttl_seconds": 60}
    payload.update(changes)
    return payload


@pytest.mark.parametrize("image_id", ["lab2_logo", "lab2_check"])
def test_display_image_roundtrip_and_atom_poll(app, client, clock, user_headers, atom_headers, valid_poll, image_id):
    response = client.post("/api/jobs", headers=user_headers, json=display_request(image_id))
    assert response.status_code == 201
    created = response.get_json()
    assert created["job"] == "display_image" and created["arg"] == {"image_id": image_id}
    assert created["status"] == "queued"
    # Reopen the existing schema without migrations or a new queue.
    restarted = create_app(dict(app.config), clock=clock).test_client()
    assert restarted.get("/api/jobs/" + created["id"], headers=user_headers).get_json() == created
    assert restarted.get("/api/jobs", headers=user_headers).get_json()["jobs"] == [created]
    polled = claim(restarted, atom_headers, valid_poll).get_json()["job"]
    assert polled["id"] == created["id"] and polled["status"] == "claimed"
    assert polled["job"] == "display_image" and polled["arg"] == {"image_id": image_id}
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None


@pytest.mark.parametrize("image_id", [
    None, "", "unknown", "LAB2_LOGO", " lab2_logo", "lab2_logo ",
    "https://example.invalid/image.jpg", "http://127.0.0.1/image.jpg",
    "../lab2_logo", "/tmp/lab2_logo", "C:\\image.jpg", "file:///tmp/image.jpg",
    "lab2_logo\x00extra", "<script>alert(1)</script>", 1, True, [], {},
])
def test_display_image_rejects_any_non_whitelisted_id(client, user_headers, image_id):
    response = client.post("/api/jobs", headers=user_headers, json=display_request(image_id))
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_image"
    assert client.get("/api/jobs", headers=user_headers).get_json()["jobs"] == []


@pytest.mark.parametrize("argument", [{}, None, [], "lab2_logo"])
def test_display_image_requires_image_id_object(client, user_headers, argument):
    response = client.post("/api/jobs", headers=user_headers, json=display_request(arg=argument))
    assert response.status_code == 400
    assert client.get("/api/jobs", headers=user_headers).get_json()["jobs"] == []


@pytest.mark.parametrize("field,value", [
    ("url", "https://example.invalid/image.jpg"), ("path", "/tmp/image.jpg"),
    ("x", 1), ("y", 2), ("z", 3), ("r", 4), ("speed", 20), ("DO", 1),
    ("do", 1), ("pump", "suck"), ("script", "run"), ("trajectory", []), ("repetitions", 2),
])
def test_display_image_rejects_extra_arguments_and_commands(client, user_headers, field, value):
    payload = display_request()
    payload["arg"][field] = value
    response = client.post("/api/jobs", headers=user_headers, json=payload)
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "unexpected_field"
    assert client.get("/api/jobs", headers=user_headers).get_json()["jobs"] == []


@pytest.mark.parametrize("ttl", [0, 3601, True, 1.5, "60", None])
def test_display_image_uses_existing_ttl_validation(client, user_headers, ttl):
    response = client.post("/api/jobs", headers=user_headers, json=display_request(ttl_seconds=ttl))
    assert response.status_code == 400 and response.get_json()["error"]["code"] == "invalid_ttl"


def test_expired_display_image_is_not_delivered(client, clock, user_headers, atom_headers, valid_poll):
    created = client.post("/api/jobs", headers=user_headers, json=display_request(ttl_seconds=1)).get_json()
    clock.advance(2)
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None
    saved = client.get("/api/jobs/" + created["id"], headers=user_headers).get_json()
    assert saved["status"] == "expired" and saved["reason"] == "ttl_expired"
    assert saved["arg"] == {"image_id": "lab2_logo"}


def test_display_image_is_claimed_by_only_one_concurrent_atom(app, client, user_headers, atom_headers, valid_poll):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    created = client.post("/api/jobs", headers=user_headers, json=display_request()).get_json()
    ready = Barrier(2)

    def poll(device):
        ready.wait(timeout=5)
        response = app.test_client().post("/api/atom/poll", headers=atom_headers,
                                         json={**valid_poll, "device_id": device})
        assert response.status_code == 200
        return response.get_json()["job"]

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(poll, ("synthetic-atom-1", "synthetic-atom-2")))
    jobs = [job for job in results if job is not None]
    assert len(jobs) == 1 and jobs[0]["id"] == created["id"]
    assert results.count(None) == 1


def test_display_image_keeps_user_and_atom_authentication(client, user_headers, atom_headers, valid_poll):
    assert client.post("/api/jobs", json=display_request()).status_code == 401
    assert client.post("/jobs", data={"job": "display_image", "image_id": "lab2_logo", "ttl_seconds": "60"}).status_code == 401
    created = client.post("/api/jobs", headers=user_headers, json=display_request()).get_json()
    assert claim(client, {}, valid_poll).status_code == 401
    assert claim(client, {"Authorization": "Bearer wrong"}, valid_poll).status_code == 403
    assert claim(client, atom_headers, valid_poll).get_json()["job"]["id"] == created["id"]


def test_display_image_server_path_has_no_hardware_or_network_side_effects(client, user_headers, atom_headers, valid_poll, monkeypatch):
    import socket
    from unittest import mock
    import requests
    import serial
    import cv2

    denied = mock.Mock(side_effect=AssertionError("hardware/network must not be used"))
    monkeypatch.setattr(socket, "create_connection", denied)
    monkeypatch.setattr(requests.Session, "request", denied)
    monkeypatch.setattr(serial, "serial_for_url", denied)
    monkeypatch.setattr(serial, "Serial", denied)
    monkeypatch.setattr(cv2, "VideoCapture", denied)
    created = client.post("/api/jobs", headers=user_headers, json=display_request()).get_json()
    assert claim(client, atom_headers, valid_poll).get_json()["job"]["id"] == created["id"]
    assert client.get("/", headers=user_headers).status_code == 200
    denied.assert_not_called()


@pytest.mark.parametrize("routine", ["", "other", None])
def test_unknown_or_missing_pick_place_routine_is_rejected(create_pick_place, routine):
    response = create_pick_place(routine)
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_routine"


@pytest.mark.parametrize(
    "field,value",
    [
        ("x", 100),
        ("y", 20),
        ("z", -80),
        ("r", 0),
        ("speed", 20),
        ("pump", "on"),
        ("do", 1),
        ("repetitions", 2),
        ("trajectory", [[1, 2, 3]]),
    ],
)
def test_pick_place_direct_control_fields_are_rejected(create_pick_place, field, value):
    response = create_pick_place(extra_arg={field: value})
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "unexpected_field"


def test_invalid_letter_is_rejected(create_letter):
    response = create_letter("AB")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_letter"


def test_expired_job_is_never_delivered(
    create_letter, clock, client, atom_headers, valid_poll, user_headers
):
    created = create_letter("E", ttl_seconds=1).get_json()
    clock.advance(2)
    response = claim(client, atom_headers, valid_poll)
    assert response.status_code == 200
    assert response.get_json()["job"] is None
    stored = client.get("/api/jobs/" + created["id"], headers=user_headers).get_json()
    assert stored["status"] == "expired"
    assert stored["reason"] == "ttl_expired"


def test_expired_pick_place_is_never_delivered(
    create_pick_place, clock, client, atom_headers, valid_poll, user_headers
):
    created = create_pick_place(ttl_seconds=1).get_json()
    clock.advance(2)
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None
    stored = client.get("/api/jobs/" + created["id"], headers=user_headers).get_json()
    assert stored["status"] == "expired"


def test_atom_key_is_required(client, valid_poll):
    response = client.post("/api/atom/poll", json=valid_poll)
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "atom_key_required"


def test_wrong_atom_key_is_rejected(client, valid_poll):
    response = client.post(
        "/api/atom/poll",
        headers={"Authorization": "Bearer wrong-test-key"},
        json=valid_poll,
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "invalid_atom_key"


def test_poll_updates_last_seen(client, atom_headers, valid_poll, user_headers):
    response = claim(client, atom_headers, valid_poll)
    assert response.status_code == 200
    status = client.get("/api/status", headers=user_headers).get_json()["atom"]
    assert status["status"] == "online"
    assert status["last_seen"] == "2030-01-01T12:00:00Z"
    assert status["device"]["poll_interval_ms"] == 1000


def test_queued_job_can_be_claimed(create_letter, client, atom_headers, valid_poll):
    created = create_letter("Q").get_json()
    delivered = claim(client, atom_headers, valid_poll).get_json()["job"]
    assert delivered["id"] == created["id"]
    assert delivered["status"] == "claimed"


def test_claimed_and_completed_job_is_not_delivered_twice(
    create_letter, client, atom_headers, valid_poll
):
    created = create_letter("D").get_json()
    first = claim(client, atom_headers, valid_poll).get_json()["job"]
    assert first["id"] == created["id"]
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None
    result = client.post(
        "/api/atom/result",
        headers=atom_headers,
        json={"id": created["id"], "status": "done", "result": {"simulated": True}},
    )
    assert result.status_code == 200
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None


def test_claim_whose_poll_response_was_lost_is_delivered_again(
    create_letter, client, clock, atom_headers, valid_poll
):
    created = create_letter("R").get_json()
    assert claim(client, atom_headers, valid_poll).get_json()["job"]["id"] == created["id"]
    clock.advance(1)
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None   # lease still running
    clock.advance(3)
    again = claim(client, atom_headers, valid_poll).get_json()["job"]
    assert again["id"] == created["id"] and again["status"] == "claimed"


def test_lost_claim_is_not_delivered_after_its_ttl(
    create_letter, client, clock, atom_headers, valid_poll
):
    created = create_letter("T").get_json()
    claim(client, atom_headers, valid_poll)
    clock.advance(61)
    assert claim(client, atom_headers, valid_poll).get_json()["job"] is None


def test_duplicate_result_reporting_is_idempotent(
    create_letter, client, atom_headers, valid_poll
):
    job = create_letter("I").get_json()
    claim(client, atom_headers, valid_poll)
    payload = {"id": job["id"], "status": "done", "result": {"simulated": True}}
    first = client.post("/api/atom/result", headers=atom_headers, json=payload)
    second = client.post("/api/atom/result", headers=atom_headers, json=payload)
    assert first.get_json()["duplicate"] is False
    assert second.status_code == 200
    assert second.get_json()["duplicate"] is True


def test_conflicting_duplicate_result_is_rejected(
    create_letter, client, atom_headers, valid_poll
):
    job = create_letter("C").get_json()
    claim(client, atom_headers, valid_poll)
    client.post(
        "/api/atom/result",
        headers=atom_headers,
        json={"id": job["id"], "status": "done", "result": {"value": 1}},
    )
    conflict = client.post(
        "/api/atom/result",
        headers=atom_headers,
        json={"id": job["id"], "status": "done", "result": {"value": 2}},
    )
    assert conflict.status_code == 409
    assert conflict.get_json()["error"]["code"] == "state_conflict"


def test_refused_result_is_stored_and_visible(
    create_letter, client, atom_headers, valid_poll, user_headers
):
    job = create_letter("R").get_json()
    claim(client, atom_headers, valid_poll)
    client.post(
        "/api/atom/result",
        headers=atom_headers,
        json={"id": job["id"], "status": "refused", "reason": "mock_station_refused"},
    )
    stored = client.get("/api/jobs/" + job["id"], headers=user_headers).get_json()
    assert stored["status"] == "refused"
    assert stored["reason"] == "mock_station_refused"


def test_completed_result_is_stored_and_visible(
    create_letter, client, atom_headers, valid_poll, user_headers
):
    job = create_letter("S").get_json()
    claim(client, atom_headers, valid_poll)
    client.post(
        "/api/atom/result",
        headers=atom_headers,
        json={"id": job["id"], "status": "done", "result": {"letter": "S"}},
    )
    stored = client.get("/api/jobs/" + job["id"], headers=user_headers).get_json()
    assert stored["status"] == "done"
    assert stored["result"] == {"letter": "S"}


def test_coordinates_and_direct_motion_fields_are_rejected(client, user_headers):
    response = client.post(
        "/api/jobs",
        headers=user_headers,
        json={
            "job": "letter",
            "arg": {"letter": "A", "x": 100, "speed": 50, "pump": "on"},
        },
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "unexpected_field"


def test_online_stale_offline_status_without_sleep(
    client, atom_headers, valid_poll, user_headers, clock
):
    claim(client, atom_headers, valid_poll)
    status = lambda: client.get("/api/status", headers=user_headers).get_json()["atom"][
        "status"
    ]
    assert status() == "online"
    clock.advance(11)
    assert status() == "stale"
    clock.advance(20)
    assert status() == "offline"


def test_post_office_exposes_no_camera_routes(app, client, user_headers):
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    assert not any("camera" in rule or "stream" in rule for rule in rules)
    assert client.get("/api/cameras", headers=user_headers).status_code == 404


def test_user_api_requires_authentication(client):
    response = client.get("/api/jobs")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "user_auth_required"


def test_unknown_job_returns_json_404(client, user_headers):
    response = client.get("/api/jobs/not-a-real-job", headers=user_headers)
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "job_not_found"


def test_user_page_creates_and_lists_letter_job(client, user_headers):
    created = client.post(
        "/jobs",
        headers=user_headers,
        data={"job": "letter", "letter": "B", "ttl_seconds": "60"},
    )
    assert created.status_code == 302
    page = client.get("/", headers=user_headers)
    assert page.status_code == 200
    assert b"queued" in page.data
    assert b"Lab 2 postkontor" in page.data


def test_user_page_creates_predefined_pick_place_job(client, user_headers):
    created = client.post(
        "/jobs",
        headers=user_headers,
        data={
            "job": "pick_place",
            "routine": "source_to_finished",
            "ttl_seconds": "60",
        },
    )
    assert created.status_code == 302
    page = client.get("/", headers=user_headers)
    assert b"pick_place" in page.data
    assert b"source_to_finished" in page.data


def test_startup_refuses_missing_required_secrets(tmp_path, monkeypatch):
    monkeypatch.delenv("ATOM_API_KEY", raising=False)
    monkeypatch.delenv("POST_OFFICE_PASSWORD", raising=False)
    common = {"TESTING": True, "DATABASE_PATH": str(tmp_path / "missing.sqlite3")}
    with pytest.raises(RuntimeError, match="ATOM_API_KEY"):
        create_app(dict(common, ATOM_API_KEY=None, USER_PASSWORD="configured"))
    with pytest.raises(RuntimeError, match="POST_OFFICE_PASSWORD"):
        create_app(dict(common, ATOM_API_KEY="configured", USER_PASSWORD=None))
