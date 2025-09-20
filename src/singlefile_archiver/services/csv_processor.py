"""CSV file processing service."""

import csv
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from ..utils.logging import get_logger

logger = get_logger(__name__)


class CSVProcessor:
    """Service for processing CSV files containing URLs."""
    
    def __init__(self):
        """Initialize CSV processor."""
        pass
    
    def is_valid_url(self, url: str) -> bool:
        """Validate if a string is a proper URL."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def load_urls(self, csv_file: Path) -> List[str]:
        """Load URLs from a CSV file (compatible with original format)."""
        urls = []
        
        if not csv_file.exists():
            logger.error(f"CSV file not found: {csv_file}")
            return urls
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get('url', '').strip()
                    if url and url.startswith(('http://', 'https://')):
                        urls.append(url)
            
            logger.info(f"Found {len(urls)} URLs in {csv_file}")
            return urls
        
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_file}: {e}")
            return []
    
    def save_urls(self, urls: List[str], csv_file: Path) -> bool:
        """Save URLs to a CSV file."""
        try:
            # Ensure parent directory exists
            csv_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['url'])
                
                # Write URLs
                for url in urls:
                    if url and self.is_valid_url(url):
                        writer.writerow([url])
                    else:
                        logger.warning(f"Skipping invalid URL: {url}")
            
            logger.info(f"Saved {len(urls)} URLs to {csv_file}")
            return True
        
        except Exception as e:
            logger.error(f"Error writing CSV file {csv_file}: {e}")
            return False
    
    def merge_csv_files(self, input_files: List[Path], output_file: Path) -> bool:
        """Merge multiple CSV files into one."""
        all_urls = []
        
        for csv_file in input_files:
            urls = self.load_urls(csv_file)
            all_urls.extend(urls)
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in all_urls:
            if url not in seen:
                unique_urls.append(url)
                seen.add(url)
        
        logger.info(f"Merged {len(all_urls)} URLs into {len(unique_urls)} unique URLs")
        return self.save_urls(unique_urls, output_file)
    
    def filter_urls_by_domain(self, csv_file: Path, allowed_domains: List[str], output_file: Path) -> bool:
        """Filter URLs by allowed domains."""
        urls = self.load_urls(csv_file)
        filtered_urls = []
        
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                
                # Remove www. prefix for comparison
                if domain.startswith('www.'):
                    domain = domain[4:]
                
                if any(allowed_domain.lower() in domain for allowed_domain in allowed_domains):
                    filtered_urls.append(url)
            except Exception as e:
                logger.warning(f"Error filtering URL {url}: {e}")
        
        logger.info(f"Filtered {len(urls)} URLs to {len(filtered_urls)} URLs matching domains")
        return self.save_urls(filtered_urls, output_file)
    
    def validate_csv(self, csv_file: Path) -> dict:
        """Validate a CSV file and return statistics."""
        stats = {
            "total_rows": 0,
            "valid_urls": 0,
            "invalid_urls": 0,
            "empty_rows": 0,
            "unique_domains": set(),
            "errors": []
        }
        
        if not csv_file.exists():
            stats["errors"].append(f"File not found: {csv_file}")
            return stats
        
        try:
            with open(csv_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                # Skip header if present
                first_row = next(reader, None)
                if first_row and csv.Sniffer().has_header(csv_file.read_text()):
                    pass  # Header row, continue with data rows
                else:
                    # Process first row as data
                    if first_row:
                        self._process_csv_row(first_row, 1, stats)
                
                for row_num, row in enumerate(reader, start=2):
                    stats["total_rows"] += 1
                    self._process_csv_row(row, row_num, stats)
        
        except Exception as e:
            stats["errors"].append(f"Error reading file: {e}")
        
        # Convert set to list for JSON serialization
        stats["unique_domains"] = list(stats["unique_domains"])
        return stats
    
    def _process_csv_row(self, row: List[str], row_num: int, stats: dict) -> None:
        """Process a single CSV row for validation."""
        if not row or not row[0].strip():
            stats["empty_rows"] += 1
            return
        
        url = row[0].strip()
        if self.is_valid_url(url):
            stats["valid_urls"] += 1
            try:
                domain = urlparse(url).netloc.lower()
                if domain.startswith('www.'):
                    domain = domain[4:]
                stats["unique_domains"].add(domain)
            except Exception:
                pass
        else:
            stats["invalid_urls"] += 1
            stats["errors"].append(f"Invalid URL at row {row_num}: {url}")