# Contributing to Hybrid Agent Memory

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/yourusername/hybrid-agent-memory/issues)
- If not, create a new issue with:
  - Clear description of the bug
  - Steps to reproduce
  - Expected vs actual behavior
  - Your environment (OS, Python version, etc.)

### Suggesting Features

- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain why it would be valuable

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/hybrid-agent-memory.git
cd hybrid-agent-memory

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 -m pytest tests/
```

## Code Style

- Follow PEP 8
- Use meaningful variable names
- Add docstrings to functions
- Keep functions focused and small

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Reference issues when applicable

## Questions?

Feel free to open an issue for any questions!
