# Cybersecurity Policy Validator

A desktop application for validating cybersecurity policy documents against common standards including NIST SP 800-53, ISO 27001, SOC 2, and custom requirements.

## Features

- Support for multiple document formats:
  - PDF files (.pdf)
  - Microsoft Word documents (.docx, .doc)
  - Plain text files (.txt)
- Drag-and-drop interface for easy file handling
- Multiple validation standards:
  - NIST SP 800-53
  - ISO 27001
  - SOC 2
  - Custom standards
- Customizable section validation
- Real-time validation feedback
- Automatic file type verification
- File watching capabilities for policy updates

## Requirements

- Python 3.x
- Dependencies:
  - PyQt6: GUI framework
  - python-docx: Word document parsing
  - PyPDF2: PDF parsing
  - python-magic: File type detection
  - watchdog: File system monitoring

## Installation

1. Clone the repository:
   ```bash
git clone https://github.com/nishanthc/policy_validator.git
   cd policy_validator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Launch the application:
   ```bash
   python -m policy_validator.main
   ```

2. Select a validation standard:
   - Choose from NIST SP 800-53, ISO 27001, SOC 2, or Custom
   - Select the sections you want to validate
   - Standards can be switched at any time

3. Load policy documents:
   - Drag and drop files into the application window
   - Or use the "Browse Files" button
   - Supported formats: PDF, DOCX, DOC, TXT

4. Validate policies:
   - Click "Validate Policies" to start validation
   - Results appear in the status area
   - Clear results using the "Clear" button

## Configuration

### Validation Standards

#### NIST SP 800-53
- Requires structured format
- Minimum length: 1000 characters
- Sections include:
  - Access Control
  - Audit and Accountability
  - Security Assessment
  - Configuration Management
  - Contingency Planning
  - Identification and Authentication
  - Incident Response
  - Maintenance
  - Media Protection
  - Physical Protection
  - Risk Assessment
  - System and Communications Protection

#### ISO 27001
- Requires structured format
- Minimum length: 800 characters
- Sections include:
  - Information Security Policies
  - Organization of Information Security
  - Human Resource Security
  - Asset Management
  - Access Control
  - Cryptography
  - Physical Security
  - Operations Security
  - Communications Security
  - Incident Management

#### SOC 2
- Free-form format allowed
- Minimum length: 500 characters
- Sections include:
  - Security
  - Availability
  - Processing Integrity
  - Confidentiality
  - Privacy

#### Custom Standards
- Free-form format allowed
- Minimum length: 50 characters
- Default sections:
  - Password
  - Data Protection
  - Access Control
  - Incident Response
  - Compliance

## Development

### Project Structure

```
policy_validator/
├── src/
│   └── policy_validator/
│       ├── __init__.py
│       ├── main.py              # Main application and GUI
│       ├── parsers/             # Document parsers
│       │   ├── __init__.py
│       │   ├── docx_parser.py   # Word document parser
│       │   └── pdf_parser.py    # PDF parser
│       ├── validators/          # Policy validators
│       │   ├── __init__.py
│       │   └── base_validator.py # Base validator class
│       └── utils/               # Utilities
│           ├── __init__.py
│           └── file_watcher.py  # File monitoring
├── tests/                       # Unit tests
├── README.md                    # This file
├── CONTRIBUTING.md             # Contribution guidelines
└── requirements.txt            # Python dependencies
```

### Extending the Validator

1. Create a new validator class:
```python
from policy_validator.validators.base_validator import BaseValidator

class CustomValidator(BaseValidator):
    def validate(self):
        # Implement validation logic
        self.add_result(
            section="custom_section",
            status="pass",
            message="Validation passed",
            details={"score": 100}
        )
```

2. Add parser support:
```python
from policy_validator.parsers.custom_parser import CustomParser

