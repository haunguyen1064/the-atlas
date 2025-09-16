# CodeDoc AI Agent - Copilot Instructions

## Project Overview
CodeDoc AI Agent is a PoC for analyzing source code and generating comprehensive documentation using CrewAI multi-agent framework. Focus: simplicity over backward compatibility since only one developer uses it currently.

## Architecture & Key Components

### Core Structure
- **Entry Point**: `src/codedoc_agent/main.py` - CLI with Click framework
- **Git Integration**: `src/codedoc_agent/tools/git_integration.py` - Repository caching & analysis
- **Agent Framework**: CrewAI-based (planned), currently basic CLI implementation
- **Cache System**: `~/.cache/codedoc-agent/repos/` for repository persistence

### Git Integration Pattern
The `GitRepositoryTool` class implements smart caching:
```python
# URL normalization: https://github.com/owner/repo.git → github_com_owner_repo
# Cache-first strategy: check cache → pull updates OR clone fresh
cache_path = self._get_cache_path(repo_url)
if cache_path.exists():
    # Update existing cache
else:
    # Clone to cache
```

## Development Workflow

### Package Management
**Always use `uv` (not pip):**
```bash
uv sync          # Install dependencies
uv sync --dev    # Include dev dependencies  
uv add package   # Add new dependency
uv run command   # Run in virtual environment
```

### Testing
```bash
uv run pytest tests/test_git_integration.py -v  # Run specific tests
uv run pytest                                   # Run all tests
```

### Code Style
- **Black**: 88 character line length, Python 3.11 target
- **isort**: Black-compatible profile
- **MyPy**: Type checking enabled with strict settings

## Project-Specific Patterns

### Data Classes for Git Operations
Three key dataclasses define the Git analysis structure:
- `RepositoryInfo`: Complete repo metadata (authors, languages, commits)
- `FileChange`: Individual file modifications with change types (A/M/D/R)
- `CommitAnalysis`: Detailed commit breakdown with file changes

### Context Manager Pattern
`GitRepository` supports context managers for automatic cleanup:
```python
with GitRepository(repo_url) as git_repo:
    local_path = git_repo.clone()
    # Automatic cleanup on exit
```

### Language Detection
Built-in language analysis via file extensions with 25+ supported languages. Uses simple line counting for metrics, not external tools.

### CLI Design Pattern
Main CLI uses Click with structured command handling:
- Repository input: `--repo-url` (remote) OR `--repo-path` (local)  
- Output formatting: Emoji-rich console output with structured sections
- Error handling: Try-catch with user-friendly error messages

## Critical Developer Knowledge

### Git Repository Caching
**Cache location**: `~/.cache/codedoc-agent/repos/`
**Cache invalidation**: Automatic fetch on existing repos, corruption detection with re-clone fallback
**URL normalization**: Converts all Git URL formats to consistent cache keys

### Testing Strategy
Comprehensive test suite in `tests/test_git_integration.py`:
- Uses `pytest.fixture` for temporary Git repositories
- Mocks external Git operations for unit tests
- Tests both success and failure scenarios
- 23 test cases covering all major functionality

### Module Organization
```
src/codedoc_agent/
├── main.py              # CLI entry point
├── tools/
│   ├── __init__.py      # Exports for easy importing
│   └── git_integration.py  # Core Git functionality
├── agents/              # Future CrewAI agents (empty)
└── templates/           # Future documentation templates (empty)
```

## Integration Points

### External Dependencies
- **GitPython**: Core Git operations, not git CLI commands
- **Click**: CLI framework with type hints and help generation  
- **CrewAI**: Multi-agent framework (not yet implemented)
- **Logging**: Standard Python logging with configurable levels

### Future CrewAI Integration
Architecture document shows planned agents:
- CodeReader Agent: AST parsing and pattern detection
- Architect Agent: High-level architecture analysis  
- DocumentWriter Agent: Markdown generation
- Current code provides foundation for this multi-agent system

## Common Commands for Development

```bash
# Test Git integration with real repository
uv run python -m src.codedoc_agent.main --repo-url https://github.com/owner/repo --verbose

# Run comprehensive tests
uv run pytest tests/test_git_integration.py -v

# Code formatting
uv run black src/ tests/
uv run isort src/ tests/

# Type checking  
uv run mypy src/
```

## Important Notes for AI Agents

1. **This is a PoC** - prioritize working code over perfect architecture
2. **No backward compatibility needed** - refactor freely 
3. **uv is mandatory** - never use pip for this project
4. **Cache-first approach** - always consider Git repository caching impact
5. **Comprehensive testing** - maintain the existing test coverage patterns
6. **CrewAI ready** - current structure supports future multi-agent implementation

The codebase emphasizes practical functionality over enterprise patterns, making it ideal for rapid iteration and experimentation with AI-powered code analysis.