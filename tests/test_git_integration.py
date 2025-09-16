"""Tests for Git integration module."""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
import pytest

from git import Repo, GitCommandError
from src.codedoc_agent.tools.git_integration import (
    GitRepository,
    GitRepositoryTool,
    RepositoryInfo,
    FileChange,
    CommitAnalysis
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_repo(temp_dir):
    """Create a sample Git repository for testing."""
    repo_path = os.path.join(temp_dir, "sample_repo")
    os.makedirs(repo_path)
    
    # Initialize Git repository
    repo = Repo.init(repo_path)
    
    # Create some sample files
    sample_file = os.path.join(repo_path, "README.md")
    with open(sample_file, "w") as f:
        f.write("# Sample Repository\n\nThis is a test repository.")
    
    python_file = os.path.join(repo_path, "main.py")
    with open(python_file, "w") as f:
        f.write('print("Hello, World!")\n')
    
    # Create subdirectory with files
    src_dir = os.path.join(repo_path, "src")
    os.makedirs(src_dir)
    
    module_file = os.path.join(src_dir, "module.py")
    with open(module_file, "w") as f:
        f.write("def hello():\n    return 'Hello from module'\n")
    
    # Add and commit files
    repo.index.add([sample_file, python_file, module_file])
    repo.index.commit("Initial commit")
    
    # Create a second commit
    with open(python_file, "a") as f:
        f.write("\n# Added comment\n")
    
    repo.index.add([python_file])
    repo.index.commit("Added comment to main.py")
    
    return repo_path


class TestGitRepository:
    """Test cases for GitRepository class."""
    
    def test_init(self):
        """Test GitRepository initialization."""
        git_repo = GitRepository("/path/to/repo")
        assert git_repo.repo_path == "/path/to/repo"
        assert git_repo.auto_fetch is True
        assert git_repo._repo is None
        assert git_repo._temp_dir is None
    
    def test_context_manager(self, sample_repo):
        """Test GitRepository as context manager."""
        with GitRepository(sample_repo) as git_repo:
            git_repo.open()
            assert git_repo._repo is not None
        # After context, cleanup should be called
    
    def test_open_local_repository(self, sample_repo):
        """Test opening a local repository."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        local_path = git_repo.open()
        
        assert local_path == sample_repo
        assert git_repo._repo is not None
        assert git_repo.repo.working_dir == sample_repo
    
    def test_open_nonexistent_repository(self):
        """Test opening a non-existent repository."""
        git_repo = GitRepository("/nonexistent/path")
        
        with pytest.raises(FileNotFoundError):
            git_repo.open()
    
    def test_open_invalid_repository(self, temp_dir):
        """Test opening an invalid Git repository."""
        # Create a directory that's not a Git repository
        invalid_repo = os.path.join(temp_dir, "not_a_repo")
        os.makedirs(invalid_repo)
        
        git_repo = GitRepository(invalid_repo)
        
        with pytest.raises(GitCommandError):
            git_repo.open()
    
    def test_is_local_path(self, sample_repo):
        """Test local path detection."""
        git_repo = GitRepository(sample_repo)
        
        assert git_repo._is_local_path("/local/path")
        assert git_repo._is_local_path("./relative/path")
        assert git_repo._is_local_path("../parent/path")
        
        assert not git_repo._is_local_path("https://github.com/user/repo.git")
        assert not git_repo._is_local_path("http://example.com/repo.git")
        assert not git_repo._is_local_path("git@github.com:user/repo.git")
        assert not git_repo._is_local_path("ssh://git@server.com/repo.git")
    
    def test_get_repository_info(self, sample_repo):
        """Test getting repository information."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        repo_info = git_repo.get_repository_info()
        
        assert isinstance(repo_info, RepositoryInfo)
        assert repo_info.url == sample_repo
        assert repo_info.local_path == sample_repo
        assert repo_info.total_commits == 2
        assert len(repo_info.authors) > 0
        assert "Python" in repo_info.languages
        assert "Markdown" in repo_info.languages
    
    def test_get_recent_commits(self, sample_repo):
        """Test getting recent commits."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        commits = git_repo.get_recent_commits(count=5)
        
        assert len(commits) == 2  # We created 2 commits
        assert all(isinstance(commit, CommitAnalysis) for commit in commits)
        assert commits[0].message.strip() == "Added comment to main.py"
        assert commits[1].message.strip() == "Initial commit"
    
    def test_get_changed_files(self, sample_repo):
        """Test getting changed files between commits."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        # Get all commits
        commits = list(git_repo.repo.iter_commits())
        
        if len(commits) >= 2:
            # Get changes between second and first commit
            changes = git_repo.get_changed_files(commits[1].hexsha, commits[0].hexsha)
            
            assert len(changes) > 0
            assert all(isinstance(change, FileChange) for change in changes)
            
            # Should have a modification to main.py
            main_py_changes = [c for c in changes if c.file_path == "main.py"]
            assert len(main_py_changes) == 1
            assert main_py_changes[0].change_type == "M"  # Modified
    
    def test_get_file_history(self, sample_repo):
        """Test getting file history."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        history = git_repo.get_file_history("main.py")
        
        assert len(history) == 2  # main.py was in both commits
        assert all(isinstance(commit, CommitAnalysis) for commit in history)
    
    def test_get_important_files(self, sample_repo):
        """Test identifying important files."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        important_files = git_repo.get_important_files(threshold=1)
        
        # main.py should be important (changed in 2 commits)
        assert "main.py" in important_files
        assert important_files["main.py"] >= 1
    
    def test_get_repository_structure(self, sample_repo):
        """Test getting repository structure."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        structure = git_repo.get_repository_structure()
        
        assert isinstance(structure, dict)
        assert "." in structure  # Root directory
        assert "src" in structure  # Subdirectory
        
        # Check files in root
        root_files = structure["."]
        assert "README.md" in root_files
        assert "main.py" in root_files
        
        # Check files in src
        src_files = structure["src"]
        assert "module.py" in src_files
    
    def test_analyze_languages(self, sample_repo):
        """Test language analysis."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        languages = git_repo._analyze_languages()
        
        assert isinstance(languages, dict)
        assert "Python" in languages
        assert "Markdown" in languages
        assert languages["Python"] > 0
        assert languages["Markdown"] > 0
    
    def test_is_git_ignored(self, sample_repo):
        """Test Git ignore detection."""
        git_repo = GitRepository(sample_repo, auto_fetch=False)
        git_repo.open()
        
        # Test ignore patterns
        assert git_repo._is_git_ignored(Path(".git"))
        assert git_repo._is_git_ignored(Path("__pycache__"))
        assert git_repo._is_git_ignored(Path(".DS_Store"))
        assert git_repo._is_git_ignored(Path("node_modules"))
        
        # Test normal files
        assert not git_repo._is_git_ignored(Path("main.py"))
        assert not git_repo._is_git_ignored(Path("README.md"))
    
    def test_cleanup(self, sample_repo):
        """Test cleanup functionality."""
        git_repo = GitRepository(sample_repo)
        git_repo.open()
        
        # Set a temporary directory
        git_repo._temp_dir = tempfile.mkdtemp()
        temp_path = git_repo._temp_dir
        
        # Cleanup should remove temp directory
        git_repo.cleanup()
        
        assert not os.path.exists(temp_path)
        assert git_repo._temp_dir is None
        assert git_repo._repo is None


class TestGitRepositoryTool:
    """Test cases for GitRepositoryTool class."""
    
    def test_init(self):
        """Test GitRepositoryTool initialization."""
        tool = GitRepositoryTool()
        assert tool.name == "git_repository"
        assert isinstance(tool.description, str)
        assert isinstance(tool.repositories, dict)
        assert len(tool.repositories) == 0
    
    def test_analyze_repository(self, sample_repo):
        """Test repository analysis through tool."""
        tool = GitRepositoryTool()
        
        repo_info = tool.analyze_repository(sample_repo)
        
        assert isinstance(repo_info, RepositoryInfo)
        assert repo_info.local_path == sample_repo
        assert repo_info.total_commits == 2
        assert sample_repo in tool.repositories
    
    def test_get_recent_changes(self, sample_repo):
        """Test getting recent changes through tool."""
        tool = GitRepositoryTool()
        
        changes = tool.get_recent_changes(sample_repo, count=5)
        
        assert len(changes) == 2
        assert all(isinstance(change, CommitAnalysis) for change in changes)
        assert sample_repo in tool.repositories
    
    def test_cleanup_all(self, sample_repo):
        """Test cleanup all repositories."""
        tool = GitRepositoryTool()
        
        # Add a repository
        tool.analyze_repository(sample_repo)
        assert len(tool.repositories) == 1
        
        # Cleanup all
        tool.cleanup_all()
        assert len(tool.repositories) == 0
    
    @patch('src.codedoc_agent.tools.git_integration.Repo.clone_from')
    def test_clone_repository(self, mock_clone, temp_dir):
        """Test repository cloning through tool."""
        # Mock the clone operation
        mock_repo = MagicMock()
        mock_repo.working_dir = temp_dir
        mock_clone.return_value = mock_repo
        
        tool = GitRepositoryTool()
        repo_url = "https://github.com/example/repo.git"
        
        with patch.object(GitRepository, 'fetch'):  # Mock fetch to avoid network calls
            local_path = tool.clone_repository(repo_url, temp_dir)
        
        assert local_path == temp_dir
        assert repo_url in tool.repositories
        mock_clone.assert_called_once()


class TestDataClasses:
    """Test cases for data classes."""
    
    def test_repository_info(self):
        """Test RepositoryInfo data class."""
        repo_info = RepositoryInfo(
            url="https://github.com/example/repo.git",
            local_path="/local/path",
            branch="main",
            last_commit="abc123",
            total_commits=100,
            authors=["Alice", "Bob"],
            languages={"Python": 1000, "JavaScript": 500}
        )
        
        assert repo_info.url == "https://github.com/example/repo.git"
        assert repo_info.local_path == "/local/path"
        assert repo_info.branch == "main"
        assert repo_info.last_commit == "abc123"
        assert repo_info.total_commits == 100
        assert repo_info.authors == ["Alice", "Bob"]
        assert repo_info.languages == {"Python": 1000, "JavaScript": 500}
    
    def test_file_change(self):
        """Test FileChange data class."""
        file_change = FileChange(
            file_path="src/main.py",
            change_type="M",
            old_path=None,
            lines_added=10,
            lines_deleted=5
        )
        
        assert file_change.file_path == "src/main.py"
        assert file_change.change_type == "M"
        assert file_change.old_path is None
        assert file_change.lines_added == 10
        assert file_change.lines_deleted == 5
    
    def test_commit_analysis(self):
        """Test CommitAnalysis data class."""
        file_changes = [
            FileChange("main.py", "M", lines_added=5, lines_deleted=2),
            FileChange("README.md", "M", lines_added=3, lines_deleted=0)
        ]
        
        commit_analysis = CommitAnalysis(
            commit_hash="abc123def456",
            author="Alice",
            date=datetime.now(timezone.utc),
            message="Update documentation",
            files_changed=file_changes,
            total_additions=8,
            total_deletions=2
        )
        
        assert commit_analysis.commit_hash == "abc123def456"
        assert commit_analysis.author == "Alice"
        assert isinstance(commit_analysis.date, datetime)
        assert commit_analysis.message == "Update documentation"
        assert len(commit_analysis.files_changed) == 2
        assert commit_analysis.total_additions == 8
        assert commit_analysis.total_deletions == 2


if __name__ == "__main__":
    pytest.main([__file__])