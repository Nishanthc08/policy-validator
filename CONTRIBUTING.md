# Contributing to Policy Validator

Thank you for your interest in contributing to the Policy Validator project! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Environment](#development-environment)
4. [Coding Standards](#coding-standards)
5. [Submitting Changes](#submitting-changes)
6. [Pull Request Process](#pull-request-process)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [Issue Reporting](#issue-reporting)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please be kind and constructive in your communications and consider the impact of your words and actions on others.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/yourusername/policy_validator.git
   cd policy_validator
   ```
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```
5. Create a branch for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Environment

The project uses the following tools for development:

- **pytest**: For unit and integration testing
- **flake8**: For code style checks
- **black**: For code formatting
- **mypy**: For type checking
- **isort**: For import sorting

Install all development dependencies with:

```bash
pip install -e ".[dev]"
```

## Coding Standards

We follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html) with the following specific requirements:

### Docstrings

- Use Google-style docstrings for all modules, classes, and functions
- Include type annotations in docstrings and as function annotations
- Document parameters, return values, and exceptions
- Include examples for public APIs
- Add implementation notes for complex functions

Example:

```python
def validate_policy(file_path: str, standard: str = "NIST") -> Dict[str, Any]:
    """Validate a policy document against the specified standard.
    
    Args:
        file_path: Path to the policy document file.
        standard: Validation standard to use (default: "NIST").
            Options are "NIST", "ISO", "SOC2", or "Custom".
            
    Returns:
        Dictionary containing validation results with the following structure:
        {
            "valid": bool,
            "issues": List[str],
            "details": Dict[str, Any]
        }
        
    Raises:
        FileNotFoundError: If the policy file doesn't exist.
        ValueError: If the standard is not supported.
        
    Example:
        >>> results = validate_policy("policy.pdf", "ISO")
        >>> if results["valid"]:
        ...     print("Policy is compliant!")
        ... else:
        ...     print("Issues found:", results["issues"])
    """
```

### Type Hints

- Use type hints for all function parameters and return values
- Use `Optional` for parameters that can be None
- Use type annotations from `typing` module (Dict, List, etc.)
- Use union types with `Union` where appropriate

### Comments

- Add inline comments for complex logic
- Use section markers for better code organization (`# --- Section Name ---`)
- Mark future improvements with `# TODO: description`

### Code Formatting

- 4 spaces for indentation (no tabs)
- Maximum line length of 88 characters (same as Black)
- Use Black for code formatting
- Use isort for import sorting

Run the formatters with:

```bash
black src tests
isort src tests
```

## Submitting Changes

1. Ensure your code follows the coding standards
2. Add tests for your changes
3. Update documentation as needed
4. Run all tests and make sure they pass
5. Commit your changes with clear commit messages
6. Push to your fork and submit a pull request

### Commit Messages

Use clear, descriptive commit messages that explain what the change does and why:

```
feat: Add SOC 2 validation support

Add support for validating documents against SOC 2 requirements.
This includes checking for the five trust service criteria and
implementing specific validation rules for each.
```

## Pull Request Process

1. Ensure your PR includes tests for new functionality
2. Update the README.md and other documentation if needed
3. Include a description of the changes in your PR
4. Link any related issues in your PR description
5. Be ready to address review feedback
6. PR will be merged once it receives approval

## Testing

- Write unit tests for all new functionality
- Write integration tests for critical paths
- Test on multiple platforms if possible
- Run tests with coverage reporting

Run tests with:

```bash
pytest
pytest --cov=src/policy_validator
```

## Documentation

- Update module docstrings for new modules
- Update function and class docstrings for changed code
- Ensure examples in docstrings are correct and work
- Update README.md for user-facing changes
- Add docstrings that follow the Google style guide

## Issue Reporting

When reporting issues, please include:

1. Description of the issue
2. Steps to reproduce the issue
3. Expected behavior
4. Actual behavior
5. Environment information (OS, Python version)
6. Screenshots if applicable

Use issue templates if available.

---

Thank you for contributing to the Policy Validator project!

