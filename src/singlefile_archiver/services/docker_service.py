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
        """Generate a readable output filename based on page title with enhanced content preservation."""
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
        use_enhanced_naming = os.getenv('FF_ENHANCED_CONTENT_NAMING', 'true').lower() == 'true'

        if use_optimization and use_enhanced_naming:
            # **NEW: Use enhanced content preservation strategy**
            base = self._generate_enhanced_filename(title, url)
        elif use_optimization:
            # Use existing optimized filename generation
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
        
        # **ENHANCED: Better duplicate handling with semantic preservation**
        if candidate.exists():
            candidate = self._resolve_filename_conflict(candidate, title, url, use_enhanced_naming)

        return candidate

    def _generate_enhanced_filename(self, title: str, url: str) -> str:
        """Generate enhanced filename using the new content preservation strategy.
        
        Args:
            title: Page title
            url: Source URL
            
        Returns:
            Enhanced filename base (without extension)
        """
        # Import the enhanced functions from optimize module
        from ..commands.optimize import (
            create_standardized_filename, 
            create_enhanced_content_filename,
            _has_url_indicators
        )
        
        # **FIXED: Check if the TITLE contains URL indicators, not create mock with URL**
        # This determines if we should show URL info or focus on content
        has_url_info = _has_url_indicators(title)
        
        try:
            if has_url_info:
                # Use standardized URL format with 150-byte limit
                return create_standardized_filename(title, url, max_bytes=150)
            else:
                # Use enhanced content preservation format with 150-byte limit
                return create_enhanced_content_filename(title, max_bytes=150)
        except Exception as e:
            logger.warning(f"Failed to generate enhanced filename for {title[:50]}...: {e}")
            # Fallback to canonical format
            return build_canonical_basename(title, url, max_title_length=120)

    def _resolve_filename_conflict(self, candidate: Path, title: str, url: str, use_enhanced: bool) -> Path:
        """Resolve filename conflicts with better content preservation.
        
        Args:
            candidate: Original candidate path
            title: Page title  
            url: Source URL
            use_enhanced: Whether to use enhanced naming
            
        Returns:
            Resolved unique path
        """
        if not candidate.exists():
            return candidate
            
        base_stem = candidate.stem
        extension = candidate.suffix
        output_dir = candidate.parent
        
        # Get existing files to avoid conflicts
        existing_files = {f.stem.lower() for f in output_dir.glob('*.html')}
        
        if use_enhanced:
            # Use enhanced conflict resolution
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Try to preserve content while adding uniqueness
            from ..commands.optimize import _ensure_unique_filename
            
            # Add timestamp to title and regenerate
            timestamped_title = f"{title} {timestamp}"
            enhanced_base = self._generate_enhanced_filename(timestamped_title, url)
            unique_base = _ensure_unique_filename(enhanced_base, existing_files)
            
            new_candidate = output_dir / f"{safe_filename(unique_base)}{extension}"
            
        else:
            # Legacy timestamp approach
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_stem = f"{base_stem}_{timestamp}"
            new_candidate = output_dir / f"{new_stem}{extension}"
        
        # Final safety check
        counter = 1
        while new_candidate.exists() and counter < 100:
            if use_enhanced:
                extra_unique = f"{unique_base}_{counter:02d}"
                new_candidate = output_dir / f"{safe_filename(extra_unique)}{extension}"
            else:
                new_candidate = output_dir / f"{base_stem}_{timestamp}_{counter:02d}{extension}"
            counter += 1
        
        return new_candidate

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
