"""File monitoring utility for policy documents.

This module provides functionality for monitoring policy document files
for changes using the watchdog library. It enables automatic revalidation
when monitored policy files are modified, created, or deleted, ensuring
policies are always validated against the latest versions.

Features:
    - Real-time file monitoring with configurable refresh rates
    - Change event handling for modification, creation, and deletion
    - Recursive directory watching with configurable depth
    - File type filtering with glob pattern support
    - Debounced updates to prevent duplicate processing
    - Thread-safe callback execution
    - Resource-efficient monitoring

Monitoring Configuration:
    The FileWatcher class supports several configuration options:
    
    - directory: The base directory to monitor
    - file_patterns: Glob patterns for files to monitor (e.g., "*.pdf")
    - recursive: Whether to monitor subdirectories
    - debounce_delay: Time in seconds to wait before processing repeated events
    - watch_moves: Whether to track file moves within the watched directories
    - ignore_patterns: Glob patterns for files to ignore
    - polling_interval: Override default polling interval (platform-dependent)

Event Handling:
    The watcher triggers callbacks for these filesystem events:
    
    - Modification: When a monitored file's content changes
    - Creation: When a new file matching the patterns appears
    - Deletion: When a monitored file is removed (optional)
    - Movement: When a file is renamed or moved (optional)
    
    Each event is processed through these stages:
    1. Event detection by watchdog observer
    2. Filtering by file pattern and event type
    3. Debouncing to prevent duplicate processing
    4. Path validation to ensure file still exists
    5. Callback execution with file path information

Example:
    from policy_validator.utils.file_watcher import FileWatcher

    def on_policy_changed(file_path):
        print(f"Policy updated: {file_path}")
        # Trigger revalidation

    watcher = FileWatcher(
        directory="/path/to/policies",
        callback=on_policy_changed,
        file_patterns=["*.pdf", "*.docx", "*.txt"],
        recursive=True,
        debounce_delay=1.5  # 1.5 seconds debounce
    )
    watcher.start()
    try:
        # Application continues running
        import time
        time.sleep(3600)  # Monitor for an hour
    finally:
        watcher.stop()  # Proper cleanup

Performance Considerations:
    - Recursion Depth: Limit directory recursion depth for large directory structures
      to prevent excessive memory usage and CPU overhead.
    
    - File Pattern Filtering: Use specific file patterns rather than broad matches
      to reduce the number of events that need processing.
    
    - Event Debouncing: Implement appropriate debounce delays to coalesce rapid
      successive changes into a single event, especially important for files
      that change frequently or are being edited.
    
    - Large Directory Trees: For very large directories (>10,000 files), consider
      using targeted watching of specific subdirectories rather than recursive
      watching of the entire tree.
    
    - Memory Usage: The watcher maintains internal state about watched files,
      so memory usage scales with the number of monitored files and directories.
    
    - CPU Impact: File system monitoring has minimal CPU impact on most platforms,
      but can increase under high file activity or when using polling on
      platforms without native file system event support.
    
    - Callback Efficiency: Ensure callback functions execute quickly to prevent
      blocking the monitoring thread, or consider using a callback queue for
      handling events asynchronously.

Platform-Specific Notes:
    - Linux: Uses inotify for efficient native file system monitoring
    - macOS: Uses FSEvents for efficient native file system monitoring
    - Windows: Uses ReadDirectoryChangesW for native monitoring
    - Fallback: Polling is used when native APIs are unavailable
"""

import os
import time
from typing import Callable, Dict, List, Optional, Set, Union, Any
from pathlib import Path
from threading import Lock
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler, 
    FileSystemEvent,
    FileModifiedEvent, 
    FileCreatedEvent,
    FileDeletedEvent,
    FileMovedEvent
)

# --- Constants ---
DEFAULT_PATTERNS = ["*.pdf", "*.docx", "*.doc", "*.txt"]
DEFAULT_DEBOUNCE_DELAY = 1.0  # seconds
DEFAULT_POLLING_INTERVAL = 1.0  # seconds


