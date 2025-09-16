"""Main entry point for CodeDoc AI Agent."""

import click
from typing import Optional


@click.command()
@click.option('--repo-url', help='Repository URL to analyze')
@click.option('--repo-path', help='Local repository path to analyze')
@click.option('--output-dir', default='./docs', help='Output directory for documentation')
def cli(repo_url: Optional[str], repo_path: Optional[str], output_dir: str):
    """CodeDoc AI Agent - Analyze source code and generate documentation."""
    if not repo_url and not repo_path:
        click.echo("Please provide either --repo-url or --repo-path")
        return
    
    click.echo(f"Analyzing repository: {repo_url or repo_path}")
    click.echo(f"Output directory: {output_dir}")
    
    # TODO: Implement the main logic
    click.echo("CodeDoc AI Agent is not yet implemented. Coming soon!")


if __name__ == "__main__":
    cli()