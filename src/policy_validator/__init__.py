"""Cybersecurity Policy Validator package.

This package provides tools and utilities for validating and analyzing cybersecurity
policies against various standards and best practices. It features a GUI interface
for interactive validation, and programmatic APIs for integration with other tools.

Features:
    - Support for multiple document formats (PDF, DOCX, TXT)
    - Validation against industry standards (NIST SP 800-53, ISO 27001, SOC 2)
    - Customizable validation rules
    - Detailed validation reports
    - Real-time file monitoring for policy updates
    - GUI interface with drag-and-drop support

Usage:
    GUI Application:
        $ policy-validator
        
    Programmatic API:
        >>> from policy_validator import validate_policy
        >>> results = validate_policy("policy.pdf", standard="NIST")
        >>> print(results.summary())

Compatibility:
    - Python 3.8 or higher
    - PyQt6 for GUI components
    - Compatible with Windows, macOS, and Linux

Version History:
    0.1.0 (2025-05-30)
        - Initial release
        - Support for PDF, DOCX, and TXT files
        - Basic validation against NIST, ISO, SOC 2 standards
        - GUI interface with drag-and-drop
"""

__version__ = "0.1.0"

# Public API exports
from .main import main, run_application
from .validators.base_validator import BaseValidator
from .parsers.pdf_parser import PdfParser
from .parsers.docx_parser import DocxParser

# Standard validation function shortcuts
from .validators import (
    validate_policy,
    validate_against_nist,
    validate_against_iso,
    validate_against_soc2,
    validate_custom
)

__all__ = [
    # Main application entry points
    'main',
    'run_application',
    
    # Core validator classes
    'BaseValidator',
    
    # Parser classes
    'PdfParser',
    'DocxParser',
    
    # Validation functions
    'validate_policy',
    'validate_against_nist',
    'validate_against_iso',
    'validate_against_soc2',
    'validate_custom'
]

