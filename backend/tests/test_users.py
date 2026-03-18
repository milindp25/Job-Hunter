from __future__ import annotations

from httpx import AsyncClient


class TestGetMe:
    """Tests for GET /api/v1/users/me."""

    async def test_get_me_authenticated(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "profile" in data
        assert data["user"]["email"] == "testuser@example.com"
        assert data["user"]["full_name"] == "Test User"
        assert data["profile"]["onboarding_completed"] is False

    async def test_get_me_unauthenticated(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401


class TestUpdateProfile:
    """Tests for profile update endpoints."""

    async def test_update_profile(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/users/me",
            headers=auth_headers,
            json={
                "phone": "+1234567890",
                "location": "San Francisco, CA",
                "summary": "Experienced software engineer",
                "linkedin_url": "https://linkedin.com/in/testuser",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+1234567890"
        assert data["location"] == "San Francisco, CA"
        assert data["summary"] == "Experienced software engineer"
        assert data["linkedin_url"] == "https://linkedin.com/in/testuser"

    async def test_update_skills(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/users/me/skills",
            headers=auth_headers,
            json={
                "skills": [
                    {"name": "Python", "level": "expert", "years": 5.0},
                    {"name": "TypeScript", "level": "advanced", "years": 3.0},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["skills"]) == 2
        assert data["skills"][0]["name"] == "Python"
        assert data["skills"][1]["name"] == "TypeScript"

    async def test_update_experience(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/users/me/experience",
            headers=auth_headers,
            json={
                "experience": [
                    {
                        "company": "Acme Corp",
                        "title": "Senior Developer",
                        "description": "Built microservices",
                        "start_date": "2020-01-01",
                        "end_date": "2023-06-30",
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["experience"]) == 1
        assert data["experience"][0]["company"] == "Acme Corp"
        assert data["experience"][0]["title"] == "Senior Developer"

    async def test_update_education(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/users/me/education",
            headers=auth_headers,
            json={
                "education": [
                    {
                        "institution": "MIT",
                        "degree": "B.S.",
                        "field": "Computer Science",
                        "start_date": "2014-09-01",
                        "end_date": "2018-06-01",
                    }
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["education"]) == 1
        assert data["education"][0]["institution"] == "MIT"
        assert data["education"][0]["degree"] == "B.S."


class TestOnboarding:
    """Tests for onboarding endpoints."""

    async def test_save_onboarding_step(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.put(
            "/api/v1/users/me/onboarding",
            headers=auth_headers,
            json={
                "phone": "+1234567890",
                "location": "New York, NY",
                "desired_roles": ["Backend Engineer", "Full Stack Developer"],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "completed" in data
        assert "profile_completeness" in data
        assert "missing_fields" in data
        assert data["completed"] is False
        # phone (+5) + location (+5) + desired_roles (+10) = 20
        assert data["profile_completeness"] >= 20

    async def test_complete_onboarding(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/v1/users/me/onboarding/complete",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] is True
        assert "profile_completeness" in data

    async def test_get_onboarding_status(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/v1/users/me/onboarding/status",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "completed" in data
        assert "profile_completeness" in data
        assert "missing_fields" in data
        assert isinstance(data["missing_fields"], list)


class TestDeactivateUser:
    """Tests for DELETE /api/v1/users/me."""

    async def test_deactivate_user(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete("/api/v1/users/me", headers=auth_headers)
        assert response.status_code == 204

        # Confirm the user is deactivated -- GET /me should still work
        # (the token is still valid) but is_active should be False
        me_resp = await client.get("/api/v1/users/me", headers=auth_headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["user"]["is_active"] is False
