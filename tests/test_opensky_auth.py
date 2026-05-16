from unittest.mock import AsyncMock, patch

import pytest

from tracker.aviation_opensky.auth import fetch_token


async def test_fetch_token_returns_access_token():
    mock_response = {"access_token": "tok123", "expires_in": 300}
    with patch("tracker.aviation_opensky.auth._post", new_callable=AsyncMock, return_value=mock_response):
        result = await fetch_token("client-id", "client-secret")
    assert result == "tok123"


async def test_fetch_token_posts_client_credentials_grant():
    mock_response = {"access_token": "tok123", "expires_in": 300}
    with patch("tracker.aviation_opensky.auth._post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        await fetch_token("my-id", "my-secret")
    payload = mock_post.call_args[0][1]
    assert payload["grant_type"] == "client_credentials"
    assert payload["client_id"] == "my-id"
    assert payload["client_secret"] == "my-secret"
