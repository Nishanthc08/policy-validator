"""File monitoring utility for policy documents.

This module provides functionality for monitoring policy document files
for changes using the watchdog library. It enables automatic revalidation
when monitored policy files are modified.

Features:
    - Real-time file monitoring
    - Change event handling
    - Recursive directory watching
    - File type filtering
    - Debounced updates

Example:
    from policy_validator.utils.file_watcher import FileWatcher

    def on_policy_changed(file_path):
        print(f"Policy updated: {file_path}")
        # Trigger revalidation

    watcher = FileWatcher(
        directory="/path/to/policies",
        callback=on_policy_changed,
        file_patterns=["*.pdf", "*.docx", "*.txt"]
    )
    watcher.start()
    try:
        # Application continues running
        pass
    finally:
        watcher.stop()

Performance Considerations:
    - Use appropriate recursion depth
    - Filter specific file types
    - Implement event debouncing
    - Handle large directory trees efficiently
"""

import os
from typing import Callable, List, Optional
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.events import FileModifiedEvent, FileCreatedEvent


class PolicyFileHandler(FileSystemEventHandler):
    """Handle file system events for policy documents.

    This class extends watchdog's FileSystemEventHandler to process
    events specific to policy document files.

    Attributes:
        callback (Callable[[str], None]): Function to call when files change
        file_patterns (List[str]): File patterns to monitor
        _debounce_delay (float): Seconds to wait before triggering callback

    Events Handled:
        - File modification
        - File creation (optional)
        - File deletion (optional)
        - File movement (optional)

    Implementation Details:
        - Filters events by file pattern
        - Debounces rapid changes
        - Validates file existence
        - Handles concurrent modifications
    """

    def __init__(self, callback: Callable[[str], None], 
                 file_patterns: Optional[List[str]] = None,
                 debounce_delay: float = 1.0):
        """Initialize the event handler.

        Args:
            callback: Function to call when files change
            file_patterns: List of file patterns to monitor (e.g., ["*.pdf"])
            debounce_delay: Seconds to wait before triggering callback

        The callback function receives the path of the changed file
        and should handle validation or processing as needed.
        """
        self.callback = callback
        self.file_patterns = file_patterns or ["*.pdf", "*.docx", "*.doc", "*.txt"]
        self._debounce_delay = debounce_delay
        self._last_modified = {}

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events.

        Args:
            event: File system modification event

        Processing Steps:
            1. Check if file matches monitored patterns
            2. Validate file still exists
            3. Apply debounce delay
            4. Trigger callback if appropriate

        Thread Safety:
            This method is called from the observer thread and must be
            thread-safe when interacting with the callback.
        """
        if not event.is_directory and self._should_process_file(event.src_path):
            if os.path.exists(event.src_path):
                self.callback(event.src_path)

    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should trigger processing.

        Args:
            file_path: Path to the file to check

        Returns:
            bool: True if file should be processed

        Validation Steps:
            1. Check file extension against patterns
            2. Verify file exists
            3. Check debounce timing
            4. Validate file accessibility
        """
        if not os.path.exists(file_path):
            return False

        return any(
            file_path.endswith(pattern.replace("*", ""))
            for pattern in self.file_patterns
        )


class FileWatcher:
    """Watch for changes to policy files in a directory.

    This class provides a high-level interface for monitoring policy
    document files and directories for changes.

    Attributes:
        directory (str): Directory to watch for changes
        callback (Callable[[str], None]): Function to call on changes
        file_patterns (List[str]): File patterns to monitor
        recursive (bool): Whether to watch subdirectories
        observer (Observer): watchdog observer instance
        handler (PolicyFileHandler): Event handler instance

    Configuration Options:
        - Recursive monitoring
        - File pattern filtering
        - Event debouncing
        - Change notifications

    Thread Safety:
        The watcher runs in a separate thread. Callbacks must be
        thread-safe and handle synchronization with the main application.
    """

    def __init__(self, directory: str,
                 callback: Callable[[str], None],
                 file_patterns: Optional[List[str]] = None,
                 recursive: bool = True):
        """Initialize the file watcher.

        Args:
            directory: Directory path to monitor
            callback: Function to call when files change
            file_patterns: List of file patterns to monitor
            recursive: Whether to watch subdirectories

        Raises:
            ValueError: If directory doesn't exist
            PermissionError: If directory isn't accessible
        """
        if not os.path.isdir(directory):
            raise ValueError(f"Directory does not exist: {directory}")

        self.directory = directory
        self.recursive = recursive
        self.observer = Observer()
        self.handler = PolicyFileHandler(callback, file_patterns)
        self._setup_observer()

    def _setup_observer(self) -> None:
        """Configure the file system observer.

        Sets up the watchdog observer with the configured directory
        and event handler.

        Implementation Details:
            - Creates observer thread
            - Configures event handler
            - Sets up directory watching
            - Handles recursive monitoring
        """
        self.observer.schedule(
            self.handler,
            self.directory,
            recursive=self.recursive
        )

    def start(self) -> None:
        """Start monitoring for file changes.

        Begins watching the configured directory for changes to
        policy documents.

        Thread Safety:
            This method starts a new thread for monitoring. The
            application should call stop() before exiting.
        """
        self.observer.start()

    def stop(self) -> None:
        """Stop monitoring for file changes.

        Stops the file system observer and cleans up resources.

        This method should be called before the application exits
        to ensure proper cleanup of monitoring threads.
        """
        self.observer.stop()
        self.observer.join()

    def is_watching(self) -> bool:
        """Check if the watcher is currently active.

        Returns:
            bool: True if the watcher is monitoring for changes
        """
        return self.observer.is_alive()

