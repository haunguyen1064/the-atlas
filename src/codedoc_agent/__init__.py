"""CodeDoc AI Agent package for analyzing source code and generating documentation."""

__version__ = "0.1.0"

# Export main components
from .tools.git_integration import GitRepository, GitRepositoryTool, RepositoryInfo
from .analysis import (
    CodeAnalysisOrchestrator, FilePatternProvider, LanguageDataProcessor,
    AIAnalysisInput, ImportantFile, AIAnalysisResult, ProjectAnalysis
)

__all__ = [
    'GitRepository', 'GitRepositoryTool', 'RepositoryInfo',
    'CodeAnalysisOrchestrator', 'FilePatternProvider', 'LanguageDataProcessor',
    'AIAnalysisInput', 'ImportantFile', 'AIAnalysisResult', 'ProjectAnalysis'
]