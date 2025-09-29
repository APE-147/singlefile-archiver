"""Helper that bridges to the cookie-update utilities packaged with the project."""

from __future__ import annotations

from typing import Dict, List, Optional

from ..common.cookie_update_bridge import CookieBundle, CookieUpdateFetcher


class CookieProvider:
    """Expose cookie-update lookups for SingleFile archiving commands."""

    def __init__(self) -> None:
        self._fetcher = CookieUpdateFetcher()

    def get_bundle(self, domain_or_url: str) -> Optional[CookieBundle]:
        """Return the detailed cookie bundle for a domain or URL."""
        return self._fetcher.get_bundle(domain_or_url)

    def get_singlefile_cookies(self, domain_or_url: str) -> Optional[List[Dict[str, object]]]:
        """Return cookies formatted for SingleFile's ``--browser-cookies-file`` flag."""
        result = self._fetcher.get_singlefile_cookies(domain_or_url)
        return result if result else None

    def get_requests_cookies(self, domain_or_url: str) -> Optional[Dict[str, str]]:
        """Return cookies as a simple name/value mapping (requests compatible)."""
        result = self._fetcher.get_requests_cookies(domain_or_url)
        return result if result else None

    @staticmethod
    def normalize_domain(domain_or_url: str) -> Optional[str]:
        """Expose the same normalization logic used by the fetcher."""
        return CookieUpdateFetcher._normalize_domain(domain_or_url)  # type: ignore[attr-defined]
