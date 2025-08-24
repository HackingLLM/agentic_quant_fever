"""
File generator for creating mock files and content.
"""
import random
import string
import json
from typing import Dict, List, Tuple
from config import config

class FileGenerator:
    """Generates mock files and content for the evaluation."""
    
    def __init__(self):
        self.important_files = []
        self.useless_files = []
        self.file_importance_map = {}
        self.file_content_cache = {}
        self._generate_file_list()
    
    def _generate_file_list(self):
        """Generate the list of important and useless files."""
        # Generate important files
        count_important = 0
        count_useless = 0
        for i in range(config.total_files):
            if random.random() < config.important_files_count / config.total_files:
                count_important += 1
                important_file = f"{config.important_file_prefix}{i:03d}.txt"
                self.important_files.append(important_file)
                self.file_importance_map[important_file] = "important"
            else:
                count_useless += 1
                useless_file = f"{config.useless_file_prefix}{i:03d}.txt"
                self.useless_files.append(useless_file)
                self.file_importance_map[useless_file] = "useless"
        
        
    
    def get_all_files(self) -> List[Dict[str, any]]:
        """Get all files with their metadata."""
        all_files = []
        
        for filename in self.important_files + self.useless_files:
            file_info = {
                "name": filename,
                "size": config.file_size_bytes,
                "type": "text/plain"
            }
            all_files.append(file_info)
        
        return all_files
    
    def generate_file_content(self, filename: str) -> str:
        """Generate random content for a file."""
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
    
    def save_file_list(self, filepath: str = "file_list.json"):
        """Save the file list to a JSON file."""
        file_data = {
            "total_files": config.total_files,
            "important_files_count": config.important_files_count,
            "useless_files_count": config.useless_files_count,
            "files": self.get_all_files()
        }
        
        with open(filepath, 'w') as f:
            json.dump(file_data, f, indent=2)
        
        print(f"File list saved to {filepath}")

# Global file generator instance
file_generator = FileGenerator()
