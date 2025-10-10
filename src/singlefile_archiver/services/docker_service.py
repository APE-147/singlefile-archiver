"""Docker service for SingleFile container management."""

import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse

import docker
from docker.errors import DockerException

from ..utils.config import get_config
from ..utils.logging import get_logger
from ..utils.paths import build_canonical_basename, optimize_filename, safe_filename

logger = get_logger(__name__)


@dataclass
class ArchiveResult:
    """Result of an archive operation."""
    success: bool
    output_file: Optional[Path] = None
    error: Optional[str] = None
    message: Optional[str] = None


class DockerService:
    """Service for managing Docker operations."""

    def __init__(self):
        """Initialize Docker service."""
        self.config = get_config()
        self._client: Optional[docker.DockerClient] = None

    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client, creating if necessary."""
        if self._client is None:
            try:
                self._client = docker.from_env()
            except DockerException as e:
                logger.error(f"Failed to create Docker client: {e}")
                raise
        return self._client

    def is_running(self) -> bool:
        """Check if Docker daemon is running."""
        try:
            self.client.ping()
            return True
        except DockerException:
            return False

    def pull_image(self) -> ArchiveResult:
        """Pull the SingleFile Docker image."""
        try:
            logger.info(f"Pulling Docker image: {self.config.docker_image}")
            self.client.images.pull(self.config.docker_image)
            return ArchiveResult(
                success=True,
                message=f"Successfully pulled {self.config.docker_image}"
            )
        except DockerException as e:
            error_msg = f"Failed to pull image: {e}"
            logger.error(error_msg)
            return ArchiveResult(success=False, error=error_msg)

    def get_container_status(self) -> Optional[dict]:
        """Get status of SingleFile container/image."""
        try:
            images = self.client.images.list(self.config.docker_image)
            if images:
                return {
                    "image": self.config.docker_image,
                    "id": images[0].id[:12],
                    "tags": images[0].tags
                }
            return None
        except DockerException:
            return None

    def archive_url(
        self,
        url: str,
        output_dir: Path,
        cookies_file: Optional[Path] = None,
    ) -> ArchiveResult:
        """Archive a single URL using SingleFile."""
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            # Resolve cookies file if provided via argument or configuration
            container_cookies_path = self.config.docker_cookies_mount_path
            resolved_cookies: Optional[Path] = None

            candidate = cookies_file
            if candidate is None and self.config.docker_cookies_file:
                candidate = Path(self.config.docker_cookies_file)

            if candidate is not None:
                candidate_path = Path(candidate).expanduser()
                if candidate_path.exists():
                    resolved_cookies = candidate_path
                    logger.debug("Using cookies file: %s", candidate_path)
                else:
                    logger.warning("Cookies file not found, skipping: %s", candidate_path)

            # Docker run command
            docker_cmd = ["docker", "run", "--rm"]

            if resolved_cookies:
                docker_cmd.extend([
                    "-v",
                    f"{resolved_cookies}:{container_cookies_path}:ro",
                ])

            docker_cmd.append(self.config.docker_image)

            if resolved_cookies:
                docker_cmd.extend([
                    "--browser-cookies-file",
                    container_cookies_path,
                ])

            docker_cmd.append(url)

            logger.info(f"Running Docker command: {' '.join(docker_cmd)}")

            # Run container
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.config.docker_timeout
            )

            if result.returncode == 0:
                output_file: Optional[Path] = None

                if result.stdout:
                    output_file = self._derive_output_file(url, result.stdout, output_dir)
                    try:
                        output_file.write_text(result.stdout, encoding="utf-8")
                        logger.info("Wrote archive content from stdout to %s", output_file)
                        return ArchiveResult(
                            success=True,
                            output_file=output_file,
                            message=f"Archived via stdout to {output_file}"
                        )
                    except OSError as exc:
                        error_msg = f"Failed to save stdout content to {output_file}: {exc}"
                        logger.error(error_msg)
                        return ArchiveResult(success=False, error=error_msg)

                if not output_file:
                    output_file = self._derive_output_file(url, "", output_dir)

                if output_file and output_file.exists():
                    return ArchiveResult(
                        success=True,
                        output_file=output_file,
                        message=f"Successfully archived to {output_file}"
                    )

                error_msg = f"Archive command succeeded but produced no output for {url}"
                logger.error(error_msg)
                return ArchiveResult(success=False, error=error_msg)
            else:
                error_msg = f"Docker command failed: {result.stderr}"
                logger.error(error_msg)
                return ArchiveResult(success=False, error=error_msg)

        except subprocess.TimeoutExpired:
            error_msg = f"Archive operation timed out after {self.config.docker_timeout}s"
            logger.error(error_msg)
            return ArchiveResult(success=False, error=error_msg)

        except Exception as e:
            error_msg = f"Archive operation failed: {e}"
            logger.error(error_msg)
            return ArchiveResult(success=False, error=error_msg)

    def _derive_output_file(self, url: str, html_content: str, output_dir: Path) -> Path:
        """Generate a readable output filename based on page title."""
        title: Optional[str] = None

        if html_content:
            match = re.search(r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
            if match:
                extracted = unescape(match.group(1)).strip()
                # Collapse whitespace but preserve multilingual characters
                title = re.sub(r"\s+", " ", extracted)

        if not title:
            parsed_url = urlparse(url)
            fallback = f"{parsed_url.netloc or 'page'}{parsed_url.path}"
            if parsed_url.query:
                fallback = f"{fallback}?{parsed_url.query}"
            title = fallback or "archived_page"

        # Check feature flags for filename optimization
        use_optimization = os.getenv('FF_FILENAME_OPTIMIZATION', 'false').lower() == 'true'

        if use_optimization:
            # Use new optimized filename generation with deduplication
            # For single file operations, we don't have existing names context
            # The deduplication will be more effective in batch operations
            base = build_canonical_basename(title, url, max_title_length=100)
        else:
            # Legacy filename generation (backward compatibility)
            def _encode_url_for_filename(raw: str, max_len: int = 180) -> str:
                encoded = quote(raw, safe="")
                if len(encoded) > max_len:
                    return encoded[: max_len - 1] + "…"
                return encoded

            url_part = _encode_url_for_filename(url)
            base = f"({title}) [URL] {url_part}"

        sanitized = safe_filename(base)
        if not sanitized.endswith('.html'):
            sanitized += '.html'

        candidate = output_dir / sanitized
        if candidate.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            if use_optimization:
                # For optimized filenames, add timestamp to the title portion
                # Pass existing filename as context to avoid further conflicts
                existing_names = {candidate.stem.lower()}
                optimized_title = optimize_filename(f"{title} {timestamp}", max_length=100, existing_names=existing_names)
                base_with_timestamp = build_canonical_basename(optimized_title, url, max_title_length=100, existing_names=existing_names)
            else:
                # Legacy approach
                base_with_timestamp = f"{base}_{timestamp}"

            sanitized = safe_filename(base_with_timestamp)
            if not sanitized.endswith('.html'):
                sanitized += '.html'
            candidate = output_dir / sanitized

        return candidate

    def test_connection(self) -> ArchiveResult:
        """Test Docker connection with a simple container."""
        try:
            # Run a simple hello-world test
            result = subprocess.run(
                ["docker", "run", "--rm", "hello-world"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return ArchiveResult(
                    success=True,
                    message="Docker connection test successful"
                )
            else:
                error_msg = f"Docker test failed: {result.stderr}"
                return ArchiveResult(success=False, error=error_msg)

        except subprocess.TimeoutExpired:
            return ArchiveResult(
                success=False,
                error="Docker test timed out"
            )
        except Exception as e:
            return ArchiveResult(
                success=False,
                error=f"Docker test error: {e}"
            )
