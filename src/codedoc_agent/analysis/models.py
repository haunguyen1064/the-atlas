"""Simplified data models for AI Agent integration."""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class LanguageInfo:
    """Information about a programming language detected in the project."""
    name: str
    line_count: int
    file_count: int
    percentage: float
    sample_files: List[str]  # Sample files for this language


@dataclass
class AIAnalysisInput:
    """Input data structure for AI Agent analysis."""
    # Repository information
    repo_url: str
    repo_description: Optional[str]
    
    # Language breakdown (from git_integration)
    languages: Dict[str, LanguageInfo]  # language_name -> LanguageInfo
    primary_language: str
    
    # File structure summary
    total_files: int
    directory_structure: Dict[str, List[str]]  # directory -> files
    
    # Repository metadata
    total_commits: int
    authors_count: int
    last_commit_date: Optional[datetime]


@dataclass
class ImportantFile:
    """AI Agent's classification of an important file."""
    file_path: str
    importance_level: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW"  
    confidence_score: float  # AI's confidence in this classification (0.0 to 1.0)
    reasons: List[str]  # AI's reasons for why this file is important
    content_type: str  # "entry_point", "configuration", "business_logic", etc.
    estimated_lines: int  # Estimated number of lines in the file


@dataclass
class AIAnalysisResult:
    """Result from AI Agent analysis."""
    # Important files identified by AI
    important_files: List[ImportantFile]
    
    # AI insights and recommendations
    insights: List[str]  # Key insights from AI analysis
    recommendations: List[str]  # AI's suggestions for documentation
    confidence_score: float  # Overall confidence in the analysis
    
    # Optional metadata
    analysis_timestamp: Optional[datetime] = None
    project_type: Optional[str] = None  # "web_app", "api", "library", "cli_tool", etc.
    architecture_patterns: Optional[List[str]] = None  # Patterns detected by AI
    frameworks_detected: Optional[List[str]] = None  # Frameworks identified by AI
    entry_point_suggestion: Optional[str] = None  # AI's suggested starting point
    reading_order: Optional[List[str]] = None  # AI's suggested order for reading files
    summary: Optional[str] = None  # AI-generated summary of the project


@dataclass
class ProjectAnalysis:
    """Complete project analysis combining Git data and AI insights."""
    # Input data
    input_data: AIAnalysisInput
    
    # AI analysis results
    ai_analysis: AIAnalysisResult
    
    # Combined insights
    analysis_timestamp: datetime
    analysis_version: str  # Version of the analysis process used