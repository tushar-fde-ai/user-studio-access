"""
studio_access.client
=====================

A small, dependency-light client for Treasure Data's "Controlling AI Studio
Access" API.

Docs:
https://docs.treasure.ai/products/control-panel/security/users/controlling-ai-studio-access

The API lets an account administrator grant, check, or remove a user's
access to Treasure AI Studio via a per-user profile option. It is available
in both API v3 (``/access_control`` prefix) and v4 (no prefix); this client
defaults to v4.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional
from urllib import error as urlerror
from urllib import request as urlrequest


OPTION_KEY = "treasure_ai_studio"
FULL_ACCESS = "full_access"

API_VERSIONS = {
    "v3": "/v3/access_control/users/{user_id}/profile_options/" + OPTION_KEY,
    "v4": "/v4/users/{user_id}/profile_options/" + OPTION_KEY,
}


class StudioAccessError(Exception):
    """Raised when the Treasure AI API returns a non-2xx response."""

    def __init__(self, status: int, body: str):
        self.status = status
        self.body = body
        super().__init__(f"HTTP {status}: {body}")


@dataclass
class StudioAccessResult:
    """Normalized result of a Studio access API call."""

    user_id: int
    status_code: int
    value: Optional[str] = None  # "full_access" or None (unset -> account default)

    @property
    def has_access(self) -> bool:
        return self.value == FULL_ACCESS


class StudioAccessClient:
    """
    OOP client for granting, checking, and removing a user's Treasure AI
    Studio access.

    Parameters
    ----------
    api_key:
        Master API key, in ``ACCOUNT_ID/KEY`` format. Only a Master API key
        is accepted for PUT/DELETE operations per the docs.
    endpoint:
        Base URL of the Treasure Data REST API, e.g.
        ``https://api.treasuredata.com``. Defaults to the US region.
    api_version:
        ``"v3"`` or ``"v4"``. Both behave identically; v4 omits the
        ``/access_control`` path segment. Defaults to ``"v4"``.
    """

    def __init__(
        self,
        api_key: str,
        endpoint: str = "https://api.treasuredata.com",
        api_version: str = "v4",
    ):
        if not api_key:
            raise ValueError("api_key is required (set TD_API_KEY in your .env)")
        if api_version not in API_VERSIONS:
            raise ValueError(f"api_version must be one of {list(API_VERSIONS)}")

        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.api_version = api_version

    # -- public API -------------------------------------------------------

    def grant_access(self, user_id: int) -> StudioAccessResult:
        """Grant a user full_access to Treasure AI Studio (PUT). Requires
        account administrator role."""
        body = json.dumps({"value": FULL_ACCESS}).encode("utf-8")
        status, payload = self._request("PUT", user_id, data=body)
        return StudioAccessResult(
            user_id=user_id, status_code=status, value=payload.get(OPTION_KEY)
        )

    def check_access(self, user_id: int) -> StudioAccessResult:
        """Check whether a user currently has Studio access (GET). Callable
        by an account admin, delegated admin, or the user themselves."""
        status, payload = self._request("GET", user_id)
        return StudioAccessResult(
            user_id=user_id, status_code=status, value=payload.get(OPTION_KEY)
        )

    def remove_access(self, user_id: int) -> StudioAccessResult:
        """
        Remove a user's Studio access grant (DELETE). Requires account
        administrator role.

        In restricted (opt-in) mode this immediately revokes issued
        credentials and blocks new sign-ins for that user. In default-allow
        mode it has no immediate effect, since ungranted users are still
        allowed.
        """
        status, _ = self._request("DELETE", user_id)
        return StudioAccessResult(user_id=user_id, status_code=status, value=None)

    # -- internals ----------------------------------------------------------

    def _path(self, user_id: int) -> str:
        return API_VERSIONS[self.api_version].format(user_id=user_id)

    def _request(self, method: str, user_id: int, data: Optional[bytes] = None):
        url = f"{self.endpoint}{self._path(user_id)}"
        req = urlrequest.Request(url, data=data, method=method)
        req.add_header("Authorization", f"TD1 {self.api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urlrequest.urlopen(req) as resp:
                status = resp.status
                raw = resp.read().decode("utf-8")
        except urlerror.HTTPError as exc:
            raise StudioAccessError(exc.code, exc.read().decode("utf-8")) from exc

        payload = json.loads(raw) if raw else {}
        return status, payload
