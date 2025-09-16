"""CrewAI File Analysis Crew for identifying important files in repositories."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List, Dict, Any
import json
import logging

from codedoc_agent.analysis.models import AIAnalysisInput, ImportantFile, AIAnalysisResult

logger = logging.getLogger(__name__)


@CrewBase
class FileAnalysisCrew:
    """CrewAI crew for analyzing repositories and identifying important files."""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        """Initialize the FileAnalysisCrew."""
        super().__init__()
        logger.info("Initializing FileAnalysisCrew")

    @agent
    def file_analysis_researcher(self) -> Agent:
        """Create the file analysis researcher agent."""
        return Agent(
            config=self.agents_config['file_analysis_researcher'],
            verbose=True,
            tools=[SerperDevTool()],  # Enable web search for research
            allow_delegation=False
        )

    @agent
    def file_importance_classifier(self) -> Agent:
        """Create the file importance classifier agent."""
        return Agent(
            config=self.agents_config['file_importance_classifier'],
            verbose=True,
            allow_delegation=False
        )

    @task
    def research_important_files_task(self) -> Task:
        """Create the research task for finding important files."""
        return Task(
            config=self.tasks_config['research_important_files_task'],
            agent=self.file_analysis_researcher()
        )

    @task
    def classify_file_importance_task(self) -> Task:
        """Create the classification task for ranking file importance."""
        return Task(
            config=self.tasks_config['classify_file_importance_task'],
            agent=self.file_importance_classifier(),
            context=[self.research_important_files_task()]
        )

    @crew
    def crew(self) -> Crew:
        """Create the FileAnalysis crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )

    def analyze_important_files(self, ai_input: AIAnalysisInput, max_files: int = 20) -> AIAnalysisResult:
        """
        Analyze repository and identify important files using CrewAI agents.
        
        Args:
            ai_input: Structured input data prepared by CodeAnalysisOrchestrator
            max_files: Maximum number of important files to identify
            
        Returns:
            AIAnalysisResult with identified important files and analysis insights
        """
        logger.info(f"Starting file analysis for repository: {ai_input.repo_url}")
        
        try:
            # Prepare languages list for agents
            languages_list = ", ".join([
                f"{name} ({info.percentage:.1f}%)" 
                for name, info in ai_input.languages.items()
            ])
            
            # Prepare sample files list
            sample_files_str = "\n".join([
                f"- {file_path}" for file_path in ai_input.sample_files[:30]
            ])
            
            # Execute the crew with structured inputs
            crew_inputs = {
                "repo_url": ai_input.repo_url or "Unknown repository",
                "primary_language": ai_input.primary_language,
                "languages_list": languages_list,
                "repo_description": ai_input.repo_description or "No description available",
                "total_files": ai_input.total_files,
                "sample_files": sample_files_str,
                "max_important_files": max_files,
                "research_findings": ""  # Will be populated by first task
            }
            
            logger.info("Executing CrewAI file analysis crew...")
            result = self.crew().kickoff(inputs=crew_inputs)
            
            # Parse the crew result into ImportantFile objects
            important_files = self._parse_crew_result(result.raw)
            
            # Create insights from the analysis
            insights = self._generate_insights(ai_input, important_files)
            
            # Create final result
            analysis_result = AIAnalysisResult(
                important_files=important_files,
                insights=insights,
                recommendations=self._generate_recommendations(ai_input, important_files),
                confidence_score=self._calculate_confidence_score(important_files)
            )
            
            logger.info(f"File analysis completed. Found {len(important_files)} important files.")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error during CrewAI file analysis: {e}")
            # Return a basic result with fallback logic
            return self._create_fallback_result(ai_input)

    def _parse_crew_result(self, crew_output: str) -> List[ImportantFile]:
        """Parse CrewAI output into ImportantFile objects."""
        important_files = []
        
        try:
            # Try to extract JSON from crew output
            if "```json" in crew_output:
                json_start = crew_output.find("```json") + 7
                json_end = crew_output.find("```", json_start)
                json_content = crew_output[json_start:json_end].strip()
            else:
                # Try to find JSON-like content
                json_content = crew_output
            
            # Parse the JSON
            parsed_data = json.loads(json_content)
            
            # Handle different JSON structures
            if isinstance(parsed_data, list):
                files_data = parsed_data
            elif isinstance(parsed_data, dict) and "files" in parsed_data:
                files_data = parsed_data["files"]
            elif isinstance(parsed_data, dict) and "important_files" in parsed_data:
                files_data = parsed_data["important_files"]
            else:
                files_data = [parsed_data]
            
            # Convert to ImportantFile objects
            for file_data in files_data:
                if isinstance(file_data, dict):
                    important_file = ImportantFile(
                        file_path=file_data.get("file_path", ""),
                        importance_level=file_data.get("importance_level", "MEDIUM"),
                        confidence_score=float(file_data.get("confidence_score", 0.7)),
                        reasons=file_data.get("reasons", []),
                        content_type=file_data.get("content_type", ""),
                        estimated_lines=int(file_data.get("estimated_lines", 100))
                    )
                    important_files.append(important_file)
                    
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"Failed to parse CrewAI output as JSON: {e}")
            # Fallback: try to extract file paths from text
            important_files = self._extract_files_from_text(crew_output)
        
        return important_files

    def _extract_files_from_text(self, text: str) -> List[ImportantFile]:
        """Fallback method to extract file information from text output."""
        important_files = []
        lines = text.split('\n')
        
        current_file = None
        current_importance = "MEDIUM"
        current_reasons = []
        
        for line in lines:
            line = line.strip()
            
            # Look for file paths (common patterns)
            if any(ext in line for ext in ['.py', '.js', '.ts', '.java', '.go', '.cpp', '.c', '.rb']):
                if '/' in line or '\\' in line:
                    # Extract file path
                    words = line.split()
                    for word in words:
                        if any(ext in word for ext in ['.py', '.js', '.ts', '.java', '.go']):
                            current_file = word.strip(':`"\'(),')
                            break
                            
            # Look for importance indicators
            if any(word in line.upper() for word in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']):
                for importance in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
                    if importance in line.upper():
                        current_importance = importance
                        break
            
            # Look for reasons
            if line.startswith('-') or line.startswith('*') or 'because' in line.lower():
                current_reasons.append(line.strip('- *'))
            
            # When we have enough info, create ImportantFile
            if current_file and (len(current_reasons) > 0 or line == '' or line.startswith('---')):
                important_file = ImportantFile(
                    file_path=current_file,
                    importance_level=current_importance,
                    confidence_score=0.6,  # Lower confidence for text parsing
                    reasons=current_reasons.copy(),
                    content_type="Extracted from text analysis",
                    estimated_lines=150
                )
                important_files.append(important_file)
                current_file = None
                current_reasons = []
                current_importance = "MEDIUM"
        
        return important_files

    def _generate_insights(self, ai_input: AIAnalysisInput, important_files: List[ImportantFile]) -> List[str]:
        """Generate insights based on the file analysis."""
        insights = []
        
        # Language-based insights
        if ai_input.primary_language:
            insights.append(f"Primary language is {ai_input.primary_language} with {ai_input.languages[ai_input.primary_language].percentage:.1f}% coverage")
        
        # File distribution insights
        critical_files = [f for f in important_files if f.importance_level == "CRITICAL"]
        high_files = [f for f in important_files if f.importance_level == "HIGH"]
        
        if critical_files:
            insights.append(f"Identified {len(critical_files)} critical files essential for understanding the project")
        if high_files:
            insights.append(f"Found {len(high_files)} high-importance files containing key business logic")
        
        # Confidence insights
        avg_confidence = sum(f.confidence_score for f in important_files) / len(important_files) if important_files else 0
        insights.append(f"Average classification confidence: {avg_confidence:.1%}")
        
        return insights

    def _generate_recommendations(self, ai_input: AIAnalysisInput, important_files: List[ImportantFile]) -> List[str]:
        """Generate recommendations based on the analysis."""
        recommendations = []
        
        # Documentation priority recommendations
        critical_files = [f for f in important_files if f.importance_level == "CRITICAL"]
        if critical_files:
            recommendations.append("Start documentation with critical files: " + ", ".join([f.file_path for f in critical_files[:3]]))
        
        # Language-specific recommendations
        if ai_input.primary_language:
            if ai_input.primary_language.lower() == "python":
                recommendations.append("Focus on documenting main modules, __init__.py files, and configuration files")
            elif ai_input.primary_language.lower() in ["javascript", "typescript"]:
                recommendations.append("Prioritize documenting index.js/ts, package.json, and main component files")
            elif ai_input.primary_language.lower() == "java":
                recommendations.append("Document main classes, interfaces, and configuration files first")
        
        # Project structure recommendations
        config_files = [f for f in important_files if "config" in f.file_path.lower() or f.content_type and "config" in f.content_type.lower()]
        if config_files:
            recommendations.append("Document configuration files to explain project setup and dependencies")
        
        return recommendations

    def _calculate_confidence_score(self, important_files: List[ImportantFile]) -> float:
        """Calculate overall confidence score for the analysis."""
        if not important_files:
            return 0.0
        
        # Average individual file confidence scores
        avg_confidence = sum(f.confidence_score for f in important_files) / len(important_files)
        
        # Bonus for having critical files identified
        critical_count = len([f for f in important_files if f.importance_level == "CRITICAL"])
        critical_bonus = min(critical_count * 0.1, 0.2)  # Up to 20% bonus
        
        return min(avg_confidence + critical_bonus, 1.0)

    def _create_fallback_result(self, ai_input: AIAnalysisInput) -> AIAnalysisResult:
        """Create a basic fallback result when CrewAI analysis fails."""
        logger.warning("Creating fallback result due to CrewAI analysis failure")
        
        # Create basic important files based on sample files and patterns
        important_files = []
        
        # Look for common important file patterns in sample files
        for file_path in ai_input.sample_files[:10]:
            importance = "MEDIUM"
            reasons = ["Identified as potentially important file"]
            
            # Simple pattern matching for importance
            if any(pattern in file_path.lower() for pattern in ["main", "index", "app", "__init__"]):
                importance = "CRITICAL"
                reasons = ["Entry point or main application file"]
            elif any(pattern in file_path.lower() for pattern in ["config", "settings", "setup"]):
                importance = "HIGH"
                reasons = ["Configuration or setup file"]
            
            important_file = ImportantFile(
                file_path=file_path,
                importance_level=importance,
                confidence_score=0.4,  # Lower confidence for fallback
                reasons=reasons,
                content_type="Fallback analysis",
                estimated_lines=100
            )
            important_files.append(important_file)
        
        return AIAnalysisResult(
            important_files=important_files,
            insights=["Fallback analysis due to CrewAI processing error"],
            recommendations=["Manual review recommended for accurate file classification"],
            confidence_score=0.3
        )