from fastapi.testclient import TestClient

from backend.app.database import init_db
from backend.app.main import app


init_db()


def test_register_login_and_project_flow():
    email = "demo@opspilot.test"
    password = "password123"

    with TestClient(app) as client:
        register_response = client.post(
            "/api/auth/register",
            json={
                "email": email,
                "password": password,
            },
        )

        assert register_response.status_code in (200, 409)

        if register_response.status_code == 409:
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": email,
                    "password": password,
                },
            )

            assert login_response.status_code == 200
            token = login_response.json()["token"]

        else:
            token = register_response.json()["token"]

        headers = {
            "Authorization": f"Bearer {token}",
        }

        me_response = client.get(
            "/api/auth/me",
            headers=headers,
        )

        assert me_response.status_code == 200
        assert me_response.json()["email"] == email

        project_response = client.post(
            "/api/projects",
            headers=headers,
            json={
                "name": "Demo Website",
                "repository_url": "https://github.com/example/demo",
                "application_url": "https://example.com",
                "health_endpoint": "https://example.com/health",
                "environment": "production",
            },
        )

        assert project_response.status_code == 200

        project = project_response.json()

        assert project["name"] == "Demo Website"

        projects_response = client.get(
            "/api/projects",
            headers=headers,
        )

        assert projects_response.status_code == 200

        projects = projects_response.json()["projects"]

        assert any(
            item["id"] == project["id"]
            for item in projects
        )