"""Simple orchestrator for preparing AI Agent input data."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from dataclasses import asdict, is_dataclass

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
    
    def prepare_ai_input(self) -> AIAnalysisInput:
        """Prepare input data for AI Agent analysis.
            
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
            
            # Repository metadata
            total_commits=repo_info.total_commits,
            authors_count=len(repo_info.authors),
            last_commit_date=self._get_last_commit_date()
        )
        
        # Log full ai_input details for debugging/inspection
        self._log_ai_input(ai_input)
        
        logger.info(f"Prepared AI input: {len(languages)} languages, {len(all_files)} files")
        return ai_input
    
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
        ai_input = self.prepare_ai_input()
        
        context_lines = [
            f"Repository: {ai_input.repo_url}",
            f"Primary Language: {ai_input.primary_language}",
            "",
            self.language_processor.create_language_summary_for_ai(ai_input.languages),
            "",
        ]
        
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

    def _log_ai_input(self, ai_input: Any) -> None:
        """Log full AIAnalysisInput as JSON for inspection."""
        try:
            if is_dataclass(ai_input):
                payload = asdict(ai_input)
            elif hasattr(ai_input, "model_dump"):
                payload = ai_input.model_dump()  # pydantic v2
            elif hasattr(ai_input, "dict") and callable(getattr(ai_input, "dict")):
                payload = ai_input.dict()  # pydantic v1
            elif hasattr(ai_input, "__dict__"):
                payload = ai_input.__dict__
            else:
                payload = str(ai_input)
            logger.info("AI input details:\n%s", json.dumps(payload, default=str, ensure_ascii=False, indent=2))
        except Exception:
            logger.info("AI input details (raw): %s", ai_input)

    def analyze_with_ai_agent(self, max_important_files: int = 20) -> AIAnalysisResult:
        """
        Perform complete analysis using CrewAI agents to identify important files.
        
        This method combines data preparation with AI Agent web search and classification
        to identify the most important files in the repository for documentation purposes.
        
        Args:
            max_important_files: Maximum number of important files to identify.
            
        Returns:
            AIAnalysisResult with identified important files, insights, and recommendations.
        """
        logger.info("Starting AI Agent analysis with CrewAI")
        
        try:
            # Step 1: Prepare AI input data
            ai_input = self.prepare_ai_input()
            
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