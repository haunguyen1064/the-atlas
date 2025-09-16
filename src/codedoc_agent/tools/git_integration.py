"""Git integration module for CodeDoc AI Agent.

This module provides comprehensive Git operations including:
- Repository cloning and fetching
- Change detection and analysis
- Branch management
- File tracking and history analysis
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import logging

import git
from git import Repo, GitCommandError
from git.objects import Commit


logger = logging.getLogger(__name__)


@dataclass
class RepositoryInfo:
    """Information about a Git repository."""
    url: str
    local_path: str
    branch: str
    last_commit: str
    total_commits: int
    authors: List[str]
    languages: Dict[str, int]  # Language -> line count


@dataclass
class FileChange:
    """Represents a file change in a commit."""
    file_path: str
    change_type: str  # 'A' (added), 'M' (modified), 'D' (deleted), 'R' (renamed)
    old_path: Optional[str] = None  # For renamed files
    lines_added: int = 0
    lines_deleted: int = 0


@dataclass
class CommitAnalysis:
    """Analysis of a specific commit."""
    commit_hash: str
    author: str
    date: datetime
    message: str
    files_changed: List[FileChange]
    total_additions: int
    total_deletions: int


class GitRepository:
    """Git repository manager for CodeDoc AI Agent."""
    
    def __init__(self, repo_path: str, auto_fetch: bool = True):
        """Initialize Git repository manager.
        
        Args:
            repo_path: Path to the repository (local or remote URL)
            auto_fetch: Whether to automatically fetch latest changes
        """
        self.repo_path = repo_path
        self.auto_fetch = auto_fetch
        self._repo: Optional[Repo] = None
        self._temp_dir: Optional[str] = None
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
    
    @property
    def repo(self) -> Repo:
        """Get the Git repository object."""
        if self._repo is None:
            raise RuntimeError("Repository not initialized. Call clone() or open() first.")
        return self._repo
    
    def clone(self, target_dir: Optional[str] = None, branch: Optional[str] = None) -> str:
        """Clone a remote repository.
        
        Args:
            target_dir: Target directory for cloning. If None, uses temporary directory.
            branch: Specific branch to clone. If None, clones default branch.
            
        Returns:
            Path to the cloned repository.
            
        Raises:
            GitCommandError: If cloning fails.
        """
        if self._is_local_path(self.repo_path):
            raise ValueError(f"Path {self.repo_path} appears to be local. Use open() instead.")
        
        if target_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix="codedoc_repo_")
            target_dir = self._temp_dir
        
        target_path = Path(target_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Cloning repository {self.repo_path} to {target_dir}")
        
        try:
            clone_kwargs = {}
            if branch:
                clone_kwargs['branch'] = branch
                
            self._repo = Repo.clone_from(self.repo_path, target_dir, **clone_kwargs)
            
            if self.auto_fetch:
                self.fetch()
                
            logger.info(f"Successfully cloned repository to {target_dir}")
            return target_dir
            
        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise
    
    def open(self, repo_path: Optional[str] = None) -> str:
        """Open an existing local repository.
        
        Args:
            repo_path: Path to local repository. If None, uses self.repo_path.
            
        Returns:
            Path to the repository.
            
        Raises:
            GitCommandError: If opening fails.
        """
        path = repo_path or self.repo_path
        
        if not self._is_local_path(path):
            raise ValueError(f"Path {path} appears to be a URL. Use clone() instead.")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"Repository path {path} does not exist.")
        
        try:
            self._repo = Repo(path)
            
            if self.auto_fetch and self._has_remote():
                self.fetch()
                
            logger.info(f"Successfully opened repository at {path}")
            return path
            
        except git.exc.InvalidGitRepositoryError as e:
            logger.error(f"Invalid Git repository at {path}: {e}")
            raise GitCommandError(f"Invalid Git repository at {path}")
    
    def fetch(self, remote_name: str = "origin") -> None:
        """Fetch latest changes from remote.
        
        Args:
            remote_name: Name of the remote to fetch from.
        """
        if not self._has_remote():
            logger.warning("No remote found, skipping fetch.")
            return
        
        try:
            logger.info(f"Fetching from remote '{remote_name}'")
            self.repo.remotes[remote_name].fetch()
            logger.info("Successfully fetched latest changes")
        except (GitCommandError, IndexError) as e:
            logger.error(f"Failed to fetch from remote: {e}")
            raise
    
    def get_repository_info(self) -> RepositoryInfo:
        """Get comprehensive repository information.
        
        Returns:
            RepositoryInfo object with repository details.
        """
        repo = self.repo
        
        # Get remote URL or local path
        url = self.repo_path
        if self._has_remote():
            url = list(repo.remotes.origin.urls)[0]
        
        # Get current branch
        try:
            current_branch = repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            current_branch = repo.head.commit.hexsha[:8]
        
        # Get commit information
        commits = list(repo.iter_commits())
        total_commits = len(commits)
        last_commit = commits[0].hexsha if commits else ""
        
        # Get unique authors
        authors = list(set(commit.author.name for commit in commits[:100]))  # Limit for performance
        
        # Analyze languages (basic file extension analysis)
        languages = self._analyze_languages()
        
        return RepositoryInfo(
            url=url,
            local_path=repo.working_dir,
            branch=current_branch,
            last_commit=last_commit,
            total_commits=total_commits,
            authors=authors,
            languages=languages
        )
    
    def get_recent_commits(self, count: int = 10, since: Optional[datetime] = None) -> List[CommitAnalysis]:
        """Get recent commits with detailed analysis.
        
        Args:
            count: Number of commits to retrieve.
            since: Only get commits since this date.
            
        Returns:
            List of CommitAnalysis objects.
        """
        commits = []
        
        for commit in self.repo.iter_commits(max_count=count):
            if since and commit.committed_datetime < since:
                break
                
            analysis = self._analyze_commit(commit)
            commits.append(analysis)
        
        return commits
    
    def get_changed_files(self, from_commit: str, to_commit: str = "HEAD") -> List[FileChange]:
        """Get files changed between two commits.
        
        Args:
            from_commit: Starting commit (hash or reference).
            to_commit: Ending commit (hash or reference).
            
        Returns:
            List of FileChange objects.
        """
        try:
            from_commit_obj = self.repo.commit(from_commit)
            to_commit_obj = self.repo.commit(to_commit)
            
            diff = from_commit_obj.diff(to_commit_obj)
            
            changes = []
            for diff_item in diff:
                change = FileChange(
                    file_path=diff_item.b_path or diff_item.a_path,
                    change_type=diff_item.change_type,
                    old_path=diff_item.a_path if diff_item.change_type == 'R' else None
                )
                changes.append(change)
            
            return changes
            
        except GitCommandError as e:
            logger.error(f"Failed to get changed files: {e}")
            raise
    
    def get_file_history(self, file_path: str, max_commits: int = 50) -> List[CommitAnalysis]:
        """Get commit history for a specific file.
        
        Args:
            file_path: Path to the file relative to repository root.
            max_commits: Maximum number of commits to retrieve.
            
        Returns:
            List of CommitAnalysis objects affecting the file.
        """
        commits = []
        
        try:
            for commit in self.repo.iter_commits(paths=file_path, max_count=max_commits):
                analysis = self._analyze_commit(commit)
                commits.append(analysis)
                
            return commits
            
        except GitCommandError as e:
            logger.error(f"Failed to get file history for {file_path}: {e}")
            raise
    
    def get_important_files(self, threshold: int = 5) -> Dict[str, int]:
        """Identify important files based on change frequency.
        
        Args:
            threshold: Minimum number of changes to consider a file important.
            
        Returns:
            Dictionary mapping file paths to change counts.
        """
        file_changes = {}
        
        # Analyze recent commits to count file changes
        for commit in self.repo.iter_commits(max_count=200):  # Limit for performance
            try:
                for diff_item in commit.diff(commit.parents[0] if commit.parents else None):
                    file_path = diff_item.b_path or diff_item.a_path
                    if file_path:
                        file_changes[file_path] = file_changes.get(file_path, 0) + 1
            except (GitCommandError, IndexError):
                # Skip merge commits or commits without parents
                continue
        
        # Filter by threshold
        important_files = {
            path: count for path, count in file_changes.items() 
            if count >= threshold
        }
        
        return dict(sorted(important_files.items(), key=lambda x: x[1], reverse=True))
    
    def get_repository_structure(self) -> Dict[str, List[str]]:
        """Get repository directory structure.
        
        Returns:
            Dictionary mapping directories to their files.
        """
        structure = {}
        repo_path = Path(self.repo.working_dir)
        
        for item in repo_path.rglob("*"):
            if item.is_file() and not self._is_git_ignored(item):
                relative_path = item.relative_to(repo_path)
                parent_dir = str(relative_path.parent) if relative_path.parent != Path(".") else "."
                
                if parent_dir not in structure:
                    structure[parent_dir] = []
                
                structure[parent_dir].append(str(relative_path.name))
        
        return structure
    
    def cleanup(self):
        """Clean up temporary directories and resources."""
        if self._temp_dir and os.path.exists(self._temp_dir):
            try:
                shutil.rmtree(self._temp_dir)
                logger.info(f"Cleaned up temporary directory: {self._temp_dir}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary directory: {e}")
            finally:
                self._temp_dir = None
        
        self._repo = None
    
    def _is_local_path(self, path: str) -> bool:
        """Check if path is a local filesystem path."""
        return not (path.startswith(('http://', 'https://', 'git@', 'ssh://')))
    
    def _has_remote(self) -> bool:
        """Check if repository has remote configured."""
        return len(self.repo.remotes) > 0
    
    def _analyze_commit(self, commit: Commit) -> CommitAnalysis:
        """Analyze a single commit.
        
        Args:
            commit: Git commit object.
            
        Returns:
            CommitAnalysis object.
        """
        files_changed = []
        total_additions = 0
        total_deletions = 0
        
        try:
            # Get diff for this commit
            if commit.parents:
                diff = commit.diff(commit.parents[0])
            else:
                # Initial commit
                diff = commit.diff(None)
            
            for diff_item in diff:
                file_change = FileChange(
                    file_path=diff_item.b_path or diff_item.a_path,
                    change_type=diff_item.change_type,
                    old_path=diff_item.a_path if diff_item.change_type == 'R' else None
                )
                files_changed.append(file_change)
                
                # Count line changes (approximation)
                if hasattr(diff_item, 'insertions'):
                    file_change.lines_added = diff_item.insertions
                    total_additions += diff_item.insertions
                if hasattr(diff_item, 'deletions'):
                    file_change.lines_deleted = diff_item.deletions
                    total_deletions += diff_item.deletions
                    
        except GitCommandError:
            # Handle cases where diff cannot be computed
            pass
        
        return CommitAnalysis(
            commit_hash=commit.hexsha,
            author=commit.author.name,
            date=commit.committed_datetime,
            message=commit.message.strip(),
            files_changed=files_changed,
            total_additions=total_additions,
            total_deletions=total_deletions
        )
    
    def _analyze_languages(self) -> Dict[str, int]:
        """Analyze programming languages in the repository.
        
        Returns:
            Dictionary mapping language names to line counts.
        """
        languages = {}
        repo_path = Path(self.repo.working_dir)
        
        # Simple language detection based on file extensions
        language_extensions = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.vue': 'Vue',
            '.jsx': 'JSX',
            '.tsx': 'TSX',
            '.md': 'Markdown',
            '.yml': 'YAML',
            '.yaml': 'YAML',
            '.json': 'JSON',
            '.xml': 'XML',
            '.sql': 'SQL',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.dockerfile': 'Dockerfile',
            '.r': 'R',
            '.m': 'MATLAB',
            '.pl': 'Perl'
        }
        
        for file_path in repo_path.rglob("*"):
            if file_path.is_file() and not self._is_git_ignored(file_path):
                extension = file_path.suffix.lower()
                if extension in language_extensions:
                    language = language_extensions[extension]
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            line_count = sum(1 for _ in f)
                        languages[language] = languages.get(language, 0) + line_count
                    except (OSError, UnicodeDecodeError):
                        # Skip files that cannot be read
                        continue
        
        return languages
    
    def _is_git_ignored(self, file_path: Path) -> bool:
        """Check if file is Git ignored.
        
        Args:
            file_path: Path to check.
            
        Returns:
            True if file should be ignored.
        """
        # Basic ignore patterns
        ignore_patterns = {
            '.git', '__pycache__', '.pyc', '.DS_Store', 
            'node_modules', '.vscode', '.idea', '.vs',
            '*.log', '*.tmp', '*.cache'
        }
        
        path_parts = file_path.parts
        for part in path_parts:
            if part in ignore_patterns or part.startswith('.'):
                return True
        
        return False


class GitRepositoryTool:
    """CrewAI tool wrapper for Git repository operations."""
    
    name = "git_repository"
    description = "Tool for Git repository operations including cloning, analysis, and change detection"
    
    def __init__(self):
        self.repositories: Dict[str, GitRepository] = {}
    
    def clone_repository(self, repo_url: str, target_dir: Optional[str] = None) -> str:
        """Clone a repository and return the local path.
        
        Args:
            repo_url: Repository URL to clone.
            target_dir: Target directory for cloning.
            
        Returns:
            Local path to the cloned repository.
        """
        git_repo = GitRepository(repo_url)
        local_path = git_repo.clone(target_dir)
        self.repositories[repo_url] = git_repo
        return local_path
    
    def analyze_repository(self, repo_path: str) -> RepositoryInfo:
        """Analyze repository and return comprehensive information.
        
        Args:
            repo_path: Local path to repository.
            
        Returns:
            RepositoryInfo object with analysis results.
        """
        if repo_path in self.repositories:
            git_repo = self.repositories[repo_path]
        else:
            git_repo = GitRepository(repo_path)
            git_repo.open()
            self.repositories[repo_path] = git_repo
        
        return git_repo.get_repository_info()
    
    def get_recent_changes(self, repo_path: str, count: int = 10) -> List[CommitAnalysis]:
        """Get recent commits with analysis.
        
        Args:
            repo_path: Local path to repository.
            count: Number of recent commits to analyze.
            
        Returns:
            List of CommitAnalysis objects.
        """
        if repo_path not in self.repositories:
            git_repo = GitRepository(repo_path)
            git_repo.open()
            self.repositories[repo_path] = git_repo
        
        return self.repositories[repo_path].get_recent_commits(count)
    
    def cleanup_all(self):
        """Clean up all managed repositories."""
        for git_repo in self.repositories.values():
            git_repo.cleanup()
        self.repositories.clear()