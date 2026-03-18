from __future__ import annotations

from httpx import AsyncClient


class TestRegister:
    """Tests for POST /api/v1/auth/register."""

    async def test_register_success(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "strongpassword1",
                "full_name": "New User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["full_name"] == "New User"
        assert data["user"]["is_active"] is True

    async def test_register_duplicate_email(self, client: AsyncClient) -> None:
        payload = {
            "email": "dup@example.com",
            "password": "strongpassword1",
            "full_name": "First User",
        }
        # First registration should succeed
        resp1 = await client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        # Second registration with same email should fail
        resp2 = await client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 409
        data = resp2.json()
        assert data["error"]["code"] == "DUPLICATE_EMAIL"

    async def test_register_invalid_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "strongpassword1",
                "full_name": "Bad Email User",
            },
        )
        # Pydantic validation returns 422 for invalid EmailStr
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "shortpw@example.com",
                "password": "short",
                "full_name": "Short PW User",
            },
        )
        # Pydantic validation enforces min_length=8
        assert response.status_code == 422


class TestLogin:
    """Tests for POST /api/v1/auth/login."""

    async def _create_user(self, client: AsyncClient) -> None:
        """Helper to register a user before login tests."""
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "correctpassword",
                "full_name": "Login User",
            },
        )

    async def test_login_success(self, client: AsyncClient) -> None:
        await self._create_user(client)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "correctpassword"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    async def test_login_wrong_password(self, client: AsyncClient) -> None:
        await self._create_user(client)

        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"

    async def test_login_nonexistent_email(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "whatever123"},
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_CREDENTIALS"


class TestRefresh:
    """Tests for POST /api/v1/auth/refresh."""

    async def test_refresh_success(self, client: AsyncClient) -> None:
        # Register a user to get tokens
        reg_resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "strongpassword1",
                "full_name": "Refresh User",
            },
        )
        assert reg_resp.status_code == 201

        # Extract refresh token from the Set-Cookie header
        cookies = reg_resp.cookies
        refresh_token = cookies.get("refresh_token")
        # If refresh token is not in cookies, we need to get it another way.
        # The register endpoint sets it as a cookie but the test client may
        # capture it. Let's also try reading it from the response directly.
        # The refresh endpoint accepts it in the request body.
        # We can create a refresh token ourselves using the user's ID.
        if refresh_token is None:
            # Create a refresh token from the access token claims
            from app.utils.security import create_refresh_token, decode_token

            access_token = reg_resp.json()["access_token"]
            payload = decode_token(access_token)
            refresh_token = create_refresh_token({"sub": str(payload["sub"])})

        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "this-is-not-a-valid-jwt"},
        )
        assert response.status_code == 401


class TestLogout:
    """Tests for POST /api/v1/auth/logout."""

    async def test_logout_success(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"
