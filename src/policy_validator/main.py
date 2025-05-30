#!/usr/bin/env python3
"""Cybersecurity Policy Validator desktop application.

Version: 1.0.0
Copyright (c) 2025 Your Organization
License: MIT

This module implements a PyQt6-based GUI application for validating cybersecurity
policy documents against various standards (NIST SP 800-53, ISO 27001, SOC 2).
It provides a user-friendly interface for loading, analyzing, and validating 
policy documents in different formats (PDF, DOCX, TXT).

GUI Components:
    - DropZone: Drag-and-drop file upload area
    - ValidationStandards: Standard selection dropdown
    - SectionCheckboxes: Section selection area
    - StatusArea: Validation results display
    - ActionButtons: Validate and Clear controls

Example:
    Run the module directly to start the application:
        $ python -m policy_validator.main

Attributes:
    SUPPORTED_FORMATS (list): List of supported file extensions
    DEFAULT_STANDARD (str): Default validation standard to use
    MIN_FILE_SIZE (int): Minimum acceptable file size in bytes

Dependencies:
    - PyQt6: GUI framework
    - python-magic: File type detection
    - PyPDF2: PDF parsing
    - python-docx: Word document parsing

Constants:
    VALIDATION_STANDARDS: Dictionary defining validation requirements:
        {
            "standard_name": {
                "sections": List of required policy sections,
                "min_length": Minimum document length in characters,
                "required_structure": Boolean indicating if headers are required
            }
        }
    
    FILE_TYPE_MAPPING: Dictionary mapping MIME types to internal file types:
        {
            "application/pdf": "pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
            "application/msword": "doc",
            "text/plain": "txt"
        }

Implementation Notes:
    - GUI operations run in the main thread
    - File validation is performed synchronously
    - Future improvements could include:
        - Asynchronous file processing
        - Progress bars for large files
        - Background validation workers
        - Real-time validation updates
"""

import sys
import os
import json
import re
import magic
from typing import Dict, List, Any, Union, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, 
    QFrame, QScrollArea, QTextEdit, QPushButton, QHBoxLayout, QFileDialog,
    QComboBox, QGroupBox, QCheckBox
)
from PyQt6.QtCore import Qt, QMimeData
from PyQt6.QtGui import QDragEnterEvent, QDropEvent

# File validation constants
SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc', '.txt', '.text'}
MIN_FILE_SIZE = 50  # Minimum valid file size in bytes (empty files are typically < 50 bytes)

# MIME type mapping for supported file formats
# Maps MIME types to (internal_type, expected_extension)
MIME_TYPE_MAPPING = {
    'application/pdf': ('pdf', '.pdf'),
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ('docx', '.docx'),
    'application/msword': ('doc', '.doc'),
    'text/plain': ('txt', '.txt')
}

# Status indicators for validation results
STATUS_ICONS = {
    'success': '✅',  # Green checkmark for passed validation
    'warning': '⚠️',  # Yellow warning for issues found
    'error': '❌'     # Red X for validation failures
}


