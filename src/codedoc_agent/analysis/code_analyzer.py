"""Simple orchestrator for preparing AI Agent input data."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
from dataclasses import asdict, is_dataclass

from .models import AIAnalysisInput, AIAnalysisResult, LanguageInfo, ProjectOverviewResult, ImportantFile
from .file_classifier import FilePatternProvider
from .language_analyzer import LanguageDataProcessor
from .file_content_reader import FileContentReader, AggregatedFileContent
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
        self.file_content_reader = FileContentReader(self.repo_path)
    
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

    def analyze_project_overview(self, important_files: List[ImportantFile]) -> ProjectOverviewResult:
        """
        Analyze project content from important files to generate comprehensive overview.
        
        Args:
            important_files: List of ImportantFile objects to analyze.
            
        Returns:
            ProjectOverviewResult with comprehensive project overview.
        """
        logger.info(f"Starting project overview analysis for {len(important_files)} important files")
        
        try:
            # Step 1: Read content from important files
            file_content = self.file_content_reader.read_important_files(important_files)
            
            # Log file reading summary
            logger.info(f"File reading summary: {file_content.successful_reads}/{file_content.total_files} files read successfully")
            
            # Step 2: Prepare AI input
            ai_input = self.prepare_ai_input()
            
            # Step 3: Try CrewAI project overview analysis
            try:
                from ..agents.project_overview_crew import ProjectOverviewCrew
                
                logger.info("Using CrewAI for project overview analysis")
                overview_crew = ProjectOverviewCrew()
                overview_result_dict = overview_crew.analyze_project_overview(ai_input, file_content)
                
                # Convert to ProjectOverviewResult
                overview_result = ProjectOverviewResult(
                    overview=overview_result_dict.get("overview", ""),
                    repo_url=overview_result_dict.get("repo_url"),
                    primary_language=overview_result_dict.get("primary_language"),
                    total_files_analyzed=overview_result_dict.get("total_files_analyzed", 0),
                    analysis_status=overview_result_dict.get("analysis_status", "success"),
                    analysis_method=overview_result_dict.get("analysis_method", "CrewAI")
                )
                
                logger.info("Project overview analysis completed successfully with CrewAI")
                return overview_result
                
            except ImportError as e:
                logger.warning(f"CrewAI not available for project overview: {e}")
                return self._create_basic_project_overview(ai_input, file_content)
            
        except Exception as e:
            logger.error(f"Project overview analysis failed: {e}")
            # Fallback to basic overview
            ai_input = self.prepare_ai_input()
            return self._create_basic_project_overview(ai_input, None)

    def _create_basic_project_overview(
        self, 
        ai_input: AIAnalysisInput, 
        file_content: Optional[AggregatedFileContent] = None
    ) -> ProjectOverviewResult:
        """
        Create a basic project overview when CrewAI is not available.
        
        Args:
            ai_input: AI analysis input data.
            file_content: Optional file content data.
            
        Returns:
            Basic ProjectOverviewResult.
        """
        logger.info("Creating basic project overview")
        
        overview_lines = [
            f"# Project Overview (Basic Analysis)",
            f"",
            f"## Repository Information",
            f"**URL**: {ai_input.repo_url or 'Local repository'}",
            f"**Primary Language**: {ai_input.primary_language or 'Unknown'}",
            f"**Total Files**: {ai_input.total_files}",
            f"**Total Commits**: {ai_input.total_commits}",
            f"**Contributors**: {ai_input.authors_count}",
            f"",
            f"## Languages Used",
        ]
        
        if ai_input.languages:
            for lang_name, lang_info in ai_input.languages.items():
                overview_lines.append(f"- **{lang_name}**: {lang_info.line_count:,} lines ({lang_info.percentage:.1f}%)")
        else:
            overview_lines.append("- No language information available")
        
        overview_lines.extend([
            "",
            f"## Project Structure",
            "### Directory Overview",
        ])
        
        if ai_input.directory_structure:
            for directory, files in list(ai_input.directory_structure.items())[:10]:
                dir_name = "Root directory" if directory == "." else directory
                overview_lines.append(f"- **{dir_name}**: {len(files)} files")
        
        if file_content:
            overview_lines.extend([
                "",
                f"## File Analysis Summary",
                f"- **Total files analyzed**: {file_content.successful_reads}/{file_content.total_files}",
                f"- **Critical files**: {file_content.critical_files_count}",
                f"- **High importance files**: {file_content.high_files_count}",
                f"- **Medium importance files**: {file_content.medium_files_count}",
                f"- **Total lines analyzed**: {file_content.total_lines:,}",
                "",
                f"### Successfully Analyzed Files",
            ])
            
            for file_obj in file_content.files[:15]:  # Show first 15 files
                if file_obj.is_readable:
                    overview_lines.append(f"- `{file_obj.file_path}` ({file_obj.importance_level}) - {file_obj.content_type}")
        
        overview_lines.extend([
            "",
            "## Notes",
            "This is a basic analysis generated from repository metadata and file structure.",
            "For detailed project analysis including dependencies, frameworks, and architecture,",
            "install CrewAI dependencies and configure API keys for enhanced analysis.",
        ])
        
        return ProjectOverviewResult(
            overview="\n".join(overview_lines),
            repo_url=ai_input.repo_url,
            primary_language=ai_input.primary_language,
            total_files_analyzed=file_content.successful_reads if file_content else 0,
            analysis_status="basic",
            analysis_method="Basic Repository Analysis"
        )

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
        
        # Get all files from directory structure
        all_files = self._flatten_file_structure(ai_input.directory_structure)
        
        # Use pattern-based identification for common important files
        for file_path in all_files[:15]:
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