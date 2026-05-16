from __future__ import annotations

from curl_cffi.requests import AsyncSession

_TOKEN_URL = (
    "https://auth.opensky-network.org/auth/realms/opensky-network"
    "/protocol/openid-connect/token"
)


async def _post(url: str, data: dict) -> dict:
    async with AsyncSession(impersonate="chrome") as session:
        resp = await session.post(url, data=data)
        resp.raise_for_status()
        return resp.json()


async def fetch_token(client_id: str, client_secret: str) -> str:
    data = await _post(_TOKEN_URL, {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    })
    return data["access_token"]
