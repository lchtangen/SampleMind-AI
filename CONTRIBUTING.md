# 🤝 Contributing to SampleMind AI v6

Thank you for your interest in contributing to SampleMind AI! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git with proper configuration
- Poetry for dependency management

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR-USERNAME/samplemind-ai-v6.git
   cd samplemind-ai-v6
   git remote add upstream https://github.com/samplemind/samplemind-ai-v6.git
   ```

2. **Environment Setup**
   ```bash
   make setup
   pre-commit install
   make doctor
   ```

3. **Run Tests**
   ```bash
   make test
   make coverage
   ```

## Development Workflow

### Branch Strategy

We follow the **Git Flow** branching model:

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/` - New features and enhancements
- `hotfix/` - Critical production fixes

### Development Process

1. **Create Feature Branch**
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feature/your-feature-name
   ```

2. **Development Cycle**
   ```bash
   # Make changes, write tests
   make test
   make lint
   make format
   git commit -m "feat: add intelligent sample organization"
   ```

3. **Submit Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

## Coding Standards

### Python Style Guide

We follow **PEP 8** with these tools:
- **Black** for code formatting
- **isort** for import sorting
- **Ruff** for linting
- **MyPy** for type checking

### Code Quality

```bash
# Run all quality checks
make quality

# Individual tools
ruff check .
black .
isort .
mypy src/
bandit -r src/
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated tests
├── integration/    # Component integration
├── e2e/           # End-to-end workflows
├── performance/   # Performance benchmarks
└── fixtures/      # Test data
```

### Writing Tests

```python
import pytest
from unittest.mock import AsyncMock

async def test_analyze_sample_success():
    """Test successful audio analysis."""
    processor = AudioProcessor()
    result = await processor.analyze_sample("test.wav")
    
    assert result is not None
    assert result.tempo > 0
    assert result.genre is not None
```

## Pull Request Process

### PR Checklist

- [ ] **Code Quality**: All tests pass, code is formatted
- [ ] **Documentation**: Code is documented, README updated
- [ ] **Testing**: New features have tests, coverage maintained
- [ ] **Commit Standards**: Conventional commit messages

### Review Process

1. **Automated Checks**: CI pipeline runs tests and quality checks
2. **Human Review**: At least 2 reviewers required
3. **Approval Process**: All checks pass, approvals obtained

## Issue Reporting

Use the appropriate issue template:

### Bug Reports

```markdown
**Bug Description**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What you expected to happen.

**Environment**
- OS: [e.g., macOS 14.1]
- Python: [e.g., 3.11.5]
- SampleMind Version: [e.g., 6.0.0]
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the feature you'd like to see.

**Problem Statement**
What problem would this feature solve?

**Proposed Solution**
How do you envision this working?
```

## Community

### Communication Channels

- **Discord**: [SampleMind Community](https://discord.gg/samplemind)
- **GitHub Discussions**: [Project Discussions](https://github.com/samplemind/samplemind-ai-v6/discussions)

### Recognition

We recognize contributors through:
- Monthly contributor highlights
- Special recognition at conferences
- Early access to new features
- Exclusive contributor merchandise

---

Happy contributing! 🎵✨
