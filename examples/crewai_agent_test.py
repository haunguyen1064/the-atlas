"""Example usage of CrewAI Agent for file analysis and importance identification."""

import logging
import os
from pathlib import Path
from codedoc_agent.tools.git_integration import GitRepository
from codedoc_agent.analysis import CodeAnalysisOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()  # Add this line if missing


def test_crewai_file_analysis(repo_path: str):
    """Test CrewAI agent for file analysis on a repository."""
    
    print("🤖 CodeDoc AI Agent - CrewAI File Analysis Test")
    print("=" * 55)
    
    try:
        # Check if required environment variables are set
        if not os.getenv('SERPER_API_KEY'):
            print("⚠️  Warning: SERPER_API_KEY not set. Web search functionality will be limited.")
        
        # if not os.getenv('OPENAI_API_KEY'):
            # print("⚠️  Warning: OPENAI_API_KEY not set. AI analysis may not work.")
        
        # Initialize Git repository
        with GitRepository(repo_path) as git_repo:
            if Path(repo_path).is_dir():
                # Local repository
                local_path = git_repo.open(repo_path)
                print(f"📁 Opened local repository: {local_path}")
            else:
                # Remote repository
                local_path = git_repo.clone()
                print(f"📥 Cloned repository to: {local_path}")
            
            # Initialize Code Analysis Orchestrator
            orchestrator = CodeAnalysisOrchestrator(git_repo)
            
            print("\n🔬 Starting AI Agent Analysis with CrewAI...")
            print("-" * 45)
            
            # Perform AI Agent analysis
            analysis_result = orchestrator.analyze_with_ai_agent(
                max_important_files=15
            )
            
            # Display results
            print(f"\n✅ AI Agent Analysis Completed!")
            print(f"Overall Confidence: {analysis_result.confidence_score:.1%}")
            print(f"Important Files Found: {len(analysis_result.important_files)}")
            
            # Display important files by importance level
            critical_files = [f for f in analysis_result.important_files if f.importance_level == "CRITICAL"]
            high_files = [f for f in analysis_result.important_files if f.importance_level == "HIGH"]
            medium_files = [f for f in analysis_result.important_files if f.importance_level == "MEDIUM"]
            
            if critical_files:
                print(f"\n🔥 Critical Files ({len(critical_files)}):")
                for file in critical_files:
                    print(f"  📄 {file.file_path}")
                    print(f"     Confidence: {file.confidence_score:.1%}")
                    print(f"     Type: {file.content_type}")
                    if file.reasons:
                        print(f"     Reason: {file.reasons[0]}")
                    print()
            
            if high_files:
                print(f"\n⭐ High Importance Files ({len(high_files)}):")
                for file in high_files[:5]:  # Show first 5
                    print(f"  📄 {file.file_path}")
                    print(f"     Confidence: {file.confidence_score:.1%}")
                    if file.reasons:
                        print(f"     Reason: {file.reasons[0]}")
                    print()
            
            if medium_files:
                print(f"\n📋 Medium Importance Files ({len(medium_files)}):")
                for file in medium_files[:3]:  # Show first 3
                    print(f"  📄 {file.file_path} (Confidence: {file.confidence_score:.1%})")
            
            # Display insights
            if analysis_result.insights:
                print(f"\n💡 Analysis Insights:")
                for insight in analysis_result.insights:
                    print(f"  • {insight}")
            
            # Display recommendations
            if analysis_result.recommendations:
                print(f"\n🎯 Recommendations:")
                for recommendation in analysis_result.recommendations:
                    print(f"  • {recommendation}")
            
            print(f"\n📊 File Importance Summary:")
            print(f"  Critical: {len(critical_files)} files")
            print(f"  High: {len(high_files)} files")
            print(f"  Medium: {len(medium_files)} files")
            print(f"  Total: {len(analysis_result.important_files)} files")
            
    except Exception as e:
        print(f"❌ Error during CrewAI analysis: {e}")
        logger.exception("CrewAI analysis failed")


def test_basic_vs_ai_analysis(repo_path: str):
    """Compare basic pattern analysis vs AI agent analysis."""
    
    print("\n🔍 Comparison: Basic Pattern vs AI Agent Analysis")
    print("=" * 55)
    
    try:
        with GitRepository(repo_path) as git_repo:
            if Path(repo_path).is_dir():
                git_repo.open(repo_path)
            else:
                git_repo.clone()
            
            orchestrator = CodeAnalysisOrchestrator(git_repo)
            
            # Get basic AI input for comparison
            ai_input = orchestrator.prepare_ai_input()
            
            print(f"\n📋 Repository Overview:")
            print(f"  Repository: {ai_input.repo_url or 'Local repository'}")
            print(f"  Primary Language: {ai_input.primary_language}")
            print(f"  Total Files: {ai_input.total_files}")
            
            # Show language breakdown
            print(f"\n🗣️ Language Distribution:")
            for lang_name, lang_info in sorted(ai_input.languages.items(), 
                                             key=lambda x: x[1].percentage, reverse=True):
                print(f"  • {lang_name}: {lang_info.percentage:.1f}% ({lang_info.file_count} files)")
            
            # Get top languages for AI focus
            top_languages = orchestrator.get_top_languages_for_search(count=3)
            print(f"\n🏆 Top Languages for AI Agent Focus:")
            
            print(f"\n🔬 Running AI Agent Analysis...")
            
            # Run AI agent analysis
            ai_result = orchestrator.analyze_with_ai_agent(max_important_files=10)
            
            print(f"\n🤖 AI Agent Results:")
            print(f"  Confidence: {ai_result.confidence_score:.1%}")
            print(f"  Critical Files: {len([f for f in ai_result.important_files if f.importance_level == 'CRITICAL'])}")
            print(f"  High Files: {len([f for f in ai_result.important_files if f.importance_level == 'HIGH'])}")
            
            # Show top 5 AI-identified files
            print(f"\n🎯 Top AI-Identified Important Files:")
            for i, file in enumerate(ai_result.important_files[:5], 1):
                print(f"  {i}. {file.file_path} ({file.importance_level})")
                if file.reasons:
                    print(f"     → {file.reasons[0]}")
    
    except Exception as e:
        print(f"❌ Error during comparison analysis: {e}")


def test_language_specific_analysis():
    """Test language-specific pattern analysis."""
    
    print("\n🗣️ Language-Specific Pattern Analysis")
    print("=" * 40)
    
    from codedoc_agent.analysis.file_classifier import FilePatternProvider
    
    pattern_provider = FilePatternProvider()
    
    # Test common languages
    test_languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust']
    
    for language in test_languages:
        print(f"\n📝 {language} Important File Patterns:")
        patterns = pattern_provider.get_all_patterns_for_language(language)
        
        print(f"  Entry Points: {', '.join(patterns['entry_points'][:4])}")
        
        if patterns['framework_files']:
            frameworks = list(patterns['framework_files'].keys())[:2]
            print(f"  Common Frameworks: {', '.join(frameworks)}")
        
        print(f"  Config Files: {len(patterns['config_files'])} patterns")
        print(f"  Test Files: {len(patterns['test_files'])} patterns")


if __name__ == "__main__":
    # Test 1: Full CrewAI analysis on current project
    print("🚀 Running CrewAI Agent Tests")
    print("=" * 35)
    
    current_project = "."
    test_crewai_file_analysis(current_project)
    
    # Test 2: Compare basic vs AI analysis
    test_basic_vs_ai_analysis(current_project)
    
    # Test 3: Language patterns for AI search
    # test_language_specific_analysis()