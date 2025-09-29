"""Helpers for accessing the cookie-update project programmatically."""

from __future__ import annotations

import importlib.util
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class CookieUpdateUnavailable(RuntimeError):
    """Raised when the cookie-update project cannot be used."""


@dataclass
class CookieBundle:
    """Aggregated cookie data for a domain."""

    domain: str
    cookies: List[Dict[str, Any]]
    requests: Dict[str, str]
    singlefile: List[Dict[str, Any]]
    raw: Dict[str, Any]


class CookieUpdateFetcher:
    """Thin wrapper around the cookie-update download script."""

    def __init__(self, scripts_root: Optional[Path] = None) -> None:
        self._scripts_root = Path(scripts_root) if scripts_root else self._detect_scripts_root()
        self._cookie_update_root = (self._scripts_root / "desktop" / "info" / "cookie-update").resolve()
        self._download_script = self._cookie_update_root / "download_cookies.py"
        self._module = None
        self._downloader = None
        self._prepare_cookie = None
        self._cache: Dict[str, Optional[CookieBundle]] = {}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _detect_scripts_root(self) -> Path:
        current = Path(__file__).resolve()
        for parent in current.parents:
            candidate = parent / "desktop" / "info" / "cookie-update"
            if candidate.is_dir():
                return parent
        raise CookieUpdateUnavailable(
            "Unable to locate the cookie-update project from current path"
        )

    def _load_module(self):  # type: ignore[no-untyped-def]
        if self._module is not None:
            return self._module
        if not self._download_script.is_file():
            raise CookieUpdateUnavailable(f"download_cookies.py not found at {self._download_script}")
        spec = importlib.util.spec_from_file_location("cookie_update_download", str(self._download_script))
        if spec is None or spec.loader is None:
            raise CookieUpdateUnavailable("Unable to load cookie-update script module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        self._module = module
        self._prepare_cookie = getattr(module, "prepare_singlefile_cookie", None)
        return module

    def _ensure_downloader(self):  # type: ignore[no-untyped-def]
        if self._downloader is not None:
            return self._downloader
        module = self._load_module()
        load_env = getattr(module, "load_env_file", None)
        if callable(load_env):
            try:
                load_env()
            except Exception:
                # Environment loading is best-effort.
                pass
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        namespace_id = os.getenv("CLOUDFLARE_KV_NAMESPACE_ID")
        if not all([account_id, api_token, namespace_id]):
            raise CookieUpdateUnavailable("Missing Cloudflare credentials for cookie-update")
        downloader_cls = getattr(module, "CloudflareCookieDownloader", None)
        if downloader_cls is None:
            raise CookieUpdateUnavailable("CloudflareCookieDownloader not found in cookie-update script")
        self._downloader = downloader_cls(account_id, api_token, namespace_id)
        return self._downloader

    @staticmethod
    def _normalize_domain(domain_or_url: str) -> Optional[str]:
        value = (domain_or_url or "").strip()
        if not value:
            return None
        if "://" in value:
            parsed = urlparse(value)
            host = parsed.netloc or parsed.path
        else:
            host = value
        host = host.split("@")[-1]
        host = host.split(":")[0]
        host = host.strip().lstrip(".")
        if not host:
            return None
        return host.lower()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_bundle(self, domain_or_url: str) -> Optional[CookieBundle]:
        """Return cached cookie data for the given domain or URL."""

        domain = self._normalize_domain(domain_or_url)
        if not domain:
            return None
        if domain in self._cache:
            return self._cache[domain]
        try:
            downloader = self._ensure_downloader()
        except CookieUpdateUnavailable:
            self._cache[domain] = None
            return None
        try:
            result = downloader.get_cookies_for_domain(domain)
        except Exception:
            self._cache[domain] = None
            return None
        if not result:
            self._cache[domain] = None
            return None
        cookies = list(result.get("cookies") or [])
        requests_cookies: Dict[str, str] = {}
        singlefile_cookies: List[Dict[str, Any]] = []
        for cookie in cookies:
            if not isinstance(cookie, dict):
                continue
            name = cookie.get("name")
            value = cookie.get("value")
            if isinstance(name, str) and value is not None:
                requests_cookies[name] = str(value)
            if callable(self._prepare_cookie):
                try:
                    prepared = self._prepare_cookie(cookie)
                except Exception:
                    prepared = None
                if prepared:
                    singlefile_cookies.append(prepared)
        bundle = CookieBundle(
            domain=domain,
            cookies=cookies,
            requests=requests_cookies,
            singlefile=singlefile_cookies,
            raw=result,
        )
        self._cache[domain] = bundle
        return bundle

    def get_requests_cookies(self, domain_or_url: str) -> Optional[Dict[str, str]]:
        bundle = self.get_bundle(domain_or_url)
        if not bundle or not bundle.requests:
            return None
        return dict(bundle.requests)

    def get_singlefile_cookies(self, domain_or_url: str) -> Optional[List[Dict[str, Any]]]:
        bundle = self.get_bundle(domain_or_url)
        if not bundle or not bundle.singlefile:
            return None
        return [dict(item) for item in bundle.singlefile]

    @property
    def cookie_update_root(self) -> Path:
        return self._cookie_update_root

    @property
    def download_script(self) -> Path:
        return self._download_script
