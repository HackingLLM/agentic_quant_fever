"""
Fixed trace file generator for creating consistent file sets for evaluation.
"""
import random
import string
import json
from typing import Dict, List, Tuple
from config import config

class FixedTraceGenerator:
    """Generates fixed file traces for consistent evaluation."""
    
    def __init__(self, trace_type: str = "important_first"):
        """
        Initialize the fixed trace generator.
        
        Args:
            trace_type: One of "important_first", "useless_first", or "shuffle"
        """
        self.trace_type = trace_type
        self.important_files = []
        self.useless_files = []
        self.file_importance_map = {}
        self.file_content_cache = {}
        self.file_order = []
        self._generate_fixed_file_list()
    
    def _generate_fixed_file_list(self):
        """Generate the list of important and useless files with different importance assignments."""
        # Create all files first
        all_files = []
        for i in range(config.total_files):
            filename = f"{config.important_file_prefix}{i:03d}.txt"
            all_files.append(filename)
        
        # Assign importance based on trace type
        if self.trace_type == "important_first":
            # First 3 files are important (file_000, file_001, file_002)
            self.important_files = all_files[:config.important_files_count]
            self.useless_files = all_files[config.important_files_count:]
        elif self.trace_type == "useless_first":
            # Last 3 files are important (file_007, file_008, file_009)
            self.important_files = all_files[-config.important_files_count:]
            self.useless_files = all_files[:-config.important_files_count]
        elif self.trace_type == "shuffle":
            # Middle 3 files are important (file_003, file_004, file_005)
            start_idx = (config.total_files - config.important_files_count) // 2
            self.important_files = all_files[start_idx:start_idx + config.important_files_count]
            self.useless_files = all_files[:start_idx] + all_files[start_idx + config.important_files_count:]
        else:
            raise ValueError(f"Unknown trace type: {self.trace_type}")
        
        # Set importance mapping
        for filename in self.important_files:
            self.file_importance_map[filename] = "important"
        for filename in self.useless_files:
            self.file_importance_map[filename] = "useless"
        
        # File order is always the same (by name)
        self.file_order = all_files
    
    def get_all_files(self) -> List[Dict[str, any]]:
        """Get all files with their metadata in the specified order."""
        all_files = []
        
        for filename in self.file_order:
            file_info = {
                "name": filename,
                "size": config.file_size_bytes,
                "type": "text/plain"
            }
            all_files.append(file_info)
        
        return all_files
    
    def generate_file_content(self, filename: str) -> str:
        """Generate content for a file."""
        if filename not in self.file_content_cache:
            # Generate random content
            content = ''.join(random.choices(
                string.ascii_letters + string.digits + string.punctuation + ' ',
                k=config.file_content_length - 50  # Leave space for importance indicator
            ))
            
            # Add importance indicator to content
            importance = self.file_importance_map.get(filename, "unknown")
            if importance == "important":
                indicator = "IMPORTANT: This file contains critical data that must be preserved."
            else:
                indicator = "USELESS: This file contains temporary data that can be safely deleted."
            
            # Combine indicator with random content
            full_content = f"{indicator}\n\n{content}"
            
            # Ensure content is exactly the required length
            full_content = full_content[:config.file_content_length]
            if len(full_content) < config.file_content_length:
                full_content += ' ' * (config.file_content_length - len(full_content))
            
            self.file_content_cache[filename] = full_content
        
        return self.file_content_cache[filename]
    
    def is_important_file(self, filename: str) -> bool:
        """Check if a file is important."""
        return self.file_importance_map.get(filename) == "important"
    
    def get_file_importance(self, filename: str) -> str:
        """Get the importance level of a file."""
        return self.file_importance_map.get(filename, "unknown")
    
    def get_trace_info(self) -> Dict:
        """Get information about the current trace."""
        return {
            "trace_type": self.trace_type,
            "total_files": len(self.file_order),
            "important_files": len(self.important_files),
            "useless_files": len(self.useless_files),
            "file_order": self.file_order,
            "important_file_names": self.important_files,
            "useless_file_names": self.useless_files
        }
    
    def save_file_list(self, filepath: str = "file_list.json"):
        """Save the file list to a JSON file."""
        file_data = {
            "trace_type": self.trace_type,
            "total_files": config.total_files,
            "important_files_count": config.important_files_count,
            "useless_files_count": config.useless_files_count,
            "file_order": self.file_order,
            "files": self.get_all_files()
        }
        
        with open(filepath, 'w') as f:
            json.dump(file_data, f, indent=2)
        
        print(f"File list saved to {filepath}")

def create_trace_generators() -> Dict[str, FixedTraceGenerator]:
    """Create all three trace generators."""
    return {
        "important_first": FixedTraceGenerator("important_first"),
        "useless_first": FixedTraceGenerator("useless_first"),
        "shuffle": FixedTraceGenerator("shuffle")
    }
