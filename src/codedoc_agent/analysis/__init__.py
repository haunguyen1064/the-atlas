"""Simplified code analysis module for AI Agent integration.

This module provides data preparation and orchestration for AI Agent analysis:
- Data structures for AI input/output
- File pattern definitions for web search
- Language data processing from Git integration
- Simple orchestration for AI Agent workflows
"""

from .models import (
    LanguageInfo,
    AIAnalysisInput,
    ImportantFile,
    AIAnalysisResult,
    ProjectAnalysis
)

from .file_classifier import FilePatternProvider
from .language_analyzer import LanguageDataProcessor
from .code_analyzer import CodeAnalysisOrchestrator

__all__ = [
    # Data models
    'LanguageInfo',
    'AIAnalysisInput',
    'ImportantFile', 
    'AIAnalysisResult',
    'ProjectAnalysis',
    
    # Core components
    'FilePatternProvider',
    'LanguageDataProcessor',
    'CodeAnalysisOrchestrator'
]