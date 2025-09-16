"""File pattern definitions for AI Agent classification."""

import logging
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class FilePatternProvider:
    """Provides file patterns and conventions for AI Agent analysis."""
    
    def __init__(self):
        """Initialize pattern provider with language-specific knowledge."""
        self._initialize_patterns()
    
    def _initialize_patterns(self):
        """Initialize pattern mappings for file classification."""
        
        # Entry point patterns by language
        self.entry_point_patterns = {
            'python': [
                'main.py', '__main__.py', 'app.py', 'server.py', 'run.py',
                'manage.py', 'wsgi.py', 'asgi.py', 'application.py'
            ],
            'javascript': [
                'index.js', 'main.js', 'app.js', 'server.js', 'start.js',
                'index.mjs', 'app.mjs', 'server.mjs'
            ],
            'typescript': [
                'index.ts', 'main.ts', 'app.ts', 'server.ts', 'start.ts',
                'index.tsx', 'app.tsx'
            ],
            'java': [
                'Main.java', 'Application.java', 'App.java', 'Server.java',
                r'.*Application\.java$', r'.*Main\.java$'
            ],
            'go': ['main.go'],
            'rust': ['main.rs', 'lib.rs'],
            'c': ['main.c'],
            'cpp': ['main.cpp', 'main.cxx'],
            'csharp': ['Program.cs', 'Main.cs', 'Application.cs'],
            'php': ['index.php', 'app.php', 'bootstrap.php']
        }
        
        # Configuration file patterns
        self.config_patterns = [
            # Package managers
            r'package\.json$', r'package-lock\.json$', r'yarn\.lock$',
            r'requirements.*\.txt$', r'Pipfile$', r'pyproject\.toml$',
            r'pom\.xml$', r'build\.gradle$', r'Cargo\.toml$',
            r'composer\.json$', r'go\.mod$', r'Gemfile$',
            
            # Environment and config
            r'\.env.*$', r'config\..*$', r'settings\..*$',
            r'.*\.config\.(js|ts|json)$', r'.*\.conf$', r'.*\.ini$',
            r'.*\.yaml$', r'.*\.yml$', r'.*\.toml$',
            
            # Build and deployment
            r'Dockerfile.*$', r'docker-compose.*\.(yml|yaml)$',
            r'Makefile$', r'makefile$', r'CMakeLists\.txt$',
            r'webpack\.config\..*$', r'vite\.config\..*$',
            r'rollup\.config\..*$', r'babel\.config\..*$',
            r'tsconfig\.json$', r'jsconfig\.json$',
            
            # CI/CD
            r'\.github/workflows/.*\.(yml|yaml)$',
            r'\.gitlab-ci\.yml$', r'\.travis\.yml$',
            r'Jenkinsfile$', r'azure-pipelines\.yml$'
        ]
        
        # Test file patterns
        self.test_patterns = [
            # Python
            r'test_.*\.py$', r'.*_test\.py$', r'conftest\.py$',
            r'.*/tests/.*\.py$', r'.*/test/.*\.py$',
            
            # JavaScript/TypeScript
            r'.*\.test\.(js|ts|jsx|tsx)$', r'.*\.spec\.(js|ts|jsx|tsx)$',
            r'.*/tests/.*\.(js|ts|jsx|tsx)$', r'.*/test/.*\.(js|ts|jsx|tsx)$',
            r'.*/__tests__/.*\.(js|ts|jsx|tsx)$',
            
            # Java
            r'.*Test\.java$', r'.*Tests\.java$', r'.*IT\.java$',
            r'.*/test/.*\.java$', r'.*/tests/.*\.java$',
            
            # Go
            r'.*_test\.go$',
            
            # Rust
            r'.*_test\.rs$', r'.*/tests/.*\.rs$',
            
            # C/C++
            r'test_.*\.(c|cpp|cxx)$', r'.*_test\.(c|cpp|cxx)$',
            
            # General
            r'.*/test.*$', r'.*/spec.*$'
        ]
        
        # Documentation patterns
        self.doc_patterns = [
            r'README.*$', r'CHANGELOG.*$', r'HISTORY.*$',
            r'LICENSE.*$', r'COPYING.*$', r'NOTICE.*$',
            r'CONTRIBUTING.*$', r'CODE_OF_CONDUCT.*$',
            r'.*\.md$', r'.*\.rst$', r'.*\.txt$',
            r'.*/docs/.*$', r'.*/doc/.*$', r'.*/documentation/.*$',
            r'.*\.adoc$', r'.*\.asciidoc$'
        ]
        
        # Build script patterns
        self.build_patterns = [
            r'Makefile$', r'makefile$', r'Dockerfile.*$',
            r'build\.sh$', r'build\.bat$', r'install\.sh$',
            r'setup\.py$', r'setup\.cfg$', r'pyproject\.toml$',
            r'build\.gradle$', r'build\.xml$', r'CMakeLists\.txt$',
            r'webpack\..*$', r'gulpfile\..*$', r'gruntfile\..*$',
            r'rollup\..*$', r'vite\..*$'
        ]
        
        # Asset patterns
        self.asset_patterns = [
            r'.*\.(png|jpg|jpeg|gif|svg|ico|webp)$',
            r'.*\.(css|scss|sass|less|styl)$',
            r'.*\.(woff|woff2|ttf|eot)$',
            r'.*\.(mp3|mp4|wav|avi|mov)$',
            r'.*\.(pdf|doc|docx|xls|xlsx)$'
        ]
        
        # Utility/helper patterns
        self.utility_patterns = [
            r'.*/utils?/.*$', r'.*/util/.*$', r'.*/helpers?/.*$',
            r'.*/helper/.*$', r'.*/common/.*$', r'.*/shared/.*$',
            r'.*/lib/.*$', r'.*/libs/.*$', r'.*/library/.*$',
            r'.*util.*\..*$', r'.*helper.*\..*$', r'.*common.*\..*$'
        ]
        
        # Framework-specific important files
        self.framework_patterns = {
            'django': [
                'settings.py', 'urls.py', 'wsgi.py', 'asgi.py',
                'models.py', 'views.py', 'admin.py', 'forms.py'
            ],
            'flask': [
                'app.py', 'run.py', 'config.py', '__init__.py'
            ],
            'react': [
                'App.js', 'App.tsx', 'index.js', 'index.tsx',
                'App.css', 'index.css'
            ],
            'vue': [
                'App.vue', 'main.js', 'main.ts', 'index.html'
            ],
            'angular': [
                'app.module.ts', 'main.ts', 'app.component.ts',
                'angular.json', 'app.component.html'
            ],
            'spring': [
                'Application.java', 'Main.java', 'application.properties',
                'application.yml', 'pom.xml'
            ],
            'express': [
                'app.js', 'server.js', 'index.js', 'routes/',
                'middleware/', 'controllers/'
            ]
        }
    
    def get_entry_point_patterns(self, language: str) -> List[str]:
        """Get entry point patterns for a specific language.
        
        Args:
            language: Programming language name.
            
        Returns:
            List of entry point file patterns.
        """
        return self.entry_point_patterns.get(language.lower(), [])
    
    def get_config_patterns(self) -> List[str]:
        """Get configuration file patterns.
        
        Returns:
            List of configuration file regex patterns.
        """
        return self.config_patterns
    
    def get_test_patterns(self) -> List[str]:
        """Get test file patterns.
        
        Returns:
            List of test file regex patterns.
        """
        return self.test_patterns
    
    def get_framework_patterns(self, framework: str) -> List[str]:
        """Get framework-specific file patterns.
        
        Args:
            framework: Framework name.
            
        Returns:
            List of framework-specific file patterns.
        """
        return self.framework_patterns.get(framework.lower(), [])
    
    def get_all_patterns_for_language(self, language: str) -> Dict[str, List[str]]:
        """Get all patterns relevant to a specific language.
        
        Args:
            language: Programming language name.
            
        Returns:
            Dictionary with pattern categories and their patterns.
        """
        lang_key = language.lower()
        return {
            'entry_points': self.entry_point_patterns.get(lang_key, []),
            'config_files': self.config_patterns,
            'test_files': self.test_patterns,
            'build_files': self.build_patterns,
            'framework_files': {k: v for k, v in self.framework_patterns.items()},
            'doc_files': self.doc_patterns
        }
    
    def get_language_extensions(self) -> Dict[str, List[str]]:
        """Get mapping of languages to their file extensions.
        
        Returns:
            Dictionary mapping language names to extension lists.
        """
        return {
            'Python': ['.py', '.pyw', '.pyx', '.pyi'],
            'JavaScript': ['.js', '.mjs', '.cjs'],
            'TypeScript': ['.ts', '.tsx'],
            'Java': ['.java'],
            'Go': ['.go'],
            'Rust': ['.rs'],
            'C': ['.c', '.h'],
            'C++': ['.cpp', '.cxx', '.cc', '.hpp', '.hxx', '.hh'],
            'C#': ['.cs'],
            'PHP': ['.php', '.php3', '.php4', '.php5'],
            'Ruby': ['.rb', '.rbw'],
            'Swift': ['.swift'],
            'Kotlin': ['.kt', '.kts'],
            'Scala': ['.scala'],
            'Dart': ['.dart'],
            'HTML': ['.html', '.htm'],
            'CSS': ['.css'],
            'SCSS': ['.scss'],
            'Sass': ['.sass'],
            'Vue': ['.vue'],
            'React': ['.jsx', '.tsx'],
            'Shell': ['.sh', '.bash', '.zsh', '.fish'],
            'SQL': ['.sql'],
            'YAML': ['.yml', '.yaml'],
            'JSON': ['.json'],
            'XML': ['.xml'],
            'Markdown': ['.md', '.markdown']
        }