class DropZone(QFrame):
    """Widget that accepts file drops for the policy validator.

    Handles drag-and-drop operations for policy document files with visual feedback
    during drag operations. Also provides a browse button for manual file selection.

    Events:
        dragEnterEvent: Updates visual style when files are dragged over
        dragLeaveEvent: Restores normal style when drag exits
        dropEvent: Processes dropped files and sends them to main application
        
    Visual States:
        Normal: Light gray background with dashed border
        Hover: Blue border highlight
        Drag Active: Light blue background with blue border
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_app = parent  # Store reference to the main app
        self.setAcceptDrops(True)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setMinimumHeight(150)
        self.setStyleSheet(
            "QFrame {"
            "  background-color: #f0f0f0;"
            "  border: 2px dashed #aaaaaa;"
            "  border-radius: 5px;"
            "}"
            "QFrame:hover {"
            "  border-color: #3498db;"
            "}"
        )
        
        # Layout for the drop zone
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Label with instructions
        self.drop_label = QLabel("Drag and drop policy documents here\nor")
        self.drop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.drop_label)
        
        # Browse button as an alternative
        self.browse_button = QPushButton("Browse Files")
        self.browse_button.setMaximumWidth(150)
        self.browse_button.clicked.connect(self.browse_files)
        layout.addWidget(self.browse_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(
                "QFrame {"
                "  background-color: #e8f4fc;"
                "  border: 2px dashed #3498db;"
                "  border-radius: 5px;"
                "}"
            )
        
    def dragLeaveEvent(self, event):
        """Handle drag leave events."""
        self.setStyleSheet(
            "QFrame {"
            "  background-color: #f0f0f0;"
            "  border: 2px dashed #aaaaaa;"
            "  border-radius: 5px;"
            "}"
            "QFrame:hover {"
            "  border-color: #3498db;"
            "}"
        )
        
    def dropEvent(self, event: QDropEvent):
        """Process dropped files."""
        self.setStyleSheet(
            "QFrame {"
            "  background-color: #f0f0f0;"
            "  border: 2px dashed #aaaaaa;"
            "  border-radius: 5px;"
            "}"
            "QFrame:hover {"
            "  border-color: #3498db;"
            "}"
        )
        
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    file_paths.append(file_path)
            
            if file_paths:
                self.main_app.process_files(file_paths)

    def browse_files(self):
        """Open file dialog to select files."""
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter("Documents (*.pdf *.docx *.doc *.txt)")
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.main_app.process_files(file_paths)


class PolicyValidatorApp(QMainWindow):
    """Main application window for the Policy Validator.
    
    This class implements the main GUI window and validation logic for the
    cybersecurity policy validator. It manages document loading, validation
    standard selection, and result reporting.

    Attributes:
        validation_standards (Dict[str, Dict[str, Union[List[str], int, bool]]]): 
            Available validation standards and their requirements
        current_standard (str): Currently selected validation standard
        section_checkboxes (Dict[str, QCheckBox]): Mapping of section names to checkbox widgets
        loaded_files (List[Dict[str, Any]]): List of files loaded for validation
        status_area (QTextEdit): Widget displaying validation status and results
        validate_button (QPushButton): Button to trigger validation
        clear_button (QPushButton): Button to clear all files and results
        drop_zone (DropZone): Widget for drag-and-drop file uploads
        standard_selector (QComboBox): Dropdown for validation standard selection
        
    Validation Strategy:
        1. Initial file processing:
           - MIME type detection
           - Size verification
           - Extension validation
        
        2. Content extraction:
           - Text files: Direct reading
           - PDF: Text extraction (TODO)
           - Word: Document parsing (TODO)
        
        3. Policy validation:
           - Length requirements
           - Section presence
           - Document structure
           - Format-specific checks
        
        4. Result reporting:
           - Success/failure status
           - Detailed issue list
           - Warning indicators
           - Validation summary
           
    Testing:
        The application can be tested using:
        - Unit tests in tests/test_main.py
        - Integration tests in tests/test_integration.py
        - GUI tests using QTest framework
        
        Mock objects are available for:
        - File operations
        - PDF/Word document parsing
        - Validation logic
    """
    
    def __init__(self):
        """Initialize the Policy Validator application.
        
        Attributes:
            loaded_files (List[Dict[str, Any]]): List of processed files with structure:
                {
                    'path': str,      # Full path to file
                    'type': str,      # File type (pdf, docx, doc, txt)
                    'mime': str,      # MIME type from python-magic
                    'size': int,      # File size in bytes
                    'extension': str, # File extension including dot
                    'valid': bool,    # Validation status
                    'issues': List[str] # List of validation issues
                }
        """
        super().__init__()

        # Define validation standards
        self.validation_standards = {
            "NIST SP 800-53": {
                "sections": [
                    "access control",
                    "audit and accountability",
                    "security assessment",
                    "configuration management",
                    "contingency planning",
                    "identification and authentication",
                    "incident response",
                    "maintenance",
                    "media protection",
                    "physical protection",
                    "risk assessment",
                    "system and communications protection",
                ],
                "min_length": 1000,
                "required_structure": True
            },
            "ISO 27001": {
                "sections": [
                    "information security policies",
                    "organization of information security",
                    "human resource security",
                    "asset management",
                    "access control",
                    "cryptography",
                    "physical security",
                    "operations security",
                    "communications security",
                    "incident management",
                ],
                "min_length": 800,
                "required_structure": True
            },
            "SOC 2": {
                "sections": [
                    "security",
                    "availability",
                    "processing integrity",
                    "confidentiality",
                    "privacy",
                ],
                "min_length": 500,
                "required_structure": False
            },
            "Custom": {
                "sections": [
                    "password",
                    "data protection",
                    "access control",
                    "incident response",
                    "compliance"
                ],
                "min_length": 50,
                "required_structure": False
            }
        }
        
        # Set default validation standard
        self.current_standard = "Custom"
        self.section_checkboxes = {}
        
        self.setWindowTitle("Cybersecurity Policy Validator")
        self.setGeometry(100, 100, 900, 700)
        
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        # Add welcome label
        welcome_label = QLabel("Welcome to the Cybersecurity Policy Validator")
        welcome_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(welcome_label)
        
        # Add description
        description = QLabel(
            "Upload and analyze your cybersecurity policies to validate them "
            "against standards and best practices."
        )
        layout.addWidget(description)
        
        # Add validation standard selection
        standards_group = QGroupBox("Validation Standards")
        standards_layout = QVBoxLayout()
        
        # Add standard selector
        standard_label = QLabel("Select standard to validate against:")
        standards_layout.addWidget(standard_label)
        
        self.standard_selector = QComboBox()
        for standard in self.validation_standards.keys():
            self.standard_selector.addItem(standard)
        self.standard_selector.setCurrentText(self.current_standard)
        self.standard_selector.currentTextChanged.connect(self.on_standard_changed)
        standards_layout.addWidget(self.standard_selector)
        
        # Add section selection
        sections_label = QLabel("Select sections to validate:")
        standards_layout.addWidget(sections_label)
        
        # Create scrollable area for section checkboxes
        self.sections_widget = QWidget()
        self.sections_widget.setObjectName("sections_widget")
        self.sections_layout = QVBoxLayout(self.sections_widget)
        
        # Add checkboxes for the default standard
        self.update_section_checkboxes()
        
        # Add scrollarea for sections
        sections_scroll = QScrollArea()
        sections_scroll.setWidget(self.sections_widget)
        sections_scroll.setWidgetResizable(True)
        sections_scroll.setMaximumHeight(150)
        standards_layout.addWidget(sections_scroll)
        
        standards_group.setLayout(standards_layout)
        layout.addWidget(standards_group)
        
        # Add drop zone for files
        self.drop_zone = DropZone(self)
        layout.addWidget(self.drop_zone)
        
        # Add status area with scroll capability
        status_label = QLabel("Validation Status:")
        status_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(status_label)
        
        self.status_area = QTextEdit()
        self.status_area.setReadOnly(True)
        self.status_area.setMinimumHeight(200)
        layout.addWidget(self.status_area)
        
        # Add action buttons
        buttons_layout = QHBoxLayout()
        
        self.validate_button = QPushButton("Validate Policies")
        self.validate_button.setEnabled(False)  # Disabled until files are loaded
        self.validate_button.clicked.connect(self.validate_policies)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_all)
        
        buttons_layout.addWidget(self.validate_button)
        buttons_layout.addWidget(self.clear_button)
        layout.addLayout(buttons_layout)
        
        # Set central widget
        self.setCentralWidget(central_widget)
        
        # Initialize file list
        self.loaded_files = []
        
    def process_files(self, file_paths: List[str]) -> None:
        """Process the dropped or selected files.

        Args:
            file_paths: List of paths to files for processing

        File Processing Steps:
            1. Verify each file exists and is not empty
            2. Detect MIME type using python-magic
            3. Validate file extension matches content
            4. Add valid files to loaded_files list
            5. Enable validation if valid files were loaded

        Each processed file gets a file_info dict with:
            path: Full path to the file
            type: Internal file type (pdf, docx, doc, txt)
            mime: Detected MIME type
            size: File size in bytes
            extension: File extension
            valid: Validation status
            issues: List of validation issues
            
        Raises:
            OSError: If file cannot be accessed or read
            magic.MagicException: If file type cannot be determined
            UnicodeDecodeError: If text file has invalid encoding
            
        Error Handling:
            - Empty files are rejected with warning
            - Invalid file types trigger error message
            - File access issues are reported to status area
            - Mismatched extensions generate warnings
            - All errors are logged but don't crash application
        """
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            
            # Check if file is empty
            try:
                file_size = os.path.getsize(file_path)
                if file_size == 0:
                    self.log_status(f"Warning: {file_name} is empty", error=True)
                    continue
            except Exception as e:
                self.log_status(f"Error checking file size for {file_name}: {str(e)}", error=True)
                continue
            
            # Use python-magic to detect file type
            try:
                mime = magic.Magic(mime=True)
                file_type = mime.from_file(file_path)
                
                # Check if file extension matches content type
                extension = os.path.splitext(file_name)[1].lower()
                
                file_info = {
                    'path': file_path, 
                    'type': None,
                    'mime': file_type,
                    'size': file_size,
                    'extension': extension,
                    'valid': True,
                    'issues': []
                }
                
                # Check if file type is supported
                if 'pdf' in file_type:
                    file_info['type'] = 'pdf'
                    if extension != '.pdf':
                        file_info['issues'].append(f"Extension {extension} doesn't match PDF content")
                    self.loaded_files.append(file_info)
                    self.log_status(f"Added PDF: {file_name}")
                elif 'officedocument.wordprocessingml' in file_type:
                    file_info['type'] = 'docx'
                    if extension != '.docx':
                        file_info['issues'].append(f"Extension {extension} doesn't match DOCX content")
                    self.loaded_files.append(file_info)
                    self.log_status(f"Added DOCX: {file_name}")
                elif 'msword' in file_type:
                    file_info['type'] = 'doc'
                    if extension != '.doc':
                        file_info['issues'].append(f"Extension {extension} doesn't match DOC content")
                    self.loaded_files.append(file_info)
                    self.log_status(f"Added DOC: {file_name}")
                elif 'text/plain' in file_type:
                    file_info['type'] = 'txt'
                    if extension not in ('.txt', '.text'):
                        file_info['issues'].append(f"Extension {extension} doesn't match text content")
                    self.loaded_files.append(file_info)
                    self.log_status(f"Added text file: {file_name}")
                else:
                    self.log_status(f"Unsupported file type: {file_name} ({file_type})", error=True)
            except Exception as e:
                self.log_status(f"Error processing {file_name}: {str(e)}", error=True)
        
        # Enable validate button if files are loaded
        self.validate_button.setEnabled(len(self.loaded_files) > 0)
    
    def log_status(self, message: str, error: bool = False) -> None:
        """Add a message to the status area.

        Args:
            message: The message to display
            error: If True, message is shown in red (default: False)

        Display Formatting:
            - Success messages: Black text
            - Error messages: Red text
            - Status indicators:
                ✅ Success
                ⚠️ Warning
                ❌ Error

        The status area maintains a log of all operations and their results,
        scrolling automatically to show the most recent messages.
        
        Thread Safety:
            This method must be called from the main GUI thread.
            Use QMetaObject.invokeMethod for cross-thread logging.
        """
        color = "red" if error else "black"
        self.status_area.append(f'<span style="color: {color};">{message}</span>')
    
    def validate_policies(self):
        """Validate the loaded policy documents."""
        if not self.loaded_files:
            self.log_status("No files to validate.", error=True)
            return
        
        self.log_status(f"Starting validation using {self.current_standard} standard...")
        
        for file_info in self.loaded_files:
            file_name = os.path.basename(file_info['path'])
            self.log_status(f"Validating {file_name}...")
            
            # Handle any pre-existing issues
            if file_info['issues']:
                for issue in file_info['issues']:
                    self.log_status(f"⚠️ Warning: {issue}", error=True)
            
            # Validate based on file type
            if file_info['type'] == 'txt':
                self._validate_text_policy(file_info)
            elif file_info['type'] == 'pdf':
                self._validate_pdf_policy(file_info)
            elif file_info['type'] in ['doc', 'docx']:
                self._validate_word_policy(file_info)
            else:
                self.log_status(f"❌ Cannot validate {file_name}: Unknown type", error=True)
                continue
            
            # Report validation result
            if file_info['valid']:
                if not file_info['issues']:
                    self.log_status(f"✅ {file_name} validated successfully")
                else:
                    self.log_status(f"⚠️ {file_name} validated with warnings")
            else:
                self.log_status(f"❌ {file_name} failed validation", error=True)
        
        self.log_status("Validation complete!")
    
    def on_standard_changed(self, standard: str) -> None:
        """Handle change of validation standard.

        Updates the validation criteria and section checkboxes when user
        selects a different standard.

        Args:
            standard: Name of the newly selected standard

        GUI Updates:
            - Clears existing section checkboxes
            - Creates new checkboxes for selected standard
            - All sections default to checked state
            - Updates status area with change message
            - Maintains current files and validation state
        """
        self.current_standard = standard
        self.update_section_checkboxes()
        self.log_status(f"Changed validation standard to: {standard}")
    
    def update_section_checkboxes(self):
        """Update section checkboxes based on the current standard."""
        # Clear existing checkboxes
        for checkbox in self.section_checkboxes.values():
            if checkbox is not None:
                checkbox.deleteLater()
        self.section_checkboxes.clear()
        
        # Add new checkboxes for the current standard
        if self.current_standard in self.validation_standards:
            for section in self.validation_standards[self.current_standard]["sections"]:
                checkbox = QCheckBox(section.title())
                checkbox.setChecked(True)
                self.section_checkboxes[section] = checkbox
                self.sections_layout.addWidget(checkbox)

    def _validate_text_policy(self, file_info: Dict[str, Any]) -> None:
        """Validate a text-based policy file against the current standard.

        Validates policy content length, required sections, and document structure
        based on the currently selected validation standard.

        Validation Steps:
            1. Check document length against standard's minimum requirement
            2. Verify presence of all checked required sections
            3. Validate document structure if required by standard
               - Looks for Markdown headers (# Section) or
               - Numbered sections (1. Section)

        Args:
            file_info (dict): File information dictionary containing:
                path (str): Path to the policy file
                type (str): File type ('txt', 'pdf', 'doc', 'docx')
                size (int): File size in bytes
                valid (bool): Whether the file passes validation
                issues (list): List of validation issues found

        Updates:
            - file_info['valid']: Set to False if validation fails
            - file_info['issues']: Appends any validation issues found
            
        Standard Requirements:
            NIST SP 800-53:
                - Minimum 1000 characters
                - Structured format required
                - All checked sections must be present
                - Headers must follow standard format

            ISO 27001:
                - Minimum 800 characters
                - Structured format required
                - All checked sections must be present
                - Headers must follow standard format

            SOC 2:
                - Minimum 500 characters
                - Free-form format allowed
                - All checked sections must be present

            Custom:
                - Minimum 50 characters
                - Free-form format allowed
                - Selected sections must be present
                
        Extensibility:
            Custom validation rules can be added by:
            1. Adding new standards to validation_standards dict
            2. Implementing standard-specific validation logic
            3. Adding new section requirements
            4. Creating custom validators for special formats
        """
        try:
            with open(file_info['path'], 'r', encoding='utf-8') as f:
                content = f.read().lower()
            
            standard = self.validation_standards[self.current_standard]
            
            # Check for empty or very short content
            if len(content) < standard["min_length"]:
                file_info['valid'] = False
                file_info['issues'].append(
                    f"Content length ({len(content)} chars) is below minimum requirement "
                    f"({standard['min_length']} chars) for {self.current_standard}"
                )
                return
            
            # Check for required sections that are checked
            missing_sections = []
            for section, checkbox in self.section_checkboxes.items():
                if checkbox.isChecked() and section not in content:
                    missing_sections.append(section)
            
            if missing_sections:
                file_info['valid'] = False
                file_info['issues'].append(
                    f"Missing required sections for {self.current_standard}: "
                    f"{', '.join(missing_sections)}"
                )
            
            # Check for policy structure if required by the standard
            if standard["required_structure"]:
                if not re.search(r'(^|\n)#+\s+\w+', content):  # Markdown headers
                    if not re.search(r'(^|\n)\d+\.\s+\w+', content):  # Numbered lists
                        file_info['issues'].append(
                            f"{self.current_standard} requires clear section headers "
                            "or structured format"
                        )
        
        except Exception as e:
            file_info['valid'] = False
            file_info['issues'].append(f"Error validating file: {str(e)}")
    
    def _validate_pdf_policy(self, file_info):
        """Validate a PDF policy file.
        
        Note: Current implementation is a placeholder.
        TODO: Implement full PDF text extraction and validation:
            - Extract text content using PyPDF2
            - Process document structure
            - Handle text encoding
            - Extract metadata
            - Process embedded tables
        """
        try:
            # In a real implementation, we would extract text from PDF
            # and validate it. For now, we'll just check file size.
            if file_info['size'] < 1000:
                file_info['issues'].append("PDF file is suspiciously small")
            
            # Simulate a basic validation
            self._validate_text_policy(file_info)
            
        except Exception as e:
            file_info['valid'] = False
            file_info['issues'].append(f"Error validating PDF: {str(e)}")
    
    def _validate_word_policy(self, file_info):
        """Validate a Word document policy file.
        
        Note: Current implementation is a placeholder.
        TODO: Implement full Word document processing:
            - Extract text using python-docx
            - Process document structure
            - Handle formatting
            - Extract headers/sections
            - Process tables and lists
        """
        try:
            # In a real implementation, we would extract text from Word doc
            # and validate it. For now, we'll just check file size.
            if file_info['size'] < 1000:
                file_info['issues'].append("Word document is suspiciously small")
            
            # Simulate a basic validation
            self._validate_text_policy(file_info)
            
        except Exception as e:
            file_info['valid'] = False
            file_info['issues'].append(f"Error validating Word document: {str(e)}")
    
    def clear_all(self):
        """Clear all loaded files and status area."""
        self.loaded_files = []
        self.status_area.clear()
        self.validate_button.setEnabled(False)
        self.log_status("All files cleared.")


def main() -> None:
    """Initialize and run the application.

    Entry point for the policy validator application. Creates the QApplication
    instance and main window, then starts the event loop.

    Returns:
        None. Application runs until window is closed."""
    app = QApplication(sys.argv)
    window = PolicyValidatorApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

