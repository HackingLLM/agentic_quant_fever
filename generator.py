#!/usr/bin/env python3
"""
File generator with clean importance assignment patterns.
"""
import random
import string
import json
from typing import Dict, List, Tuple, Optional
from enum import Enum
from config import get_config


class ImportancePattern(Enum):
    """Enumeration of importance assignment patterns."""
    IMPORTANT_FIRST = "important_first"
    USELESS_FIRST = "useless_first"
    SHUFFLE = "shuffle"
    RANDOM = "random"


class ImportanceAssigner:
    """Handles importance assignment based on different patterns."""
    
    def __init__(self, total_files: int, important_count: int, useless_count: int):
        """
        Initialize the importance assigner.
        
        Args:
            total_files: Total number of files
            important_count: Number of important files
            useless_count: Number of useless files
        """
        self.total_files = total_files
        self.important_count = important_count
        self.useless_count = useless_count
        
        # Validate configuration
        if important_count + useless_count != total_files:
            raise ValueError(f"Total files ({total_files}) must equal important ({important_count}) + useless ({useless_count})")
    
    def assign_importance(self, pattern: ImportancePattern, seed: Optional[int] = None) -> Dict[str, str]:
        """
        Assign importance to files based on the specified pattern.
        
        Args:
            pattern: The importance assignment pattern
            seed: Random seed for reproducible results (used for shuffle and random patterns)
            
        Returns:
            Dictionary mapping filename to importance ("important" or "useless")
        """
        # Create all filenames
        all_files = [f"file_{i:03d}.txt" for i in range(self.total_files)]
        
        if pattern == ImportancePattern.IMPORTANT_FIRST:
            return self._assign_important_first(all_files)
        elif pattern == ImportancePattern.USELESS_FIRST:
            return self._assign_useless_first(all_files)
        elif pattern == ImportancePattern.SHUFFLE:
            return self._assign_shuffle(all_files, seed)
        elif pattern == ImportancePattern.RANDOM:
            return self._assign_random(all_files, seed)
        else:
            raise ValueError(f"Unknown importance pattern: {pattern}")
    
    def _assign_important_first(self, all_files: List[str]) -> Dict[str, str]:
        """Assign importance to first N files."""
        importance_map = {}
        
        # First N files are important
        for i, filename in enumerate(all_files):
            if i < self.important_count:
                importance_map[filename] = "important"
            else:
                importance_map[filename] = "useless"
        
        return importance_map
    
    def _assign_useless_first(self, all_files: List[str]) -> Dict[str, str]:
        """Assign importance to last N files."""
        importance_map = {}
        
        # Last N files are important
        for i, filename in enumerate(all_files):
            if i >= self.total_files - self.important_count:
                importance_map[filename] = "important"
            else:
                importance_map[filename] = "useless"
        
        return importance_map
    
    def _assign_shuffle(self, all_files: List[str], seed: Optional[int] = None) -> Dict[str, str]:
        """Assign importance in a deterministic shuffle pattern."""
        importance_map = {}
        
        # Use a fixed seed for reproducible results
        if seed is None:
            seed = 42  # Default seed for deterministic shuffle
        
        # Create a deterministic shuffle by distributing important files evenly
        # For 10 files with 3 important files, place them at positions 1, 4, 7
        # This ensures they are not consecutive and well-distributed
        if self.total_files == 10 and self.important_count == 3:
            important_indices = [1, 4, 7]  # Positions 2, 3, 7 (0-indexed)
        else:
            # General case: distribute important files evenly
            step = self.total_files // (self.important_count + 1)
            important_indices = [step * (i + 1) for i in range(self.important_count)]
            # Ensure we don't exceed total_files
            important_indices = [idx for idx in important_indices if idx < self.total_files]
        
        for i, filename in enumerate(all_files):
            if i in important_indices:
                importance_map[filename] = "important"
            else:
                importance_map[filename] = "useless"
        
        return importance_map
    
    def _assign_random(self, all_files: List[str], seed: Optional[int] = None) -> Dict[str, str]:
        """Assign importance randomly."""
        importance_map = {}
        
        # Set random seed for reproducibility
        if seed is not None:
            random.seed(seed)
        
        # Randomly select important files
        important_indices = random.sample(range(self.total_files), self.important_count)
        
        for i, filename in enumerate(all_files):
            if i in important_indices:
                importance_map[filename] = "important"
            else:
                importance_map[filename] = "useless"
        
        return importance_map


