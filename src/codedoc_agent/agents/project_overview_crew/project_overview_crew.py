"""CrewAI-based project overview analysis crew."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Task, Process
from crewai_tools import SerperDevTool
import yaml

from ...analysis.models import AIAnalysisInput
from ...analysis.file_content_reader import AggregatedFileContent

logger = logging.getLogger(__name__)


class ProjectOverviewCrew:
    """CrewAI crew for analyzing project content and generating comprehensive overview."""
    
    def __init__(self):
        """Initialize the project overview crew with agents and tasks."""
        self.config_dir = Path(__file__).parent / "config"
        self.agents_config = self._load_config("agents.yaml")
        self.tasks_config = self._load_config("tasks.yaml")
        
        # Initialize tools
        self.search_tool = SerperDevTool() if os.getenv("SERPER_API_KEY") else None
        
        # Initialize agents
        self.project_analyzer = self._create_project_analyzer_agent()
        self.dependency_analyzer = self._create_dependency_analyzer_agent()
        
    def _load_config(self, filename: str) -> Dict[str, Any]:
        """Load YAML configuration file."""
        config_path = self.config_dir / filename
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config {filename}: {e}")
            return {}
    
    def _create_project_analyzer_agent(self) -> Agent:
        """Create the project analyzer agent."""
        config = self.agents_config.get("project_analyzer_agent", {})
        
        tools = []
        if self.search_tool:
            tools.append(self.search_tool)
        
        return Agent(
            role=config.get("role", "Project Analyzer"),
            goal=config.get("goal", "Analyze project content and architecture"),
            backstory=config.get("backstory", "Expert in project analysis"),
            llm=config.get("llm", "gpt-3.5-turbo"),
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            tools=tools
        )
    
    def _create_dependency_analyzer_agent(self) -> Agent:
        """Create the dependency analyzer agent."""
        config = self.agents_config.get("dependency_analyzer_agent", {})
        
        tools = []
        if self.search_tool:
            tools.append(self.search_tool)
        
        return Agent(
            role=config.get("role", "Dependency Analyzer"),
            goal=config.get("goal", "Analyze dependencies and technology stack"),
            backstory=config.get("backstory", "Expert in dependency analysis"),
            llm=config.get("llm", "gpt-3.5-turbo"),
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            tools=tools
        )
    
    def analyze_project_overview(
        self,
        ai_input: AIAnalysisInput,
        file_content: AggregatedFileContent
    ) -> Dict[str, Any]:
        """
        Analyze project content and generate comprehensive overview.
        
        Args:
            ai_input: AI analysis input with repository metadata.
            file_content: Aggregated content from important files.
            
        Returns:
            Dictionary with project overview analysis results.
        """
        logger.info("Starting project overview analysis with CrewAI")
        
        try:
            # Prepare content for analysis
            file_contents_text = self._prepare_file_contents_for_analysis(file_content)
            
            # Create task inputs
            task_inputs = {
                "repo_url": ai_input.repo_url or "Local repository",
                "primary_language": ai_input.primary_language or "Unknown",
                "languages_list": ", ".join(ai_input.languages.keys()) if ai_input.languages else "Unknown",
                "directory_structure": self._format_directory_structure(ai_input.directory_structure),
                "total_files_analyzed": file_content.successful_reads,
                "file_contents": file_contents_text
            }
            
            # Create tasks
            tasks = self._create_tasks(task_inputs)
            
            # Create and run crew
            crew = Crew(
                agents=[self.project_analyzer, self.dependency_analyzer],
                tasks=tasks,
                process=Process.sequential,
                verbose=True
            )
            
            # Execute analysis
            logger.info("Executing project overview analysis crew")
            result = crew.kickoff()
            
            # Process results
            overview_result = self._process_crew_results(result, task_inputs)
            
            logger.info("Project overview analysis completed successfully")
            return overview_result
            
        except Exception as e:
            logger.error(f"Project overview analysis failed: {e}")
            return self._create_fallback_overview(ai_input, file_content)
    
    def _prepare_file_contents_for_analysis(self, file_content: AggregatedFileContent) -> str:
        """Prepare file contents for AI analysis."""
        content_sections = []
        
        # Group files by importance level
        critical_files = [f for f in file_content.files if f.importance_level == "CRITICAL" and f.is_readable]
        high_files = [f for f in file_content.files if f.importance_level == "HIGH" and f.is_readable]
        medium_files = [f for f in file_content.files if f.importance_level == "MEDIUM" and f.is_readable]
        
        # Add critical files first
        if critical_files:
            content_sections.append("=== CRITICAL FILES ===")
            for file_obj in critical_files:
                content_sections.append(f"\n--- FILE: {file_obj.file_path} ---")
                content_sections.append(f"Importance: {file_obj.importance_level}")
                content_sections.append(f"Type: {file_obj.content_type}")
                content_sections.append(f"Reasons: {', '.join(file_obj.reasons)}")
                content_sections.append("Content:")
                content_sections.append(file_obj.content)
                content_sections.append("--- END FILE ---\n")
        
        # Add high importance files
        if high_files:
            content_sections.append("\n=== HIGH IMPORTANCE FILES ===")
            for file_obj in high_files:
                content_sections.append(f"\n--- FILE: {file_obj.file_path} ---")
                content_sections.append(f"Importance: {file_obj.importance_level}")
                content_sections.append(f"Type: {file_obj.content_type}")
                content_sections.append(f"Reasons: {', '.join(file_obj.reasons)}")
                content_sections.append("Content:")
                content_sections.append(file_obj.content)
                content_sections.append("--- END FILE ---\n")
        
        # Add medium importance files (limit to save space)
        if medium_files:
            content_sections.append("\n=== MEDIUM IMPORTANCE FILES ===")
            for file_obj in medium_files[:5]:  # Limit to first 5 medium files
                content_sections.append(f"\n--- FILE: {file_obj.file_path} ---")
                content_sections.append(f"Importance: {file_obj.importance_level}")
                content_sections.append(f"Type: {file_obj.content_type}")
                content_sections.append("Content:")
                content_sections.append(file_obj.content[:2000])  # Limit content length
                if len(file_obj.content) > 2000:
                    content_sections.append("... (content truncated)")
                content_sections.append("--- END FILE ---\n")
        
        return "\n".join(content_sections)
    
    def _format_directory_structure(self, directory_structure: Dict[str, List[str]]) -> str:
        """Format directory structure for display."""
        if not directory_structure:
            return "No directory structure available"
        
        structure_lines = []
        for directory, files in directory_structure.items():
            if directory == ".":
                structure_lines.append("Root directory:")
            else:
                structure_lines.append(f"{directory}/:")
            
            for file_name in files[:10]:  # Limit files per directory
                structure_lines.append(f"  - {file_name}")
            
            if len(files) > 10:
                structure_lines.append(f"  ... and {len(files) - 10} more files")
            structure_lines.append("")
        
        return "\n".join(structure_lines)
    
    def _create_tasks(self, task_inputs: Dict[str, Any]) -> List[Task]:
        """Create tasks for the crew."""
        tasks = []
        
        # Project content analysis task
        project_analysis_config = self.tasks_config.get("analyze_project_content_task", {})
        project_analysis_task = Task(
            description=project_analysis_config.get("description", "").format(**task_inputs),
            expected_output=project_analysis_config.get("expected_output", "Project analysis"),
            agent=self.project_analyzer
        )
        tasks.append(project_analysis_task)
        
        # Dependency analysis task
        dependency_analysis_config = self.tasks_config.get("analyze_dependencies_and_frameworks_task", {})
        dependency_analysis_task = Task(
            description=dependency_analysis_config.get("description", "").format(**task_inputs),
            expected_output=dependency_analysis_config.get("expected_output", "Dependency analysis"),
            agent=self.dependency_analyzer
        )
        tasks.append(dependency_analysis_task)
        
        # Overview generation task
        overview_config = self.tasks_config.get("generate_project_overview_task", {})
        overview_task = Task(
            description=overview_config.get("description", "").format(
                project_analysis="{project_analysis}",
                dependency_analysis="{dependency_analysis}"
            ),
            expected_output=overview_config.get("expected_output", "Project overview"),
            agent=self.project_analyzer
        )
        tasks.append(overview_task)
        
        return tasks
    
    def _process_crew_results(self, result: Any, task_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process crew execution results."""
        return {
            "overview": str(result),
            "repo_url": task_inputs.get("repo_url"),
            "primary_language": task_inputs.get("primary_language"),
            "total_files_analyzed": task_inputs.get("total_files_analyzed"),
            "analysis_status": "success",
            "analysis_method": "CrewAI Project Overview Analysis"
        }
    
    def _create_fallback_overview(
        self,
        ai_input: AIAnalysisInput,
        file_content: AggregatedFileContent
    ) -> Dict[str, Any]:
        """Create a basic fallback overview when CrewAI fails."""
        overview_lines = [
            f"# Project Overview (Basic Analysis)",
            f"",
            f"**Repository**: {ai_input.repo_url or 'Local repository'}",
            f"**Primary Language**: {ai_input.primary_language or 'Unknown'}",
            f"**Languages**: {', '.join(ai_input.languages.keys()) if ai_input.languages else 'Unknown'}",
            f"**Files Analyzed**: {file_content.successful_reads}/{file_content.total_files}",
            f"",
            f"## File Analysis Summary",
            f"- Critical files: {file_content.critical_files_count}",
            f"- High importance files: {file_content.high_files_count}",
            f"- Medium importance files: {file_content.medium_files_count}",
            f"",
            f"## Readable Files",
        ]
        
        for file_obj in file_content.files:
            if file_obj.is_readable:
                overview_lines.append(f"- {file_obj.file_path} ({file_obj.importance_level})")
        
        overview_lines.extend([
            "",
            "*Note: This is a basic analysis. For detailed project overview, ensure CrewAI dependencies are properly installed.*"
        ])
        
        return {
            "overview": "\n".join(overview_lines),
            "repo_url": ai_input.repo_url,
            "primary_language": ai_input.primary_language,
            "total_files_analyzed": file_content.successful_reads,
            "analysis_status": "fallback",
            "analysis_method": "Basic File Summary"
        }