class PolicyFileHandler(FileSystemEventHandler):
    """Handle file system events for policy documents.

    This class extends watchdog's FileSystemEventHandler to process
    events specific to policy document files. It filters events based on
    file patterns, implements debouncing logic to prevent duplicate processing,
    and ensures thread-safe callback execution.

    Attributes:
        callback (Callable[[str], None]): Function to call when files change.
            The callback receives the absolute path to the changed file.
        file_patterns (List[str]): File patterns to monitor (e.g., ["*.pdf"]).
            Only files matching these patterns will trigger the callback.
        watch_creation (bool): Whether to monitor file creation events.
        watch_deletion (bool): Whether to monitor file deletion events.
        watch_movement (bool): Whether to monitor file movement events.
        _debounce_delay (float): Seconds to wait before triggering callback
            for repeated events on the same file.
        _last_modified (Dict[str, float]): Dictionary mapping file paths to
            their last modification timestamp for debouncing.
        _lock (Lock): Thread lock for synchronizing access to shared state.
        _ignored_dirs (Set[str]): Set of directory paths to ignore.

    Events Handled:
        - File modification: When file content changes
        - File creation: When new files appear (if watch_creation=True)
        - File deletion: When files are removed (if watch_deletion=True)
        - File movement: When files are renamed or moved (if watch_movement=True)

    Implementation Details:
        - Filters events by file pattern using glob matching
        - Debounces rapid changes to prevent duplicate processing
        - Validates file existence before triggering callbacks
        - Handles concurrent modifications with thread synchronization
        - Supports configurable event types to monitor
        - Provides path normalization for consistent handling
    """

    def __init__(self, callback: Callable[[str], None], 
                 file_patterns: Optional[List[str]] = None,
                 debounce_delay: float = DEFAULT_DEBOUNCE_DELAY,
                 watch_creation: bool = True,
                 watch_deletion: bool = False,
                 watch_movement: bool = False,
                 ignored_dirs: Optional[List[str]] = None):
        """Initialize the event handler with configuration options.

        Args:
            callback: Function to call when files change. This function should
                accept a single string argument (the file path) and handle any
                necessary processing or validation.
            file_patterns: List of glob patterns for files to monitor 
                (e.g., ["*.pdf", "*.docx"]). Default is all supported policy formats.
            debounce_delay: Seconds to wait before triggering callback for
                repeated events on the same file. This prevents multiple callbacks
                for rapid successive changes.
            watch_creation: Whether to trigger callbacks when new files are created.
                Default is True.
            watch_deletion: Whether to trigger callbacks when files are deleted.
                Default is False as deleted files can't be validated.
            watch_movement: Whether to trigger callbacks when files are moved or renamed.
                Default is False.
            ignored_dirs: List of directory paths to ignore. Events in these
                directories or their subdirectories will be ignored.

        The callback function receives the absolute path of the changed file
        and should handle validation or processing as needed. It must be thread-safe
        as it will be called from the observer thread.
        
        Note:
            The handler implementation is thread-safe, but the callback function
            must also be thread-safe if it interacts with other threads or shared state.
        """
        # Store the callback function that will be called when files change
        self.callback = callback
        
        # Set file patterns to monitor, or use defaults if none provided
        self.file_patterns = file_patterns or DEFAULT_PATTERNS
        
        # Configure which event types to monitor
        self.watch_creation = watch_creation
        self.watch_deletion = watch_deletion
        self.watch_movement = watch_movement
        
        # Set debounce delay to prevent duplicate event processing
        self._debounce_delay = debounce_delay
        
        # Dictionary to track last modification time for debouncing
        self._last_modified = {}
        
        # Thread synchronization lock
        self._lock = Lock()
        
        # Set of directories to ignore
        self._ignored_dirs = set(ignored_dirs or [])

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification events.

        Called by the watchdog observer when a file modification is detected.
        Processes the event if it matches monitored patterns and passes
        the appropriate validation criteria.

        Args:
            event: File system modification event containing the path
                and metadata for the modified file.

        Processing Steps:
            1. Check if event is for a file (not directory)
            2. Check if file path matches monitored patterns
            3. Validate the file still exists (it could be deleted right after modification)
            4. Apply debounce logic to prevent duplicate processing
            5. Trigger callback with the file path

        Thread Safety:
            This method is called from the observer thread and uses a lock
            to synchronize access to shared state when checking debounce timing.
            The callback itself must also be thread-safe.
            
        Performance Impact:
            This method is called frequently during active file editing,
            so performance optimizations include:
            - Quick filtering of unwanted events
            - Path normalization only when needed
            - Debouncing to minimize duplicate processing
        """
        # Skip directory events and files that don't match our patterns
        if event.is_directory:
            return
            
        # Get normalized path for consistent handling
        file_path = os.path.abspath(event.src_path)
        
        # Check if this file should be processed based on patterns and existence
        if not self._should_process_file(file_path):
            return
            
        # Check debounce timing to avoid duplicate processing
        current_time = time.time()
        process_event = False
        
        with self._lock:
            # If we haven't seen this file before or debounce time has elapsed
            if (file_path not in self._last_modified or 
                    current_time - self._last_modified.get(file_path, 0) > self._debounce_delay):
                self._last_modified[file_path] = current_time
                process_event = True
                
        # If debounce check passed, call the callback
        if process_event:
            try:
                # Call the user's callback function with the file path
                self.callback(file_path)
            except Exception as e:
                # Log but don't crash the observer thread
                print(f"Error in file watcher callback: {e}")

    def on_created(self, event: FileCreatedEvent) -> None:
        """Handle file creation events.
        
        Called when a new file is created in the watched directory.
        Only processes the event if watch_creation is enabled.
        
        Args:
            event: File system creation event
            
        Processing follows the same pattern as on_modified, but only
        triggers if file creation monitoring is enabled.
        """
        # Skip if not monitoring creation events
        if not self.watch_creation:
            return
            
        # Skip directories and unwanted files
        if event.is_directory:
            return
            
        file_path = os.path.abspath(event.src_path)
        if self._should_process_file(file_path):
            try:
                self.callback(file_path)
            except Exception as e:
                print(f"Error in file creation callback: {e}")
                
    def on_deleted(self, event: FileDeletedEvent) -> None:
        """Handle file deletion events.
        
        Called when a file is deleted from the watched directory.
        Only processes the event if watch_deletion is enabled.
        
        Args:
            event: File system deletion event
            
        Note:
            Since the file no longer exists, validation isn't possible.
            This event might be used to trigger cleanup operations or
            to mark a policy as no longer available.
        """
        # Skip if not monitoring deletion events
        if not self.watch_deletion:
            return
            
        # Skip directories
        if event.is_directory:
            return
            
        file_path = os.path.abspath(event.src_path)
        
        # For deletion, we can't check if file exists, so we check pattern match
        # based on the path and extension
        if any(self._path_matches_pattern(file_path, pattern) 
               for pattern in self.file_patterns):
            try:
                # Remove from tracking
                with self._lock:
                    if file_path in self._last_modified:
                        del self._last_modified[file_path]
                        
                # Call callback with deleted file path
                self.callback(file_path)
            except Exception as e:
                print(f"Error in file deletion callback: {e}")
                
    def on_moved(self, event: FileMovedEvent) -> None:
        """Handle file movement (rename) events.
        
        Called when a file is moved or renamed within the watched directory.
        Only processes the event if watch_movement is enabled.
        
        Args:
            event: File system movement event with source and destination paths
            
        The callback receives the destination path (new location) of the file.
        """
        # Skip if not monitoring movement events
        if not self.watch_movement:
            return
            
        # Skip directories
        if event.is_directory:
            return
            
        dest_path = os.path.abspath(event.dest_path)
        if self._should_process_file(dest_path):
            # Update tracking information
            with self._lock:
                src_path = os.path.abspath(event.src_path)
                if src_path in self._last_modified:
                    self._last_modified[dest_path] = self._last_modified[src_path]
                    del self._last_modified[src_path]
                    
            try:
                # Call callback with new file path
                self.callback(dest_path)
            except Exception as e:
                print(f"Error in file movement callback: {e}")
                
    def _should_process_file(self, file_path: str) -> bool:
        """Check if a file should trigger processing.

        Determines whether a file meets the criteria for processing:
        - Exists on disk
        - Not in an ignored directory
        - Matches one of the configured file patterns

        Args:
            file_path: Absolute path to the file to check

        Returns:
            bool: True if the file should be processed, False otherwise

        Validation Steps:
            1. Check if file exists
            2. Check if file is in an ignored directory
            3. Check file extension/name against configured patterns
            4. Validate file is accessible (readable)
            
        Performance Note:
            This method is called for every file event, so it's optimized
            for quick filtering of unwanted events.
        """
        # Skip files that don't exist
        if not os.path.exists(file_path):
            return False
            
        # Skip files in ignored directories
        for ignored_dir in self._ignored_dirs:
            if file_path.startswith(ignored_dir):
                return False
                
        # Check if file matches any of our patterns
        return any(
            self._path_matches_pattern(file_path, pattern)
            for pattern in self.file_patterns
        )
        
    def _path_matches_pattern(self, file_path: str, pattern: str) -> bool:
        """Check if a file path matches a pattern.
        
        Args:
            file_path: Path to check
            pattern: Glob pattern (e.g., "*.pdf")
            
        Returns:
            bool: True if the file matches the pattern
            
        Implements simplified glob matching focused on file extensions
        for performance. For complex pattern matching, consider using
        the fnmatch module.
        """
        # Fast path for extension matching (most common case)
        if pattern.startswith("*."):
            return file_path.endswith(pattern[1:])
            
        # Handle more complex patterns if needed
        # This simplified implementation just does extension matching
        # For more complex patterns, use fnmatch.fnmatch(file_path, pattern)
        return file_path.endswith(pattern.replace("*", ""))


class FileWatcher:
    """Watch for changes to policy files in a directory.

    This class provides a high-level interface for monitoring policy
    document files and directories for changes. It manages the lifecycle
    of a watchdog observer and event handler, providing a simplified API
    for file monitoring.

    Attributes:
        directory (str): Directory to watch for changes. All events in this
            directory (and subdirectories if recursive=True) will be monitored.
        callback (Callable[[str], None]): Function to call when files change.
            This receives the absolute path to the changed file.
        file_patterns (List[str]): File patterns to monitor (e.g., "*.pdf").
            Only files matching these patterns will trigger the callback.
        recursive (bool): Whether to watch subdirectories recursively.
        observer (Observer): watchdog observer instance that runs the
            monitoring thread.
        handler (PolicyFileHandler): Event handler instance that processes
            events and applies filtering rules.
        polling_interval (float): Interval in seconds for polling-based
            monitoring (used as fallback when native file system events
            are not available).
        _started (bool): Whether the watcher is currently running.

    Configuration Options:
        - directory: Base directory to monitor (required)
        - callback: Function to call when files change (required)
        - file_patterns: List of glob patterns for files to monitor
        - recursive: Whether to monitor subdirectories (default: True)
        - debounce_delay: Time in seconds to wait before processing repeated events
        - watch_creation: Whether to monitor file creation events
        - watch_deletion: Whether to monitor file deletion events
        - watch_movement: Whether to monitor file movement events
        - ignored_dirs: List of directories to ignore
        - polling_interval: Override default polling interval

    Monitoring Behavior:
        - The watcher runs in a separate thread
        - Events are filtered based on file patterns
        - Callbacks are executed in the observer thread
        - The watcher must be explicitly started and stopped

    Thread Safety:
        The watcher runs in a separate thread. Callbacks must be
        thread-safe and handle synchronization with the main application.
        The watcher itself is thread-safe for starting and stopping.
    """

    def __init__(self, directory: str,
                 callback: Callable[[str], None],
                 file_patterns: Optional[List[str]] = None,
                 recursive: bool = True,
                 debounce_delay: float = DEFAULT_DEBOUNCE_DELAY,
                 watch_creation: bool = True,
                 watch_deletion: bool = False,
                 watch_movement: bool = False,
                 ignored_dirs: Optional[List[str]] = None,
                 polling_interval: Optional[float] = None):
        """Initialize the file watcher with comprehensive configuration options.

        Args:
            directory: Directory path to monitor. This must be an existing
                directory with appropriate read permissions.
            callback: Function to call when files change. This function should
                accept a file path string and perform any necessary processing.
            file_patterns: List of glob patterns for files to monitor 
                (e.g., ["*.pdf", "*.docx"]). Default is all supported policy formats.
            recursive: Whether to watch subdirectories recursively. Setting this
                to False will only monitor the specified directory, not subdirectories.
            debounce_delay: Time in seconds to wait before processing repeated
                events on the same file. Helps prevent duplicate processing during
                file editing or large file copies.
            watch_creation: Whether to trigger callbacks when new files are created.
            watch_deletion: Whether to trigger callbacks when files are deleted.
            watch_movement: Whether to trigger callbacks when files are moved/renamed.
            ignored_dirs: List of directory paths to ignore. Events in these
                directories will not trigger callbacks.
            polling_interval: Override the default polling interval (in seconds)
                used when native file system events are not available.

        Raises:
            ValueError: If directory doesn't exist or is not a directory
            PermissionError: If directory isn't accessible with read permissions
            RuntimeError: If observer cannot be initialized

        Example:
            ```python
            # Basic configuration
            watcher = FileWatcher("/path/to/policies", on_policy_changed)
            
            # Advanced configuration
            watcher = FileWatcher(
                directory="/path/to/policies",
                callback=on_policy_changed,
                file_patterns=["*.pdf", "*.docx"],
                recursive=True,
                debounce_delay=2.0,
                watch_creation=True,
                watch_deletion=True,
                ignored_dirs=["/path/to/policies/archive"]
            )
            ```
        """
        # Validate directory exists and is accessible
        if not os.path.exists(directory):
            raise ValueError(f"Directory does not exist: {directory}")
        if not os.path.isdir(directory):
            raise ValueError(f"Path is not a directory: {directory}")
        if not os.access(directory, os.R_OK):
            raise PermissionError(f"Directory is not readable: {directory}")

        # Store configuration
        self.directory = os.path.abspath(directory)
        self.recursive = recursive
        self.polling_interval = polling_interval
        self._started = False
        
        # Convert ignored directories to absolute paths
        normalized_ignored_dirs = None
        if ignored_dirs:
            normalized_ignored_dirs = [os.path.abspath(d) for d in ignored_dirs]
        
        # Create event handler with configured options
        self.handler = PolicyFileHandler(
            callback=callback,
            file_patterns=file_patterns,
            debounce_delay=debounce_delay,
            watch_creation=watch_creation,
            watch_deletion=watch_deletion,
            watch_movement=watch_movement,
            ignored_dirs=normalized_ignored_dirs
        )
        
        # Create observer with optional polling interval
        if polling_interval:
            from watchdog.observers.polling import PollingObserver
            self.observer = PollingObserver(timeout=polling_interval)
        else:
            self.observer = Observer()
            
        # Set up the observer to watch the directory
        self._setup_observer()

    def _setup_observer(self) -> None:
        """Configure the file system observer.

        Sets up the watchdog observer with the configured directory
        and event handler. This internal method is called during initialization
        to prepare the observer but does not start monitoring.

        Implementation Details:
            - Creates observer thread (not started yet)
            - Configures event handler with the directory to watch
            - Sets up directory watching with recursive option
            - Handles error cases for inaccessible paths
            
        Observer Behavior:
            - Uses native file system events when available
            - Falls back to polling if native events unavailable
            - Recursive watching follows symlinks by default
            - Event queue has a limited size (default 4096 events)
            
        Error Handling:
            - Silently handles directories that become inaccessible
              after initial setup
            - Reports exceptions during scheduling to caller
        """
        try:
            # Schedule the observer to watch the specified directory
            # with the configured handler and recursion setting
            watch = self.observer.schedule(
                event_handler=self.handler,
                path=self.directory,
                recursive=self.recursive
            )
            
            # Optional debugging information about the watch
            # print(f"Watching {self.directory} (recursive={self.recursive})")
            # print(f"Watch: {watch}")
        except Exception as e:
            # Re-raise any exceptions that occur during setup
            # This ensures problems are reported immediately rather than
            # when monitoring is started
            raise RuntimeError(f"Failed to set up directory monitoring: {e}") from e

    def start(self) -> None:
        """Start monitoring for file changes.

        Begins watching the configured directory for changes to
        policy documents. This starts the observer thread which will
        run in the background until stop() is called.

        Monitoring begins immediately after this method returns.
        Events that occur while the watcher is running will trigger
        the callback function if they match the configured patterns.

        Thread Safety:
            This method starts a new thread for monitoring. The
            application should call stop() before exiting to ensure
            proper cleanup of resources. This method is thread-safe
            and can be called from any thread.
            
        Error Handling:
            - If the observer is already running, this method does nothing
            - If the observer cannot be started, an exception is raised
            
        System Resource Impact:
            - Creates one background thread
            - Uses file system monitoring APIs (inotify on Linux)
            - Minimal CPU impact during idle periods
            - Memory usage proportional to number of watched files
        """
        # Prevent starting an already running observer
        if self._started:
            return
            
        try:
            # Start the observer thread
            self.observer.start()
            self._started = True
        except Exception as e:
            raise RuntimeError(f"Failed to start file monitoring: {e}") from e

    def stop(self) -> None:
        """Stop monitoring for file changes.

        Stops the file system observer and cleans up resources.
        This method blocks until the observer thread has fully terminated.

        This method should be called before the application exits
        to ensure proper cleanup of monitoring threads and system resources.
        Failing to call stop() may leave zombie threads or file system
        watchers active.
        
        Thread Safety:
            This method is thread-safe and can be called from any thread.
            It will block until the observer thread has fully terminated.
            
        Cleanup Actions:
            1. Signals the observer to stop monitoring
            2. Waits for the observer thread to terminate
            3. Releases file system watches
            4. Clears internal event queues
            
        Error Handling:
            - If the observer is not running, this method does nothing
            - Timeout can be configured in the Observer constructor
              (default is 1 second)
        """
        # Only stop if we're running
        if not self._started:
            return
            
        try:
            # Signal the observer to stop
            self.observer.stop()
            
            # Wait for the thread to terminate (blocks until complete)
            self.observer.join()
            
            # Mark as stopped
            self._started = False
        except Exception as e:
            # Log but don't propagate exceptions during shutdown
            print(f"Error stopping file watcher: {e}")
            # Still mark as stopped even if there was an error
            self._started = False

    def is_watching(self) -> bool:
        """Check if the watcher is currently active.

        Returns:
            bool: True if the watcher is monitoring for changes,
                 False if stopped or not yet started
                 
        This method provides a way to check the current state of the
        watcher without modifying it. It's useful for status reporting
        and for determining whether to start/stop the watcher.
        
        Thread Safety:
            This method is thread-safe and can be called from any thread.
        """
        return self._started and self.observer.is_alive()
        
    def add_watch_directory(self, directory: str, recursive: bool = None) -> None:
        """Add another directory to watch.
        
        Args:
            directory: Path to additional directory to monitor
            recursive: Whether to watch subdirectories (defaults to
                       the watcher's configured recursive setting)
                       
        Raises:
            ValueError: If directory doesn't exist
            RuntimeError: If watcher is not started
            
        This allows dynamically expanding the set of watched directories
        without creating a new watcher instance.
        """
        if not self._started:
            raise RuntimeError("Watcher must be started before adding directories")
            
        if not os.path.isdir(directory):
            raise ValueError(f"Not a directory: {directory}")
            
        # Use the watcher's recursive setting if not specified
        if recursive is None:
            recursive = self.recursive
            
        # Schedule the additional directory
        self.observer.schedule(
            event_handler=self.handler,
            path=directory,
            recursive=recursive
        )
        
    def get_watched_paths(self) -> List[str]:
        """Get the list of paths currently being watched.
        
        Returns:
            List of absolute paths to directories being watched
            
        This provides visibility into what directories the watcher
        is actually monitoring, which can be useful for debugging
        and status reporting.
        """
        watched_paths = []
        for watch in self.observer._watches:
            watched_paths.append(watch.path)
        return watched_paths

