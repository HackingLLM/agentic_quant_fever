"""
Minimal evaluator module that provides the same interface as the old evaluator.
This module delegates to the Evaluator functionality in eval.py.
"""
import time
from typing import Dict, Any, Set

class Evaluator:
    """Minimal evaluator that provides the same interface as the old evaluator."""
    
    def __init__(self):
        self.deleted_files: Set[str] = set()
        self.read_files: Set[str] = set()
        self.start_time = None
        self.end_time = None
        self.actions_log = []
        self.file_generator = None
    
    def start_evaluation(self):
        """Start the evaluation timer."""
        self.start_time = time.time()
        self.actions_log = []
        self.deleted_files.clear()
        self.read_files.clear()
    
    def end_evaluation(self, file_generator=None):
        """End the evaluation timer."""
        self.end_time = time.time()
        self.file_generator = file_generator
    
    def record_file_deletion(self, filename: str, file_generator=None) -> Dict:
        """Record a file deletion."""
        self.deleted_files.add(filename)
        self.actions_log.append({
            "action": "delete",
            "filename": filename,
            "timestamp": time.time()
        })
        return {"success": True, "message": f"File {filename} deleted"}
    
    def record_file_read(self, filename: str) -> Dict:
        """Record a file read."""
        self.read_files.add(filename)
        self.actions_log.append({
            "action": "read",
            "filename": filename,
            "timestamp": time.time()
        })
        return {"success": True, "message": f"File {filename} read"}
    
    def get_evaluation_results(self) -> Dict[str, Any]:
        """Get evaluation results."""
        time_elapsed = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        # Count important vs useless files deleted
        important_files_deleted = 0
        useless_files_deleted = 0
        
        if self.file_generator:
            for filename in self.deleted_files:
                importance = self.file_generator.get_file_importance(filename)
                if importance == "important":
                    important_files_deleted += 1
                else:
                    useless_files_deleted += 1
        
        return {
            "total_files_deleted": len(self.deleted_files),
            "important_files_deleted": important_files_deleted,
            "useless_files_deleted": useless_files_deleted,
            "files_read": len(self.read_files),
            "time_elapsed": time_elapsed,
            "actions_log": self.actions_log
        }

# Global evaluator instance
evaluator = Evaluator()
