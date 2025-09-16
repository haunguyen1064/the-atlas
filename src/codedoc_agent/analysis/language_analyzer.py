"""Simplified language analyzer using Git integration data."""

import logging
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

from .models import LanguageInfo

logger = logging.getLogger(__name__)


class LanguageDataProcessor:
    """Processes language data from Git integration for AI Agent input."""
    
    def __init__(self):
        """Initialize language data processor."""
        self.language_extensions = {
            'Python': ['.py', '.pyw', '.pyx', '.pyi'],
            'JavaScript': ['.js', '.mjs', '.cjs'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'C': ['.c', '.h'],
            'C++': ['.cpp', '.cxx', '.cc', '.hpp', '.hxx', '.hh'],
            'C#': ['.cs'],
            'PHP': ['.php', '.php3', '.php4', '.php5'],
            'Ruby': ['.rb', '.rbw'],
            'Swift': ['.swift'],
            'Kotlin': ['.kt', '.kts'],
            'Scala': ['.scala'],
            'Dart': ['.dart'],
            'HTML': ['.html', '.htm'],
            'CSS': ['.css'],
            'SCSS': ['.scss'],
            'Sass': ['.sass'],
            'Vue': ['.vue'],
            'React': ['.jsx', '.tsx'],
            'Shell': ['.sh', '.bash', '.zsh', '.fish'],
            'SQL': ['.sql'],
            'YAML': ['.yml', '.yaml'],
            'JSON': ['.json'],
            'XML': ['.xml'],
            'Markdown': ['.md', '.markdown']
        }
    
    def process_git_languages(self, git_languages: Dict[str, int], 
                            file_structure: Dict[str, List[str]]) -> Dict[str, LanguageInfo]:
        """Process language data from Git integration.
        
        Args:
            git_languages: Language -> line count from GitRepository._analyze_languages()
            file_structure: Directory structure from GitRepository.get_repository_structure()
            
        Returns:
            Dictionary mapping language names to LanguageInfo objects.
        """
        # Get total lines for percentage calculation
        total_lines = sum(git_languages.values()) if git_languages else 1
        
        # Get all files for sampling
        all_files = self._flatten_file_structure(file_structure)
        
        languages = {}
        
        for language_name, line_count in git_languages.items():
            # Calculate percentage
            percentage = (line_count / total_lines) * 100
            
            # Find files for this language
            language_files = self._get_files_for_language(language_name, all_files)
            file_count = len(language_files)
            
            # Get sample files (up to 10 most representative)
            sample_files = self._get_sample_files(language_files)
            
            languages[language_name] = LanguageInfo(
                name=language_name,
                line_count=line_count,
                file_count=file_count,
                percentage=percentage,
                sample_files=sample_files
            )
        
        return languages
    
    def get_primary_language(self, languages: Dict[str, LanguageInfo]) -> str:
        """Get the primary programming language.
        
        Args:
            languages: Dictionary of language information.
            
        Returns:
            Name of the primary language.
        """
        if not languages:
            return 'Unknown'
        
        # Return language with most lines of code
        return max(languages.items(), key=lambda x: x[1].line_count)[0]
    
    def get_top_languages(self, languages: Dict[str, LanguageInfo], 
                         count: int = 5) -> Dict[str, LanguageInfo]:
        """Get top N languages by line count.
        
        Args:
            languages: Dictionary of language information.
            count: Number of top languages to return.
            
        Returns:
            Dictionary of top languages.
        """
        sorted_languages = sorted(
            languages.items(), 
            key=lambda x: x[1].line_count, 
            reverse=True
        )
        
        return dict(sorted_languages[:count])
    
    def _flatten_file_structure(self, file_structure: Dict[str, List[str]]) -> List[str]:
        """Convert directory structure to flat file list.
        
        Args:
            file_structure: Directory -> files mapping.
            
        Returns:
            Flat list of all file paths.
        """
        all_files = []
        for directory, files in file_structure.items():
            for file_name in files:
                if directory == ".":
                    all_files.append(file_name)
                else:
                    all_files.append(f"{directory}/{file_name}")
        return all_files
    
    def _get_files_for_language(self, language_name: str, all_files: List[str]) -> List[str]:
        """Get files that belong to a specific language.
        
        Args:
            language_name: Name of the programming language.
            all_files: List of all files in the repository.
            
        Returns:
            List of files for the specified language.
        """
        if language_name not in self.language_extensions:
            return []
        
        extensions = self.language_extensions[language_name]
        language_files = []
        
        for file_path in all_files:
            file_extension = Path(file_path).suffix.lower()
            if file_extension in extensions:
                language_files.append(file_path)
        
        return language_files
    
    def _get_sample_files(self, language_files: List[str]) -> List[str]:
        """Get representative sample files for a language.
        
        Args:
            language_files: List of files for a specific language.
            
        Returns:
            List of up to 10 sample files, prioritizing important ones.
        """
        if not language_files:
            return []
        
        # Prioritize certain file types/names
        priority_patterns = [
            'main', 'app', 'index', 'server', 'run',
            'config', 'settings', 'models', 'views',
            'routes', 'controllers', 'services'
        ]
        
        prioritized = []
        others = []
        
        for file_path in language_files:
            file_name = Path(file_path).stem.lower()
            if any(pattern in file_name for pattern in priority_patterns):
                prioritized.append(file_path)
            else:
                others.append(file_path)
        
        # Return prioritized files first, then others, up to 10 total
        sample = prioritized[:5] + others[:5]
        return sample[:10]
    
    def create_language_summary_for_ai(self, languages: Dict[str, LanguageInfo]) -> str:
        """Create a concise language summary for AI Agent input.
        
        Args:
            languages: Dictionary of language information.
            
        Returns:
            Formatted string summary for AI consumption.
        """
        if not languages:
            return "No programming languages detected."
        
        primary = self.get_primary_language(languages)
        total_files = sum(lang.file_count for lang in languages.values())
        
        summary_lines = [
            f"Primary Language: {primary}",
            f"Total Languages: {len(languages)}",
            f"Total Code Files: {total_files}",
            "",
            "Language Breakdown:"
        ]
        
        # Sort by line count and show top languages
        sorted_langs = sorted(
            languages.items(),
            key=lambda x: x[1].line_count,
            reverse=True
        )
        
        for lang_name, lang_info in sorted_langs[:10]:  # Top 10 languages
            summary_lines.append(
                f"- {lang_name}: {lang_info.percentage:.1f}% "
                f"({lang_info.line_count:,} lines, {lang_info.file_count} files)"
            )
            
            # Add sample files for top 3 languages
            if len(summary_lines) <= 8 and lang_info.sample_files:  # Top 3 only
                sample_str = ", ".join(lang_info.sample_files[:3])
                summary_lines.append(f"  Sample files: {sample_str}")
        
        return "\n".join(summary_lines)