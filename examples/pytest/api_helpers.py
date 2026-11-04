"""HTTP helpers shared by the Customers API tests."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class ApiClient:
    """Thin requests wrapper: base URL, explicit timeout, bearer auth."""

    def __init__(self, base_url: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def request(self, method: str, path: str, token: Optional[str] = None,
                headers: Optional[Dict[str, str]] = None, **kwargs: Any) -> requests.Response:
        all_headers = dict(headers or {})
        if token is not None:
            all_headers["Authorization"] = f"Bearer {token}"
        kwargs.setdefault("timeout", self.timeout)
        return self.session.request(method, f"{self.base_url}{path}", headers=all_headers, **kwargs)

    def get(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> requests.Response:
        return self.request("DELETE", path, **kwargs)


def describe(response: requests.Response) -> str:
    """Assertion message with status and body (never request headers/tokens)."""
    return f"{response.request.method} {response.url} -> {response.status_code}: {response.text[:500]}"
