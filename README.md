# CodeDoc AI Agent

AI Agent chuyên phân tích source code và tạo tài liệu comprehensive cho các dự án phần mềm.

## Features

- 🤖 AI-powered code analysis sử dụng CrewAI
- 📚 Tự động generate documentation theo thời gian thực
- 🔍 Phân tích architecture patterns và dependencies
- 📝 Tạo onboarding guides cho developers mới
- 🔄 Cập nhật docs theo mỗi commit changes

## Installation

### Prerequisites

- Python 3.11+
- uv package manager

### Setup

1. Clone repository:
```bash
git clone <repo-url>
cd codedoc-agent
```

2. Install dependencies với uv:
```bash
uv sync
```

3. Setup environment variables:
```bash
cp .env.example .env
# Edit .env và thêm API keys
```

4. Activate virtual environment:
```bash
source .venv/bin/activate  # On macOS/Linux
# hoặc .venv\Scripts\activate  # On Windows
```

## Usage

### Command Line

```bash
# Analyze GitHub repository
codedoc --repo-url https://github.com/username/repo

# Analyze local repository  
codedoc --repo-path ./path/to/repo

# Specify output directory
codedoc --repo-url https://github.com/username/repo --output-dir ./custom-docs
```

### Programmatic Usage

```python
from codedoc_agent import CodeDocAgent

agent = CodeDocAgent()
result = agent.analyze_repository("https://github.com/username/repo")
print(result)
```

## Configuration

Cấu hình trong file `.env`:

- `OPENAI_API_KEY`: OpenAI API key
- `ANTHROPIC_API_KEY`: Anthropic API key (alternative)
- `CREWAI_TELEMETRY_OPT_OUT`: Disable CrewAI telemetry

## Development

### Project Structure

```
codedoc-agent/
├── src/codedoc_agent/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── agents/              # CrewAI agents
│   ├── tools/               # Custom tools
│   └── templates/           # Documentation templates
├── tests/
├── pyproject.toml
└── README.md
```

### Development Dependencies

```bash
uv sync --group dev
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
isort src/ tests/
```

## License

MIT License