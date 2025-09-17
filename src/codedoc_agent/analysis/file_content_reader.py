"""Module for reading and aggregating content from important files."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .models import ImportantFile

logger = logging.getLogger(__name__)


@dataclass
class FileContent:
    """Represents content of a single file."""
    file_path: str
    content: str
    importance_level: str
    reasons: List[str]
    content_type: str
    file_size_bytes: int
    line_count: int
    is_readable: bool
    error_message: Optional[str] = None


@dataclass
class AggregatedFileContent:
    """Aggregated content from all important files."""
    files: List[FileContent]
    total_files: int
    successful_reads: int
    failed_reads: int
    total_lines: int
    total_size_bytes: int
    critical_files_count: int
    high_files_count: int
    medium_files_count: int


class FileContentReader:
    """Reads and aggregates content from important files."""
    
    def __init__(self, repo_path: str):
        """Initialize reader with repository path.
        
        Args:
            repo_path: Path to the repository root.
        """
        self.repo_path = Path(repo_path)
        
        # File types to skip (binary or large files)
        self.skip_extensions = {
            '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.tar', '.gz', '.bz2', '.7z', '.rar',
            '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.db', '.sqlite', '.sqlite3'
        }
        
        # Maximum file size to read (in bytes)
        self.max_file_size = 1024 * 1024  # 1MB
        
        # Maximum lines to read per file
        self.max_lines_per_file = 2000
    
    def read_important_files(self, important_files: List[ImportantFile]) -> AggregatedFileContent:
        """Read content from all important files.
        
        Args:
            important_files: List of ImportantFile objects to read.
            
        Returns:
            AggregatedFileContent with all file contents and metadata.
        """
        logger.info(f"Reading content from {len(important_files)} important files")
        
        file_contents = []
        successful_reads = 0
        failed_reads = 0
        total_lines = 0
        total_size = 0
        
        # Count by importance level
        critical_count = sum(1 for f in important_files if f.importance_level == "CRITICAL")
        high_count = sum(1 for f in important_files if f.importance_level == "HIGH")
        medium_count = sum(1 for f in important_files if f.importance_level == "MEDIUM")
        
        for important_file in important_files:
            file_content = self._read_single_file(important_file)
            file_contents.append(file_content)
            
            if file_content.is_readable:
                successful_reads += 1
                total_lines += file_content.line_count
                total_size += file_content.file_size_bytes
            else:
                failed_reads += 1
        
        aggregated = AggregatedFileContent(
            files=file_contents,
            total_files=len(important_files),
            successful_reads=successful_reads,
            failed_reads=failed_reads,
            total_lines=total_lines,
            total_size_bytes=total_size,
            critical_files_count=critical_count,
            high_files_count=high_count,
            medium_files_count=medium_count
        )
        
        logger.info(f"File reading completed: {successful_reads} successful, {failed_reads} failed")
        return aggregated
    
    def _read_single_file(self, important_file: ImportantFile) -> FileContent:
        """Read content from a single important file.
        
        Args:
            important_file: ImportantFile object to read.
            
        Returns:
            FileContent with file data or error information.
        """
        file_path = self.repo_path / important_file.file_path
        
        # Initialize FileContent
        file_content = FileContent(
            file_path=important_file.file_path,
            content="",
            importance_level=important_file.importance_level,
            reasons=important_file.reasons,
            content_type=important_file.content_type,
            file_size_bytes=0,
            line_count=0,
            is_readable=False
        )
        
        try:
            # Check if file exists
            if not file_path.exists():
                file_content.error_message = "File does not exist"
                return file_content
            
            # Check if it's a file (not directory)
            if not file_path.is_file():
                file_content.error_message = "Path is not a file"
                return file_content
            
            # Check file extension
            if file_path.suffix.lower() in self.skip_extensions:
                file_content.error_message = f"Skipped binary/large file type: {file_path.suffix}"
                return file_content
            
            # Check file size
            file_size = file_path.stat().st_size
            file_content.file_size_bytes = file_size
            
            if file_size > self.max_file_size:
                file_content.error_message = f"File too large: {file_size} bytes > {self.max_file_size} bytes"
                return file_content
            
            # Read file content
            content = self._safe_read_file(file_path)
            if content is None:
                file_content.error_message = "Could not decode file content"
                return file_content
            
            # Limit lines if necessary
            lines = content.split('\n')
            if len(lines) > self.max_lines_per_file:
                lines = lines[:self.max_lines_per_file]
                content = '\n'.join(lines) + f"\n\n... (truncated, showing first {self.max_lines_per_file} lines)"
            
            file_content.content = content
            file_content.line_count = len(lines)
            file_content.is_readable = True
            
            logger.debug(f"Successfully read {important_file.file_path}: {len(lines)} lines, {file_size} bytes")
            
        except Exception as e:
            file_content.error_message = f"Error reading file: {str(e)}"
            logger.warning(f"Failed to read {important_file.file_path}: {e}")
        
        return file_content
    
    def _safe_read_file(self, file_path: Path) -> Optional[str]:
        """Safely read file with multiple encoding attempts.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            File content as string, or None if reading failed.
        """
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception:
                break
        
        return None
    
    def create_content_summary(self, aggregated_content: AggregatedFileContent) -> str:
        """Create a summary of the aggregated file content.
        
        Args:
            aggregated_content: AggregatedFileContent to summarize.
            
        Returns:
            Human-readable summary string.
        """
        summary_lines = [
            f"📄 File Content Summary",
            f"==================",
            f"Total files: {aggregated_content.total_files}",
            f"Successfully read: {aggregated_content.successful_reads}",
            f"Failed to read: {aggregated_content.failed_reads}",
            f"Total lines: {aggregated_content.total_lines:,}",
            f"Total size: {aggregated_content.total_size_bytes:,} bytes",
            "",
            f"📊 By Importance Level:",
            f"  Critical: {aggregated_content.critical_files_count} files",
            f"  High: {aggregated_content.high_files_count} files", 
            f"  Medium: {aggregated_content.medium_files_count} files",
            "",
            f"📝 Readable Files:"
        ]
        
        for file_content in aggregated_content.files:
            if file_content.is_readable:
                summary_lines.append(
                    f"  ✅ {file_content.file_path} ({file_content.importance_level}, "
                    f"{file_content.line_count} lines)"
                )
            else:
                summary_lines.append(
                    f"  ❌ {file_content.file_path} - {file_content.error_message}"
                )
        
        return "\n".join(summary_lines)
