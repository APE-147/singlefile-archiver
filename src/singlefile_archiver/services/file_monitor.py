"""File system monitoring service."""

import os
import re
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import List, Set

# Try to import watchdog, use polling if not available
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    
    # Create dummy classes for compatibility
    class FileSystemEventHandler:
        pass

from ..utils.logging import get_logger

logger = get_logger(__name__)


class HTMLFileHandler(FileSystemEventHandler):
    """Handler for file system events in the incoming directory"""
    
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor
        self.processed_files: Set[str] = set()  # Track processed files to avoid duplicates
    
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.process_file(Path(event.src_path))
    
    def on_moved(self, event):
        """Handle file move events"""
        if not event.is_directory:
            self.process_file(Path(event.dest_path))
    
    def process_file(self, file_path: Path):
        """Process a single file if it matches our criteria"""
        # Avoid processing the same file multiple times
        if str(file_path) in self.processed_files:
            return
        
        # Small delay to ensure file is fully written
        time.sleep(0.5)
        
        if self.monitor.should_move_file(file_path):
            self.monitor.move_file_to_archive(file_path)
            self.processed_files.add(str(file_path))


class FileMonitor:
    """Service for monitoring and processing files."""
    
    def __init__(self, watch_dir: Path, archive_dir: Path, check_interval: int = 2):
        """Initialize file monitor."""
        self.watch_dir = Path(watch_dir)
        self.archive_dir = Path(archive_dir)
        self.check_interval = check_interval
        self.processed_files: Set[str] = set()
        
        # Ensure directories exist
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"📁 Incoming directory: {self.watch_dir}")
        logger.info(f"📁 Archive directory: {self.archive_dir}")
    
    def should_move_file(self, file_path: Path) -> bool:
        """Check if file matches our naming pattern criteria"""
        if not file_path.exists():
            return False
            
        if not file_path.suffix.lower() == '.html':
            return False
        
        filename = file_path.name
        
        # Special condition: Files containing "X 上的" are always moved regardless of timestamp
        if "X 上的" in filename:
            logger.info(f"✅ File matches special pattern (contains 'X 上的'): {filename}")
            return True
        
        # Pattern for timestamp in filename - very flexible
        timestamp_patterns = [
            r'\(\d+[_\-/]\d+[_\-/]\d+\s+\d+[:\：\.]\d+[:\：\.]?\d*\s*[APM]*\)',  # (8_20_2025 1:18:55 PM) or (8_14_2025 8：58：47 PM)
            r'\(\d{4}[_\-/]\d{1,2}[_\-/]\d{1,2}[_\s\-T]\d{1,2}[:\：\.]?\d{1,2}[:\：\.]?\d*\)',  # (2025-08-20 13:18:55)
            r'\(\d{8}[_\-T]\d{6}\)',  # (20250820_131855)
            r'\(\d{4}[_\-/]\d{1,2}[_\-/]\d{1,2}\)',  # (2025-08-20) - date only
            r'\(\d+[_\-/]\d+[_\-/]\d+\)',  # (8_20_2025) - flexible date format
        ]
        
        for pattern in timestamp_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                logger.info(f"✅ File matches timestamp pattern: {filename}")
                return True
        
        logger.debug(f"❌ File does not match any patterns: {filename}")
        return False
    
    def move_file_to_archive(self, file_path: Path) -> bool:
        """Move file from incoming to archive directory"""
        try:
            # Ensure archive directory exists
            self.archive_dir.mkdir(parents=True, exist_ok=True)
            
            destination = self.archive_dir / file_path.name
            
            # Handle filename conflicts
            if destination.exists():
                # Add timestamp suffix to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                stem = destination.stem
                suffix = destination.suffix
                destination = self.archive_dir / f"{stem}_moved_{timestamp}{suffix}"
            
            # Move the file
            shutil.move(str(file_path), str(destination))
            logger.info(f"📁 Moved: {file_path.name} → {destination}")
            
            # Verify the move was successful
            if destination.exists() and not file_path.exists():
                logger.info(f"✅ Successfully moved to archive: {destination.name}")
                return True
            else:
                logger.error(f"❌ Move verification failed for: {file_path.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error moving file {file_path.name}: {e}")
            return False
    
    def scan_existing_files(self) -> int:
        """Scan existing files in incoming directory and process matching ones"""
        logger.info("🔍 Scanning existing files in incoming directory...")
        
        if not self.watch_dir.exists():
            logger.warning(f"Incoming directory does not exist: {self.watch_dir}")
            return 0
        
        moved_count = 0
        
        for file_path in self.watch_dir.glob("*.html"):
            if str(file_path) not in self.processed_files:
                if self.should_move_file(file_path):
                    if self.move_file_to_archive(file_path):
                        moved_count += 1
                        self.processed_files.add(str(file_path))
        
        if moved_count > 0:
            logger.info(f"📦 Initial scan complete: {moved_count} files moved")
        else:
            logger.info("📦 Initial scan complete: no matching files found")
        
        return moved_count
    
    def start_monitoring(self, use_watchdog: bool = True) -> None:
        """Start file system monitoring"""
        logger.info("🚀 Starting File Monitor")
        logger.info("=" * 60)
        
        # Scan existing files first
        self.scan_existing_files()
        
        # Set up file system monitoring
        if WATCHDOG_AVAILABLE and use_watchdog:
            self._start_watchdog_monitoring()
        else:
            self._start_polling_monitoring()
    
    def _start_watchdog_monitoring(self) -> None:
        """Use watchdog for real-time monitoring"""
        try:
            event_handler = HTMLFileHandler(self)
            observer = Observer()
            observer.schedule(event_handler, str(self.watch_dir), recursive=False)
            observer.start()
            
            logger.info("👁️ Real-time file monitoring started (watchdog)")
            logger.info("Press Ctrl+C to stop monitoring")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Stopping file monitor...")
                observer.stop()
            
            observer.join()
            
        except Exception as e:
            logger.error(f"Error setting up watchdog monitoring: {e}")
            logger.info("Falling back to polling mode")
            self._start_polling_monitoring()
    
    def _start_polling_monitoring(self) -> None:
        """Use polling-based monitoring"""
        logger.info("📊 Starting polling-based monitoring")
        
        try:
            while True:
                # Check for new files
                if self.watch_dir.exists():
                    for file_path in self.watch_dir.glob("*.html"):
                        if str(file_path) not in self.processed_files:
                            if self.should_move_file(file_path):
                                if self.move_file_to_archive(file_path):
                                    self.processed_files.add(str(file_path))
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping polling monitor...")
    
    def process_files(self) -> int:
        """Process all matching files in watch directory."""
        files = self.find_matching_files()
        if not files:
            return 0
        
        moved_count = 0
        for file_path in files:
            if self.move_file_to_archive(file_path):
                moved_count += 1
        
        if moved_count > 0:
            logger.info(f"Processed {moved_count} files")
        
        return moved_count
    
    def get_status(self) -> dict:
        """Get current status of monitored directories."""
        try:
            watch_files = self.find_matching_files()
            archive_files = list(self.archive_dir.glob(self.pattern))
            
            return {
                "watch_dir": str(self.watch_dir),
                "archive_dir": str(self.archive_dir),
                "pattern": self.pattern,
                "pending_files": len(watch_files),
                "archived_files": len(archive_files),
                "watch_exists": self.watch_dir.exists(),
                "archive_exists": self.archive_dir.exists(),
            }
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {
                "error": str(e)
            }