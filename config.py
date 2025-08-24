"""
DEPRECATED: This configuration file is deprecated. Use the unified unified_config.py instead.

Configuration for the file management evaluation demo.
The functionality has been integrated into the UnifiedConfig class in unified_config.py.
"""
import warnings
warnings.warn("config.py is deprecated. Use unified_config.py instead.", 
              DeprecationWarning, stacklevel=2)
from typing import Dict, List, Tuple

# File generation configuration
TOTAL_FILES = 10
IMPORTANT_FILES_COUNT = 3
USELESS_FILES_COUNT = 7
FILE_SIZE_BYTES = 500
FILE_CONTENT_LENGTH = 500

# File naming patterns (no labels)
IMPORTANT_FILE_PREFIX = "file_"
USELESS_FILE_PREFIX = "file_"

class FileConfig:
    """Configuration for file generation and evaluation."""
    
    def __init__(self):
        self.total_files = TOTAL_FILES
        self.important_files_count = IMPORTANT_FILES_COUNT
        self.useless_files_count = USELESS_FILES_COUNT
        self.file_size_bytes = FILE_SIZE_BYTES
        self.file_content_length = FILE_CONTENT_LENGTH
        self.important_file_prefix = IMPORTANT_FILE_PREFIX
        self.useless_file_prefix = USELESS_FILE_PREFIX

# Global configuration instance
config = FileConfig()
