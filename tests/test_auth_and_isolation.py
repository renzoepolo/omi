def get_token(client, email="user@test.com", password="test123"):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_success(client):
    response = client.post("/auth/login", json={"email": "user@test.com", "password": "test123"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]


def test_access_project_allowed(client):
    token = get_token(client)
    response = client.get(
        "/projects/current",
        headers={"Authorization": f"Bearer {token}", "X-Project-Id": "1"},
    )
    assert response.status_code == 200
    assert response.json()["project_id"] == 1


def test_project_access_denied_between_projects(client):
    token = get_token(client)
    response = client.get(
        "/projects/current",
        headers={"Authorization": f"Bearer {token}", "X-Project-Id": "2"},
    )
    assert response.status_code == 403
