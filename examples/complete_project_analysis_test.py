"""Example usage of CodeDoc AI Agent for complete project analysis with overview generation."""

import logging
import os
from pathlib import Path
from codedoc_agent.tools.git_integration import GitRepository
from codedoc_agent.analysis import CodeAnalysisOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()  # Load environment variables


def test_complete_project_analysis(repo_path: str):
    """Test complete project analysis including project overview generation."""
    
    print("🚀 CodeDoc AI Agent - Complete Project Analysis Test")
    print("=" * 60)
    
    try:
        # Check if required environment variables are set
        if not os.getenv('SERPER_API_KEY'):
            print("⚠️  Warning: SERPER_API_KEY not set. Web search functionality will be limited.")
        
        if not os.getenv('GEMINI_API_KEY') and not os.getenv('GOOGLE_API_KEY'):
            print("⚠️  Warning: GEMINI_API_KEY not set. AI analysis may not work optimally.")
        
        # Initialize Git repository
        with GitRepository(repo_path) as git_repo:
            if Path(repo_path).is_dir():
                print(f"📁 Analyzing local repository: {repo_path}")
                git_repo.open()  # Open existing local repository
            else:
                print(f"📥 Cloning repository: {repo_path}")
                git_repo.clone()  # Clone remote repository
            
            # Initialize Code Analysis Orchestrator
            orchestrator = CodeAnalysisOrchestrator(git_repo)
            
            print("\n🔍 Step 1: Identifying Important Files...")
            print("-" * 45)
            
            # Step 1: Identify important files
            analysis_result = orchestrator.analyze_with_ai_agent(
                max_important_files=15
            )
            
            print(f"✅ Important Files Identified: {len(analysis_result.important_files)}")
            print(f"Overall Confidence: {analysis_result.confidence_score:.1%}")
            
            # Display important files summary
            critical_files = [f for f in analysis_result.important_files if f.importance_level == "CRITICAL"]
            high_files = [f for f in analysis_result.important_files if f.importance_level == "HIGH"]
            medium_files = [f for f in analysis_result.important_files if f.importance_level == "MEDIUM"]
            
            print(f"\n📊 Important Files Summary:")
            print(f"  🔴 Critical: {len(critical_files)} files")
            print(f"  🟡 High: {len(high_files)} files") 
            print(f"  🟢 Medium: {len(medium_files)} files")
            
            if critical_files:
                print(f"\n🔴 Critical Files:")
                for file_obj in critical_files:
                    print(f"  - {file_obj.file_path} ({file_obj.content_type})")
                    print(f"    Reasons: {', '.join(file_obj.reasons[:2])}")
            
            print("\n🔬 Step 2: Generating Project Overview...")
            print("-" * 45)
            
            # Step 2: Generate project overview from important files
            overview_result = orchestrator.analyze_project_overview(analysis_result.important_files)
            
            print(f"✅ Project Overview Generated!")
            print(f"Analysis Method: {overview_result.analysis_method}")
            print(f"Files Analyzed: {overview_result.total_files_analyzed}")
            print(f"Status: {overview_result.analysis_status}")
            
            print("\n📄 Project Overview:")
            print("=" * 60)
            print(overview_result.overview)
            print("=" * 60)
            
            # Step 3: Save results to files
            output_dir = Path("./output")
            output_dir.mkdir(exist_ok=True)
            
            # Save important files list
            important_files_path = output_dir / "important_files.md"
            with open(important_files_path, 'w', encoding='utf-8') as f:
                f.write("# Important Files Analysis\n\n")
                f.write(f"**Analysis Confidence**: {analysis_result.confidence_score:.1%}\n\n")
                
                for importance_level in ["CRITICAL", "HIGH", "MEDIUM"]:
                    level_files = [f for f in analysis_result.important_files if f.importance_level == importance_level]
                    if level_files:
                        f.write(f"## {importance_level} Files\n\n")
                        for file_obj in level_files:
                            f.write(f"### `{file_obj.file_path}`\n")
                            f.write(f"- **Type**: {file_obj.content_type}\n")
                            f.write(f"- **Confidence**: {file_obj.confidence_score:.1%}\n")
                            f.write(f"- **Reasons**: {', '.join(file_obj.reasons)}\n\n")
            
            # Save project overview
            overview_path = output_dir / "project_overview.md"
            with open(overview_path, 'w', encoding='utf-8') as f:
                f.write(overview_result.overview)
            
            print(f"\n💾 Results saved to:")
            print(f"  - {important_files_path}")
            print(f"  - {overview_path}")
            
            # Display insights and recommendations
            if analysis_result.insights:
                print(f"\n💡 Key Insights:")
                for insight in analysis_result.insights:
                    print(f"  • {insight}")
            
            if analysis_result.recommendations:
                print(f"\n📋 Recommendations:")
                for recommendation in analysis_result.recommendations:
                    print(f"  • {recommendation}")
            
    except Exception as e:
        print(f"❌ Error during complete project analysis: {e}")
        logger.exception("Complete project analysis failed")


def test_project_overview_only(repo_path: str):
    """Test project overview generation with manually specified important files."""
    
    print("🔬 CodeDoc AI Agent - Project Overview Only Test")
    print("=" * 55)
    
    try:
        from codedoc_agent.analysis.models import ImportantFile
        
        # Define some important files manually for testing
        test_important_files = [
            ImportantFile(
                file_path="pyproject.toml",
                importance_level="CRITICAL",
                confidence_score=0.9,
                reasons=["Project configuration and dependencies"],
                content_type="Configuration file",
                estimated_lines=50
            ),
            ImportantFile(
                file_path="src/codedoc_agent/main.py",
                importance_level="CRITICAL", 
                confidence_score=0.95,
                reasons=["Main entry point of the application"],
                content_type="Application entry point",
                estimated_lines=150
            ),
            ImportantFile(
                file_path="README.md",
                importance_level="HIGH",
                confidence_score=0.8,
                reasons=["Project documentation"],
                content_type="Documentation",
                estimated_lines=100
            )
        ]
        
        with GitRepository(repo_path) as git_repo:
            if Path(repo_path).is_dir():
                print(f"📁 Analyzing local repository: {repo_path}")
                git_repo.open()  # Open existing local repository
            else:
                print(f"📥 Cloning repository: {repo_path}")
                git_repo.clone()  # Clone remote repository
            
            orchestrator = CodeAnalysisOrchestrator(git_repo)
            
            print(f"\n🔬 Generating Project Overview from {len(test_important_files)} important files...")
            
            # Generate project overview
            overview_result = orchestrator.analyze_project_overview(test_important_files)
            
            print(f"✅ Project Overview Generated!")
            print(f"Method: {overview_result.analysis_method}")
            print(f"Files Analyzed: {overview_result.total_files_analyzed}")
            
            print("\n📄 Project Overview:")
            print("=" * 60)
            print(overview_result.overview)
            print("=" * 60)
            
    except Exception as e:
        print(f"❌ Error during project overview test: {e}")
        logger.exception("Project overview test failed")


if __name__ == "__main__":
    print("🎯 Running Complete Project Analysis Tests")
    print("=" * 45)
    
    current_project = "https://github.com/haunguyen1064/Smart-parking-app"
    
    # Test 1: Complete analysis (important files + project overview)
    test_complete_project_analysis(current_project)
