"""Main entry point for CodeDoc AI Agent."""

import click
import logging
from typing import Optional
from pathlib import Path

from .tools import GitRepository, GitRepositoryTool, RepositoryInfo


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.command()
@click.option('--repo-url', help='Repository URL to analyze')
@click.option('--repo-path', help='Local repository path to analyze')
@click.option('--output-dir', default='./docs', help='Output directory for documentation')
@click.option('--branch', help='Specific branch to analyze (for remote repositories)')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def cli(repo_url: Optional[str], repo_path: Optional[str], output_dir: str, 
        branch: Optional[str], verbose: bool):
    """CodeDoc AI Agent - Analyze source code and generate documentation."""
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if not repo_url and not repo_path:
        click.echo("Please provide either --repo-url or --repo-path")
        return
    
    # Initialize Git repository tool
    git_tool = GitRepositoryTool()
    
    try:
        # Handle repository input
        if repo_url:
            click.echo(f"Cloning repository: {repo_url}")
            if branch:
                click.echo(f"Using branch: {branch}")
            
            # Clone or update repository using cache
            local_path = git_tool.clone_repository(repo_url, branch)
            click.echo(f"Repository available at: {local_path}")
            
        else:
            click.echo(f"Analyzing local repository: {repo_path}")
            local_path = repo_path
        
        # Analyze repository
        click.echo("Analyzing repository structure and history...")
        repo_info = git_tool.analyze_repository(local_path)
        
        # Display repository information
        display_repository_info(repo_info)
        
        # Get recent changes
        recent_commits = git_tool.get_recent_changes(local_path, count=5)
        display_recent_commits(recent_commits)
        
        # Prepare output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"Documentation will be generated in: {output_path.absolute()}")
        
        # TODO: Implement documentation generation with CrewAI agents
        click.echo("\n🚧 Documentation generation with AI agents coming soon!")
        click.echo("Git integration is ready and working!")
        
    except Exception as e:
        logger.error(f"Error analyzing repository: {e}")
        click.echo(f"Error: {e}", err=True)
        
    finally:
        # Cleanup temporary repositories
        git_tool.cleanup_all()


def display_repository_info(repo_info: RepositoryInfo):
    """Display repository information in a formatted way."""
    click.echo("\n" + "="*60)
    click.echo("📊 REPOSITORY ANALYSIS")
    click.echo("="*60)
    
    click.echo(f"📍 Repository URL: {repo_info.url}")
    click.echo(f"📁 Local Path: {repo_info.local_path}")
    click.echo(f"🌿 Current Branch: {repo_info.branch}")
    click.echo(f"📝 Total Commits: {repo_info.total_commits}")
    click.echo(f"🔄 Last Commit: {repo_info.last_commit[:8]}...")
    
    if repo_info.authors:
        click.echo(f"👥 Contributors ({len(repo_info.authors)}): {', '.join(repo_info.authors[:5])}")
        if len(repo_info.authors) > 5:
            click.echo(f"    ... and {len(repo_info.authors) - 5} more")
    
    if repo_info.languages:
        click.echo("\n💻 Programming Languages:")
        sorted_languages = sorted(repo_info.languages.items(), key=lambda x: x[1], reverse=True)
        for lang in sorted_languages[:10]:  # Show top 10 languages
            click.echo(f"    {lang}")


def display_recent_commits(commits):
    """Display recent commits in a formatted way."""
    if not commits:
        return
        
    click.echo("\n" + "="*60)
    click.echo("📈 RECENT COMMITS")
    click.echo("="*60)
    
    for i, commit in enumerate(commits[:5], 1):
        click.echo(f"\n{i}. {commit.commit_hash[:8]} by {commit.author}")
        click.echo(f"   📅 {commit.date.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"   💬 {commit.message.split(chr(10))[0][:80]}")  # First line, max 80 chars
        
        if commit.files_changed:
            file_count = len(commit.files_changed)
            click.echo(f"   📄 {file_count} file{'s' if file_count != 1 else ''} changed")
            
            if commit.total_additions or commit.total_deletions:
                click.echo(f"   ➕{commit.total_additions} ➖{commit.total_deletions} lines")


if __name__ == "__main__":
    cli()