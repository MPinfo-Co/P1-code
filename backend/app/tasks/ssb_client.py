"""SSB REST API client.

Decoupled from config.py — all connection parameters are passed via constructor.
"""
import logging
from datetime import datetime
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

BRUTE_FORCE_LIMIT = 8


class SSBClient:
    """SSB REST API client with auth token management and pagination."""

    def __init__(self, *, host: str, logspace: str, username: str, password: str):
        """Create an SSBClient.

        Args:
            host: Base URL of the SSB server (trailing slash is stripped).
            logspace: SSB logspace name to query.
            username: SSB login username.
            password: SSB login password.
        """
        self.host = host.rstrip("/")
        self.logspace = logspace
        self.username = username
        self.password = password
        self._client = httpx.Client(verify=False, timeout=30.0)
        self._token: Optional[str] = None
        self._login_failures: int = 0

    def _login(self) -> None:
        if self._login_failures >= BRUTE_FORCE_LIMIT:
            raise RuntimeError(
                f"SSB login failed {self._login_failures} times, stopping to avoid account lockout (SSB threshold: 10)"
            )
        resp = self._client.post(
            f"{self.host}/api/5/login",
            data={"username": self.username, "password": self.password},
        )
        data = resp.json()
        if data.get("error", {}).get("code"):
            self._login_failures += 1
            raise RuntimeError(
                f"SSB login failed: {data['error'].get('message', 'unknown error')}"
            )
        self._token = data["result"]
        self._login_failures = 0
        logger.info("SSB login successful")

    def _auth_headers(self) -> dict:
        if not self._token:
            self._login()
        return {"Cookie": f"AUTHENTICATION_TOKEN={self._token}"}

    def fetch_logs(
        self,
        time_from: datetime,
        time_to: datetime,
        search_expression: str = "",
    ) -> list[dict]:
        """Fetch logs from SSB with automatic pagination and token refresh.

        Args:
            time_from: Start of the time window (UTC).
            time_to: End of the time window (UTC).
            search_expression: SSB filter expression (empty means all logs).

        Returns:
            Combined list of log dicts from all pages.
        """
        all_logs: list[dict] = []
        offset = 0
        limit = 1000

        while True:
            resp = self._client.get(
                f"{self.host}/api/5/search/logspace/filter/{self.logspace}",
                params={
                    "from": int(time_from.timestamp()),
                    "to": int(time_to.timestamp()),
                    "search_expression": search_expression,
                    "offset": offset,
                    "limit": limit,
                },
                headers=self._auth_headers(),
            )
            if resp.status_code == 401:
                self._token = None
                self._login()
                continue
            resp.raise_for_status()
            batch = resp.json().get("result", [])
            all_logs.extend(batch)
            if len(batch) < limit:
                break
            offset += limit

        return all_logs

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()
