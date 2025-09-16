"""Simple orchestrator for preparing AI Agent input data."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import AIAnalysisInput, AIAnalysisResult, LanguageInfo
from .file_classifier import FilePatternProvider
from .language_analyzer import LanguageDataProcessor
from ..tools.git_integration import GitRepository, RepositoryInfo

logger = logging.getLogger(__name__)


class CodeAnalysisOrchestrator:
    """Simple orchestrator that prepares data for AI Agent analysis."""
    
    def __init__(self, git_repository: GitRepository):
        """Initialize orchestrator with Git repository.
        
        Args:
            git_repository: GitRepository instance with loaded repository.
        """
        self.git_repo = git_repository
        self.repo_path = git_repository.repo.working_dir
        
        # Initialize processors
        self.pattern_provider = FilePatternProvider()
        self.language_processor = LanguageDataProcessor()
    
    def prepare_ai_input(self, sample_files_count: int = 50) -> AIAnalysisInput:
        """Prepare input data for AI Agent analysis.
        
        Args:
            sample_files_count: Number of sample files to include for context.
            
        Returns:
            AIAnalysisInput ready for AI Agent processing.
        """
        logger.info("Preparing data for AI Agent analysis")
        
        # Get repository information from Git integration
        repo_info = self.git_repo.get_repository_info()
        file_structure = self.git_repo.get_repository_structure()
        
        # Process language data using Git integration results
        languages = self.language_processor.process_git_languages(
            repo_info.languages, file_structure
        )
        primary_language = self.language_processor.get_primary_language(languages)
        
        # Get sample files for AI context
        all_files = self._flatten_file_structure(file_structure)
        sample_files = self._get_representative_sample_files(
            all_files, languages, sample_files_count
        )
        
        # Create AI input structure
        ai_input = AIAnalysisInput(
            # Repository information
            repo_url=repo_info.url,
            repo_description=self._get_repo_description(),
            
            # Language data (from git_integration)
            languages=languages,
            primary_language=primary_language,
            
            # File structure
            total_files=len(all_files),
            directory_structure=file_structure,
            sample_files=sample_files,
            
            # Repository metadata
            total_commits=repo_info.total_commits,
            authors_count=len(repo_info.authors),
            last_commit_date=self._get_last_commit_date()
        )
        
        logger.info(f"Prepared AI input: {len(languages)} languages, {len(all_files)} files")
        return ai_input
    
    def get_language_patterns_for_ai(self, language: str) -> Dict[str, List[str]]:
        """Get language-specific patterns for AI Agent web search.
        
        Args:
            language: Programming language name.
            
        Returns:
            Dictionary with patterns for AI to search for.
        """
        return self.pattern_provider.get_all_patterns_for_language(language)
    
    def get_language_patterns_for_search(self, language: str) -> Dict[str, Any]:
        """Get language-specific patterns for AI Agent web search.
        
        Args:
            language: Programming language name.
            
        Returns:
            Dictionary with patterns for AI to search for.
        """
        return self.pattern_provider.get_all_patterns_for_language(language)
    
    def get_top_languages_for_search(self, count: int = 5) -> Dict[str, LanguageInfo]:
        """Get top languages for AI Agent to focus web search on.
        
        Args:
            count: Number of top languages to return.
            
        Returns:
            Dictionary of top languages by usage.
        """
        # Get repository info and process languages
        repo_info = self.git_repo.get_repository_info()
        file_structure = self.git_repo.get_repository_structure()
        languages = self.language_processor.process_git_languages(
            repo_info.languages, file_structure
        )
        
        return self.language_processor.get_top_languages(languages, count)
    
    def create_ai_search_context(self) -> str:
        """Create formatted context string for AI Agent web search.
        
        Returns:
            Formatted string with repository context for AI search.
        """
        ai_input = self.prepare_ai_input(sample_files_count=20)  # Smaller sample for search
        
        context_lines = [
            f"Repository: {ai_input.repo_url}",
            f"Primary Language: {ai_input.primary_language}",
            f"Total Files: {ai_input.total_files}",
            "",
            self.language_processor.create_language_summary_for_ai(ai_input.languages),
            "",
            "Sample Files:",
        ]
        
        # Add sample files grouped by directory
        current_dir = ""
        for file_path in ai_input.sample_files[:15]:  # Limit for search context
            file_dir = str(Path(file_path).parent) if '/' in file_path else "."
            if file_dir != current_dir:
                context_lines.append(f"  {file_dir}/")
                current_dir = file_dir
            context_lines.append(f"    {Path(file_path).name}")
        
        return "\n".join(context_lines)
    
    def _flatten_file_structure(self, file_structure: Dict[str, List[str]]) -> List[str]:
        """Convert directory structure to flat file list."""
        all_files = []
        for directory, files in file_structure.items():
            for file_name in files:
                if directory == ".":
                    all_files.append(file_name)
                else:
                    all_files.append(f"{directory}/{file_name}")
        return all_files
    
    def _get_representative_sample_files(self, all_files: List[str], 
                                       languages: Dict[str, LanguageInfo], 
                                       count: int) -> List[str]:
        """Get representative sample of files for AI context.
        
        Args:
            all_files: All files in repository.
            languages: Language information.
            count: Number of sample files to return.
            
        Returns:
            List of representative file paths.
        """
        if not all_files:
            return []
        
        # Prioritize files by importance indicators
        priority_files = []
        regular_files = []
        
        # Common important file patterns
        important_patterns = [
            'main', 'app', 'index', 'server', 'run', 'start',
            'config', 'settings', 'requirements', 'package',
            'readme', 'license', 'dockerfile', 'makefile'
        ]
        
        for file_path in all_files:
            file_name = Path(file_path).name.lower()
            file_stem = Path(file_path).stem.lower()
            
            # Check if file matches important patterns
            is_important = (
                any(pattern in file_name for pattern in important_patterns) or
                any(pattern in file_stem for pattern in important_patterns) or
                file_path.count('/') == 0  # Root level files
            )
            
            if is_important:
                priority_files.append(file_path)
            else:
                regular_files.append(file_path)
        
        # Include sample files from each language
        language_samples = []
        for lang_info in languages.values():
            language_samples.extend(lang_info.sample_files[:3])  # Top 3 per language
        
        # Combine and deduplicate
        combined = priority_files + language_samples + regular_files
        seen = set()
        result = []
        
        for file_path in combined:
            if file_path not in seen and len(result) < count:
                seen.add(file_path)
                result.append(file_path)
        
        return result
    
    def _get_repo_description(self) -> Optional[str]:
        """Try to get repository description from README or other sources."""
        try:
            readme_files = ['README.md', 'README.rst', 'README.txt', 'README']
            repo_path = Path(self.repo_path)
            
            for readme_name in readme_files:
                readme_path = repo_path / readme_name
                if readme_path.exists():
                    with open(readme_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Return first few lines as description
                        lines = content.split('\n')
                        description_lines = []
                        for line in lines[:10]:  # First 10 lines
                            line = line.strip()
                            if line and not line.startswith('#'):
                                description_lines.append(line)
                                if len(description_lines) >= 3:  # Max 3 lines
                                    break
                        return ' '.join(description_lines)[:500]  # Max 500 chars
        except Exception:
            pass
        
        return None
    
    def _get_last_commit_date(self) -> Optional[datetime]:
        """Get the date of the last commit."""
        try:
            last_commit = next(self.git_repo.repo.iter_commits(max_count=1))
            return datetime.fromtimestamp(last_commit.committed_date)
        except Exception:
            return None

    def analyze_with_ai_agent(self, sample_files_count: int = 30, max_important_files: int = 20) -> AIAnalysisResult:
        """
        Perform complete analysis using CrewAI agents to identify important files.
        
        This method combines data preparation with AI Agent web search and classification
        to identify the most important files in the repository for documentation purposes.
        
        Args:
            sample_files_count: Number of sample files to include for context.
            max_important_files: Maximum number of important files to identify.
            
        Returns:
            AIAnalysisResult with identified important files, insights, and recommendations.
        """
        logger.info("Starting AI Agent analysis with CrewAI")
        
        try:
            # Step 1: Prepare AI input data
            ai_input = self.prepare_ai_input(sample_files_count)
            
            # Step 2: Import and initialize CrewAI agent (lazy import to avoid dependency issues)
            try:
                from ..agents.file_analysis_crew import FileAnalysisCrew
            except ImportError as e:
                logger.error(f"CrewAI not available: {e}")
                return self._create_basic_analysis_result(ai_input)
            
            # Step 3: Execute CrewAI analysis
            logger.info("Initializing FileAnalysisCrew for AI-powered file analysis")
            file_analysis_crew = FileAnalysisCrew()
            
            # Step 4: Run the crew analysis
            result = file_analysis_crew.analyze_important_files(
                ai_input=ai_input,
                max_files=max_important_files
            )
            
            logger.info(f"AI Agent analysis completed successfully with {len(result.important_files)} important files identified")
            return result
            
        except Exception as e:
            logger.error(f"AI Agent analysis failed: {e}")
            # Fallback to basic analysis
            return self._create_basic_analysis_result(ai_input)

    def _create_basic_analysis_result(self, ai_input: AIAnalysisInput) -> AIAnalysisResult:
        """
        Create a basic analysis result when CrewAI is not available.
        
        Args:
            ai_input: Prepared AI input data.
            
        Returns:
            Basic AIAnalysisResult with pattern-based file identification.
        """
        from .models import ImportantFile
        
        logger.warning("Creating basic analysis result (CrewAI not available)")
        
        important_files = []
        
        # Use pattern-based identification for common important files
        for file_path in ai_input.sample_files[:15]:
            importance_level = "MEDIUM"
            reasons = ["Identified through pattern analysis"]
            content_type = "General file"
            
            # Pattern-based importance detection
            file_lower = file_path.lower()
            
            if any(pattern in file_lower for pattern in ["main.", "index.", "app.", "__init__", "setup."]):
                importance_level = "CRITICAL"
                reasons = ["Entry point or main application file"]
                content_type = "Application entry point"
            elif any(pattern in file_lower for pattern in ["config", "settings", ".env", "package.json", "requirements", "pom.xml"]):
                importance_level = "HIGH"
                reasons = ["Configuration or dependency file"]
                content_type = "Configuration file"
            elif any(pattern in file_lower for pattern in ["readme", "license", "changelog"]):
                importance_level = "HIGH"
                reasons = ["Documentation file"]
                content_type = "Documentation"
            elif any(pattern in file_lower for pattern in ["test", "spec"]):
                importance_level = "MEDIUM"
                reasons = ["Test file"]
                content_type = "Test file"
            
            important_file = ImportantFile(
                file_path=file_path,
                importance_level=importance_level,
                confidence_score=0.5,  # Lower confidence for pattern-based analysis
                reasons=reasons,
                content_type=content_type,
                estimated_lines=100
            )
            important_files.append(important_file)
        
        return AIAnalysisResult(
            important_files=important_files,
            insights=[
                f"Basic pattern-based analysis completed",
                f"Identified {len(important_files)} potentially important files",
                f"Primary language: {ai_input.primary_language}",
                "For more accurate results, install CrewAI dependencies"
            ],
            recommendations=[
                "Install CrewAI and SerperDev API key for AI-powered analysis",
                "Review pattern-based classifications manually",
                "Focus on CRITICAL and HIGH importance files first"
            ],
            confidence_score=0.4  # Lower confidence for pattern-based analysis
        )