# Development Guide

This guide covers the development setup and tooling for the Fitler monorepo.

## Quick Start

1. **Open in VS Code**: The repository includes a devcontainer that automatically sets up the development environment
2. **Extensions**: All necessary VS Code extensions will be installed automatically
3. **Dependencies**: Python and Node.js dependencies will be installed via the postCreateCommand

## Development Tools

### Python Development

**Linting & Formatting:**
- **Black**: Auto-formatting (line length: 120)
- **Flake8**: Code style checking
- **Pylint**: Advanced linting
- **MyPy**: Type checking
- **isort**: Import sorting

**Testing:**
- **Pytest**: Test runner with coverage

**Usage:**
```bash
# Format code
black --line-length=120 fitler/ tests/

# Run linting
flake8 fitler/ tests/
pylint fitler/
mypy fitler/

# Run tests
python -m pytest -v
```

### Web Development (site/)

**Linting & Formatting:**
- **ESLint**: JavaScript linting
- **Stylelint**: CSS linting  
- **Prettier**: Code formatting

**Build Tools:**
- **Vite**: Build system and dev server
- **Node.js 18**: Runtime environment

**Usage:**
```bash
cd site/

# Install dependencies
npm install

# Development server
npm run dev

# Build for production
npm run build

# Lint code
npm run lint

# Format code
npm run format
```

## VS Code Integration

### Format on Save
- Python files auto-format with Black
- JavaScript/CSS files auto-format with Prettier
- Import statements are automatically organized

### Error Highlighting
- Python: Flake8, Pylint, and MyPy errors shown inline
- JavaScript: ESLint errors shown inline
- CSS: Stylelint errors shown inline

### VS Code Tasks
Access via `Ctrl+Shift+P` → "Tasks: Run Task":

- **Python: Run Tests** - Run all Python tests
- **Python: Lint All** - Run all Python linting tools
- **Python: Format Code** - Format Python code with Black
- **Site: Build** - Build the website
- **Site: Dev Server** - Start development server
- **Site: Lint** - Lint website code
- **Site: Format** - Format website code
- **Full: Lint and Test** - Run all linting and tests

### Debugging
Pre-configured debug configurations:
- **Python: Current File** - Debug the current Python file
- **Python: Fitler Module** - Debug the Fitler module
- **Python: Pytest Current File** - Debug current test file
- **Python: Pytest All** - Debug all tests

## Pre-commit Hooks

Pre-commit hooks run automatically on `git commit` to ensure code quality:

```bash
# Install hooks (done automatically in devcontainer)
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

**Configured hooks:**
- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection
- Merge conflict detection
- Python formatting (Black)
- Python linting (Flake8, isort)
- Python type checking (MyPy)
- JavaScript/CSS formatting (Prettier)
- JavaScript linting (ESLint)

## GitHub Actions

Automated workflows run on every push:

- **Python Testing**: pytest with coverage
- **Python Linting**: Black, Flake8, Pylint, MyPy
- **Website Deployment**: Automatic deployment to GitHub Pages
- **Website Linting**: ESLint and Stylelint for code quality

## File Structure

```
fitler/
├── .devcontainer/          # VS Code devcontainer configuration
├── .github/workflows/      # GitHub Actions workflows
├── .vscode/               # VS Code workspace settings
├── fitler/                # Python package source
├── tests/                 # Python tests
├── site/                  # Static website
│   ├── src/              # Website source code
│   ├── scripts/          # Build scripts
│   └── dist/             # Built website (auto-generated)
├── .pre-commit-config.yaml # Pre-commit configuration
├── pyproject.toml         # Python project configuration
└── README.md             # Main documentation
```

## Tips

1. **Auto-save**: Enabled to trigger format-on-save frequently
2. **Problem Panel**: Check `View > Problems` for all linting errors
3. **Terminal**: Use the integrated terminal for running commands
4. **Git**: Pre-commit hooks prevent committing poorly formatted code
5. **Extensions**: All necessary extensions are automatically installed
