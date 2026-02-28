# Contributing to OpenClaw Hybrid Memory

Thank you for your interest in contributing to **OpenClaw Hybrid Memory**! This document provides guidelines for contributing to the project.

## About This Project

OpenClaw Hybrid Memory is designed specifically for [OpenClaw](https://openclaw.ai) AI agents, providing a production-grade hybrid memory system. While it's built for OpenClaw, the core components can be adapted for other agent frameworks.

## How to Contribute

### Reporting Bugs

- Check if the bug has already been reported in [Issues](https://github.com/lamost423/openclaw-hybrid-memory/issues)
- Include your OpenClaw version and configuration
- Provide steps to reproduce in an OpenClaw context
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

## Development Setup for OpenClaw

```bash
# Clone into your OpenClaw workspace
cd ~/.openclaw/workspace
git clone https://github.com/lamost423/openclaw-hybrid-memory.git scripts/openclaw-hybrid-memory
cd scripts/openclaw-hybrid-memory

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Test with your OpenClaw memory
python3 scripts/hybrid_search.py "test query" --source-dir ~/.openclaw/workspace/memory/
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