parser = CustomParser("document.ext")
content = parser.parse()
```

### Contributing

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

## License

MIT License - see LICENSE file for details.

# Cybersecurity Policy Validator

A GUI-based tool for validating cybersecurity policy documents against industry standards and best practices.

![Policy Validator Screenshot](resources/screenshot.png)

## Project Overview

The Cybersecurity Policy Validator is a desktop application designed to help security professionals and compliance officers validate their organization's security policies against recognized standards. The tool analyzes policy documents to identify missing sections, inadequate content, and formatting issues that might affect compliance.

This tool is designed to streamline the policy review process, reduce manual effort, and ensure that security policies are comprehensive and aligned with industry frameworks.

## Features

- **Multi-format Support**: Validates PDF, DOCX, DOC, and TXT policy documents
- **Multiple Standards**: Validate against NIST SP 800-53, ISO 27001, SOC 2, or custom requirements
- **Customizable Validation**: Toggle specific sections to include or exclude from validation
- **Intuitive GUI**: Simple drag-and-drop interface for file selection
- **Detailed Reports**: Clear validation results with specific issues identified
- **Content Analysis**: Checks for required sections, minimum content length, and proper formatting
- **Easy Integration**: Can be extended to support additional standards or validation rules

## Installation Instructions

### Prerequisites

- Python 3.8 or higher
- Operating system: Windows, macOS, or Linux
- libmagic (for file type detection)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/policy_validator.git
   cd policy_validator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -e .
   ```

4. Install system dependencies:
   - On Ubuntu/Debian:
     ```bash
     sudo apt-get install libmagic-dev
     ```
   - On macOS (using Homebrew):
     ```bash
     brew install libmagic
     ```
   - On Windows:
     No additional steps required as python-magic-bin will be installed automatically.

## Requirements

The application requires the following Python packages:
- PyQt6
- python-docx
- PyPDF2
- watchdog
- python-magic
- markdown
- requests
- python-dotenv

These dependencies are automatically installed when you run `pip install -e .`

## Quick Start Guide

1. Activate your virtual environment (if not already activated)
2. Launch the application:
   ```bash
   policy-validator
   ```
   
   Alternatively, you can run the module directly:
   ```bash
   python -m policy_validator.main
   ```

3. Using the application:
   - Select a validation standard from the dropdown
   - Choose which sections to validate by checking/unchecking items
   - Drag and drop your policy documents into the drop zone (or use the Browse button)
   - Click "Validate Policies" to analyze your documents
   - Review the results in the status area

## Validation Standards

The Policy Validator supports the following standards:

### NIST SP 800-53
The National Institute of Standards and Technology Special Publication 800-53 provides guidelines for federal information systems and organizations. The validator checks for sections covering:
- Access Control
- Audit and Accountability
- Security Assessment
- Configuration Management
- Contingency Planning
- Identification and Authentication
- Incident Response
- And more...

### ISO 27001
The International Organization for Standardization 27001 standard for information security management systems. The validator checks for sections covering:
- Information Security Policies
- Organization of Information Security
- Human Resource Security
- Asset Management
- Access Control
- Cryptography
- Physical Security
- And more...

### SOC 2
Service Organization Control 2 is a framework for service organizations to demonstrate their security controls. The validator checks for the five trust service criteria:
- Security
- Availability
- Processing Integrity
- Confidentiality
- Privacy

### Custom
You can also use a custom validation standard with your own requirements:
- Password policies
- Data protection
- Access control
- Incident response
- Compliance

## Usage Examples

### Basic Validation

1. Launch the application
2. Select "NIST SP 800-53" from the standard dropdown
3. Drag and drop your security policy document into the drop zone
4. Click "Validate Policies"
5. Review the validation results in the status area

### Custom Validation

1. Launch the application
2. Select "Custom" from the standard dropdown
3. Uncheck any sections you don't want to validate
4. Browse for your policy document using the Browse button
5. Click "Validate Policies"
6. Review the validation results

### Batch Validation

1. Launch the application
2. Select your desired standard
3. Hold Ctrl/Cmd while selecting multiple files in the file browser
4. Click "Validate Policies"
5. Results for each document will be displayed in the status area

## Contributing Guidelines

We welcome contributions to the Policy Validator project! Here's how you can help:

1. **Report Issues**: Submit bugs or request features through the issue tracker
2. **Suggest Improvements**: Provide feedback on how we can enhance the tool
3. **Submit Pull Requests**: Contribute code for new features or bug fixes

### Development Setup

1. Fork and clone the repository
2. Create a virtual environment and install dependencies in development mode:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e .[dev]
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Make your changes and add tests if applicable
5. Run tests:
   ```bash
   pytest
   ```
6. Submit a pull request with a clear description of your changes

## License Information

This project is licensed under the MIT License - see the LICENSE file for details.

```
MIT License

Copyright (c) 2025 Nishanth C

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