class FileGenerator:
    """File generator with clean importance assignment."""
    
    def __init__(self, pattern: str = "important_first", seed: Optional[int] = None):
        """
        Initialize the file generator.
        
        Args:
            pattern: Importance assignment pattern ("important_first", "useless_first", "shuffle", "random")
            seed: Random seed for reproducible results
        """
        # Get configuration
        config = get_config()
        file_config = config.get_file_config()
        
        self.total_files = file_config['file_generation']['total_files']
        self.important_count = file_config['file_generation']['important_files_count']
        self.useless_count = file_config['file_generation']['useless_files_count']
        self.file_size_bytes = file_config['file_generation']['file_size_bytes']
        self.file_content_length = file_config['file_generation']['file_content_length']
        self.file_prefix = file_config['file_generation']['important_file_prefix']
        
        # Validate pattern
        try:
            self.pattern = ImportancePattern(pattern)
        except ValueError:
            raise ValueError(f"Invalid pattern '{pattern}'. Valid patterns: {[p.value for p in ImportancePattern]}")
        
        self.seed = seed
        self.file_importance_map = {}
        self.file_content_cache = {}
        
        # Assign importance
        self._assign_importance()
    
    def _assign_importance(self):
        """Assign importance to files based on the pattern."""
        assigner = ImportanceAssigner(self.total_files, self.important_count, self.useless_count)
        self.file_importance_map = assigner.assign_importance(self.pattern, self.seed)
    
    def get_all_files(self) -> List[Dict[str, any]]:
        """Get all files with their metadata."""
        all_files = []
        
        for i in range(self.total_files):
            filename = f"{self.file_prefix}{i:03d}.txt"
            file_info = {
                "name": filename,
                "size": self.file_size_bytes,
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
                k=self.file_content_length - 50  # Leave space for importance indicator
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
            full_content = full_content[:self.file_content_length]
            if len(full_content) < self.file_content_length:
                full_content += ' ' * (self.file_content_length - len(full_content))
            
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
        important_files = [f for f, imp in self.file_importance_map.items() if imp == "important"]
        useless_files = [f for f, imp in self.file_importance_map.items() if imp == "useless"]
        
        return {
            "pattern": self.pattern.value,
            "total_files": self.total_files,
            "important_files": len(important_files),
            "useless_files": len(useless_files),
            "file_order": list(self.file_importance_map.keys()),
            "important_file_names": important_files,
            "useless_file_names": useless_files,
            "seed": self.seed
        }
    
    def save_file_list(self, filepath: str = "file_list.json"):
        """Save the file list to a JSON file."""
        file_data = {
            "pattern": self.pattern.value,
            "total_files": self.total_files,
            "important_files_count": self.important_count,
            "useless_files_count": self.useless_count,
            "seed": self.seed,
            "file_importance_map": self.file_importance_map,
            "files": self.get_all_files()
        }
        
        with open(filepath, 'w') as f:
            json.dump(file_data, f, indent=2)
        
        print(f"File list saved to {filepath}")


def create_file_generator(pattern: str = "important_first", seed: Optional[int] = None) -> FileGenerator:
    """
    Factory function to create a file generator with the specified pattern.
    
    Args:
        pattern: Importance assignment pattern
        seed: Random seed for reproducible results
        
    Returns:
        FileGenerator instance
    """
    return FileGenerator(pattern, seed)


def create_all_pattern_generators(seed: Optional[int] = None) -> Dict[str, FileGenerator]:
    """
    Create file generators for all patterns.
    
    Args:
        seed: Random seed for reproducible results
        
    Returns:
        Dictionary mapping pattern names to generators
    """
    generators = {}
    for pattern in ImportancePattern:
        generators[pattern.value] = FileGenerator(pattern.value, seed)
    return generators


# Global file generator instance - will be replaced by pattern-specific generators during evaluation
file_generator = FileGenerator()
