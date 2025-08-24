"""
Logging system for the generalized agent architecture.
"""
import os
import sys
import time
from datetime import datetime
from typing import Optional, TextIO
from contextlib import contextmanager

class Logger:
    """Logger that redirects print statements to log files."""
    
    def __init__(self, task_name: str = "default"):
        self.task_name = task_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = "logs"
        self.task_dir = os.path.join(self.log_dir, task_name)
        self.log_file = os.path.join(self.task_dir, f"{task_name}_{self.timestamp}.log")
        self.original_stdout = sys.stdout
        self.log_stream: Optional[TextIO] = None
        
        # Create directories if they don't exist
        os.makedirs(self.task_dir, exist_ok=True)
    
    def start_logging(self):
        """Start logging by redirecting stdout to the log file."""
        self.log_stream = open(self.log_file, 'w', encoding='utf-8')
        sys.stdout = self.log_stream
    
    def stop_logging(self):
        """Stop logging and restore original stdout."""
        if self.log_stream:
            sys.stdout = self.original_stdout
            self.log_stream.close()
            self.log_stream = None
    
    def get_log_path(self) -> str:
        """Get the path to the current log file."""
        return self.log_file
    
    @contextmanager
    def log_context(self):
        """Context manager for logging."""
        try:
            self.start_logging()
            yield self
        finally:
            self.stop_logging()

# Global logger instance
_global_logger: Optional[Logger] = None

def setup_logging(task_name: str = "default") -> Logger:
    """Setup logging for a specific task."""
    global _global_logger
    _global_logger = Logger(task_name)
    return _global_logger

def get_logger() -> Optional[Logger]:
    """Get the current logger instance."""
    return _global_logger

def log_print(*args, **kwargs):
    """Print function that logs to file and also prints to console if needed."""
    # Print to log file
    if _global_logger and _global_logger.log_stream:
        print(*args, **kwargs, file=_global_logger.log_stream, flush=True)
    
    # Also print to console for debugging
    print(*args, **kwargs, file=sys.__stdout__, flush=True)

