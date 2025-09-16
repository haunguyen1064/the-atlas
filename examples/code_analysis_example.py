"""Example usage of the simplified Code Analysis Module for AI Agent integration."""

import logging
from pathlib import Path
from codedoc_agent.tools.git_integration import GitRepository
from codedoc_agent.analysis import CodeAnalysisOrchestrator, FilePatternProvider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def prepare_ai_analysis_example(repo_path: str):
    """Example of preparing data for AI Agent analysis."""
    
    print("🤖 CodeDoc AI Agent - Data Preparation Example")
    print("=" * 55)
    
    try:
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
            
            # Prepare AI input data
            print("\n� Preparing AI Analysis Input...")
            print("-" * 35)
            ai_input = orchestrator.prepare_ai_input(sample_files_count=30)
            
            # Display prepared data
            print(f"Repository: {ai_input.repo_url}")
            print(f"Primary Language: {ai_input.primary_language}")
            print(f"Total Languages: {len(ai_input.languages)}")
            print(f"Total Files: {ai_input.total_files}")
            print(f"Sample Files: {len(ai_input.sample_files)}")
            print(f"Authors Count: {ai_input.authors_count}")
            print(f"Total Commits: {ai_input.total_commits}")
            
            if ai_input.repo_description:
                print(f"Description: {ai_input.repo_description[:100]}...")
            
            # Display language breakdown
            print(f"\n🗣️ Language Breakdown:")
            for lang_name, lang_info in sorted(ai_input.languages.items(), 
                                             key=lambda x: x[1].line_count, reverse=True):
                print(f"  • {lang_name}: {lang_info.percentage:.1f}% "
                      f"({lang_info.line_count:,} lines, {lang_info.file_count} files)")
                if lang_info.sample_files:
                    sample_str = ", ".join(lang_info.sample_files[:3])
                    print(f"    Sample files: {sample_str}")
            
            # Display sample files for AI context
            print(f"\n📄 Sample Files for AI Context:")
            current_dir = ""
            for file_path in ai_input.sample_files[:15]:  # Show first 15
                file_dir = str(Path(file_path).parent) if '/' in file_path else "."
                if file_dir != current_dir:
                    print(f"  📁 {file_dir}/")
                    current_dir = file_dir
                print(f"    📄 {Path(file_path).name}")
            
            # Show AI search context
            print(f"\n� AI Search Context Preview:")
            print("-" * 30)
            search_context = orchestrator.create_ai_search_context()
            print(search_context[:800] + "..." if len(search_context) > 800 else search_context)
            
            print(f"\n✅ AI input preparation completed!")
            print(f"Ready for AI Agent web search and analysis.")
            
    except Exception as e:
        print(f"❌ Error during preparation: {e}")
        logger.exception("Preparation failed")


def show_language_patterns_example():
    """Example of getting language patterns for AI web search."""
    
    print("\n🎯 Language Patterns for AI Search")
    print("=" * 35)
    
    pattern_provider = FilePatternProvider()
    
    # Example languages
    languages = ['Python', 'JavaScript', 'TypeScript', 'Java', 'Go']
    
    for language in languages:
        print(f"\n�️ {language} Patterns:")
        patterns = pattern_provider.get_all_patterns_for_language(language)
        
        print(f"  Entry Points: {', '.join(patterns['entry_points'][:5])}")
        if patterns['framework_files']:
            frameworks = list(patterns['framework_files'].keys())[:3]
            print(f"  Frameworks: {', '.join(frameworks)}")
        
        print(f"  Config Patterns: {len(patterns['config_files'])} patterns")
        print(f"  Test Patterns: {len(patterns['test_files'])} patterns")


def demo_top_languages_analysis(repo_path: str):
    """Example of getting top languages for AI focus."""
    
    print("\n� Top Languages Analysis")
    print("=" * 28)
    
    try:
        with GitRepository(repo_path) as git_repo:
            if Path(repo_path).is_dir():
                git_repo.open(repo_path)
            else:
                git_repo.clone()
            
            orchestrator = CodeAnalysisOrchestrator(git_repo)
            
            # Get top 5 languages
            top_languages = orchestrator.get_top_languages_for_search(count=5)
            
            print("Top languages for AI Agent to focus on:")
            for rank, (lang_name, lang_info) in enumerate(top_languages.items(), 1):
                print(f"{rank}. {lang_name}: {lang_info.percentage:.1f}% "
                      f"({lang_info.line_count:,} lines)")
                
                # Show sample files for this language
                if lang_info.sample_files:
                    samples = ", ".join(lang_info.sample_files[:3])
                    print(f"   Key files: {samples}")
    
    except Exception as e:
        print(f"❌ Error during top languages analysis: {e}")


if __name__ == "__main__":
    # Example 1: Prepare data for AI Agent analysis
    current_project = "."
    prepare_ai_analysis_example(current_project)
    
    # Example 2: Show language patterns for AI search
    show_language_patterns_example()
    
    # Example 3: Analyze top languages for AI focus
    demo_top_languages_analysis(current_project)
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps:")
    print("1. Use AIAnalysisInput data for CrewAI Agent web search")
    print("2. AI Agent searches for language-specific best practices")
    print("3. AI Agent identifies important files based on web research")
    print("4. AI Agent creates ImportantFile classifications")
    print("5. Generate AIAnalysisResult with insights and recommendations")
    print("=" * 60)