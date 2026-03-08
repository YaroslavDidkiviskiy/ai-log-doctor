import io


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_upload_invalid_extension(client):
    file = io.BytesIO(b"hello world")
    resp = client.post(
        "/api/uploads",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert resp.status_code == 400


def test_upload_valid_file(client):
    content = b"2026-03-08 12:00:01 ERROR app.auth Test error\n"
    file = io.BytesIO(content)
    resp = client.post(
        "/api/uploads",
        files={"file": ("test.log", file, "text/plain")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["filename"] == "test.log"
    assert data["status"] == "uploaded"


def test_list_uploads(client):
    content = b"2026-03-08 12:00:01 ERROR app.auth Test error\n"
    client.post("/api/uploads", files={"file": ("a.log", io.BytesIO(content), "text/plain")})
    client.post("/api/uploads", files={"file": ("b.log", io.BytesIO(content), "text/plain")})

    resp = client.get("/api/uploads")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


def test_get_upload_not_found(client):
    resp = client.get("/api/uploads/9999")
    assert resp.status_code == 404


def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "AI Log Doctor" in resp.text
