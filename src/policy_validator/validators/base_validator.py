"""Base validator framework for policy document validation.

This module provides the abstract base class and core functionality for
implementing policy document validators. It defines the interface and
common utilities for validating documents against different standards.

The framework supports validation against multiple standards:
    - NIST SP 800-53
    - ISO 27001
    - SOC 2
    - Custom standards

Example:
    class CustomValidator(BaseValidator):
        def validate(self):
            if len(self.document_content['text']) < 1000:
                self.add_result(
                    section="general",
                    status="fail",
                    message="Document too short",
                    details={"length": len(self.document_content['text'])}
                )

Implementation Guidelines:
    1. Inherit from BaseValidator
    2. Implement validate() method
    3. Use add_result() for validation results
    4. Return results via get_results()
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Literal, Optional
from datetime import datetime


class BaseValidator(ABC):
    """Abstract base class for policy document validators.

    This class defines the interface and provides common functionality
    for policy document validators. Subclasses must implement the
    validate() method to provide specific validation logic.

    Attributes:
        document_content (Dict[str, Any]): Parsed document content
        validation_results (List[Dict[str, Any]]): Validation results
        standard_name (str): Name of the validation standard
        validation_options (Dict[str, Any]): Standard-specific options

    Validation Framework:
        1. Initialize validator with document content
        2. Configure validation options
        3. Run validation
        4. Collect and return results

    Error Handling:
        - Invalid document format
        - Missing required sections
        - Insufficient content
        - Structure violations
    """

    def __init__(self, document_content: Dict[str, Any], standard_name: str = "custom"):
        """Initialize the validator.

        Args:
            document_content: Parsed document content including:
                text (str): Full document text
                metadata (dict): Document metadata
                structure (dict): Document structure info
            standard_name: Name of the validation standard to apply

        The document_content structure depends on the parser used:
            - PDF: PDF parser output
            - DOCX: Word document parser output
            - TXT: Basic text content
        """
        self.document_content = document_content
        self.validation_results = []
        self.standard_name = standard_name
        self.validation_options = {}

    @abstractmethod
    def validate(self) -> None:
        """Validate the document content against the standard.

        This method must be implemented by validator subclasses to provide
        standard-specific validation logic.

        Implementation Requirements:
            1. Check document structure requirements
            2. Validate section presence and content
            3. Apply standard-specific rules
            4. Add results using add_result()

        Example Implementation:
            def validate(self):
                # Check document length
                self._validate_length()
                
                # Check required sections
                self._validate_sections()
                
                # Check formatting
                self._validate_format()
        """
        pass

    def add_result(self, section: str, status: Literal["pass", "fail", "warning"],
                  message: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Add a validation result.

        Args:
            section: Section of the policy being validated
            status: Validation status ("pass", "fail", "warning")
            message: Description of the validation result
            details: Optional additional result information

        Result Format:
            {
                "timestamp": ISO format timestamp,
                "section": section name,
                "status": validation status,
                "message": result description,
                "details": additional information (optional)
            }

        Example:
            validator.add_result(
                section="access_control",
                status="fail",
                message="Missing required subsections",
                details={"missing": ["authentication", "authorization"]}
            )
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "section": section,
            "status": status,
            "message": message
        }
        if details:
            result["details"] = details
        self.validation_results.append(result)

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all validation results.

        Returns:
            List of validation results, each containing:
                timestamp (str): When the result was recorded
                section (str): Section that was validated
                status (str): Validation status
                message (str): Result description
                details (dict, optional): Additional information

        The results are ordered by timestamp, earliest first.
        """
        return self.validation_results

    def set_validation_options(self, options: Dict[str, Any]) -> None:
        """Configure validation options.

        Args:
            options: Dictionary of validation options:
                min_length (int): Minimum document length
                required_sections (list): Required section names
                structure_required (bool): Whether to enforce structure
                custom_rules (dict): Standard-specific rules

        Example:
            validator.set_validation_options({
                "min_length": 1000,
                "required_sections": ["security", "privacy"],
                "structure_required": True,
                "custom_rules": {"max_section_length": 5000}
            })
        """
        self.validation_options = options

    def _validate_basic_requirements(self) -> bool:
        """Validate basic document requirements.

        Checks fundamental requirements that apply to all standards:
            - Document is not empty
            - Minimum length requirements
            - Basic structure presence
            - Required metadata

        Returns:
            bool: True if basic requirements are met

        This is a helper method for subclasses to use in their
        validate() implementations.
        """
        if not self.document_content.get('text'):
            self.add_result(
                section="general",
                status="fail",
                message="Document is empty"
            )
            return False

        min_length = self.validation_options.get('min_length', 0)
        if len(self.document_content['text']) < min_length:
            self.add_result(
                section="general",
                status="fail",
                message=f"Document length below minimum requirement of {min_length} characters",
                details={"current_length": len(self.document_content['text'])}
            )
            return False

        return True

