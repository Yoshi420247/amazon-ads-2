"""Amazon Advertising API token management.

Handles OAuth 2.0 token refresh for the Amazon Ads API.
Tokens expire after 1 hour; this module manages automatic refresh.
"""

import os
import time
from dataclasses import dataclass

import httpx
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://api.amazon.com/auth/o2/token"


@dataclass
class Credentials:
    client_id: str
    client_secret: str
    refresh_token: str
    profile_id: str
    region: str = "NA"

    @classmethod
    def from_env(cls) -> "Credentials":
        return cls(
            client_id=os.environ["AMAZON_ADS_CLIENT_ID"],
            client_secret=os.environ["AMAZON_ADS_CLIENT_SECRET"],
            refresh_token=os.environ["AMAZON_ADS_REFRESH_TOKEN"],
            profile_id=os.environ["AMAZON_ADS_PROFILE_ID"],
            region=os.environ.get("AMAZON_ADS_REGION", "NA"),
        )

    @property
    def api_base_url(self) -> str:
        urls = {
            "NA": "https://advertising-api.amazon.com",
            "EU": "https://advertising-api-eu.amazon.com",
            "FE": "https://advertising-api-fe.amazon.com",
        }
        return urls.get(self.region, urls["NA"])


class TokenManager:
    """Manages OAuth 2.0 access tokens with automatic refresh."""

    def __init__(self, credentials: Credentials | None = None):
        self.credentials = credentials or Credentials.from_env()
        self._access_token: str | None = None
        self._token_expiry: float = 0

    @property
    def is_expired(self) -> bool:
        return time.time() >= self._token_expiry - 60  # 60s buffer

    def get_access_token(self) -> str:
        if self._access_token and not self.is_expired:
            return self._access_token
        return self.refresh()

    def refresh(self) -> str:
        response = httpx.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self.credentials.refresh_token,
                "client_id": self.credentials.client_id,
                "client_secret": self.credentials.client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        self._access_token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600)

        return self._access_token
