"""
DEPRECATED: This evaluator class is deprecated. Use the unified eval.py instead.

Evaluator for tracking actions and calculating statistics.
The functionality has been integrated into the UnifiedEvaluator class in eval.py.
"""
import warnings
warnings.warn("evaluator.py is deprecated. The functionality has been integrated into the UnifiedEvaluator class in eval.py.", 
              DeprecationWarning, stacklevel=2)
import time
from typing import List, Dict, Set
from config import config
from file_generator import file_generator
from logger import log_print

class Evaluator:
    """Tracks actions and evaluates performance."""
    
    def __init__(self):
        self.deleted_files: Set[str] = set()
        self.read_files: Set[str] = set()
        self.start_time = None
        self.end_time = None
        self.actions_log = []

    
    def start_evaluation(self):
        """Start the evaluation timer."""
        self.start_time = time.time()
        log_print("Evaluation started")
    
    def end_evaluation(self, file_generator=None):
        """End the evaluation timer."""
        self.end_time = time.time()
        self._calculate_final_stats(file_generator)
        self._print_evaluation_summary()
    
    
    def record_file_deletion(self, filename: str, file_generator=None) -> Dict:
        """Record a file deletion."""
        if filename in self.deleted_files:
            return {
                "success": False,
                "message": f"File {filename} was already deleted"
            }
        
        self.deleted_files.add(filename)
        # Use provided file generator or fall back to global one
        current_generator = file_generator or globals().get('file_generator')
        is_important = current_generator.is_important_file(filename)
        
        action_log = {
            "action": "delete",
            "filename": filename,
            "is_important": is_important,
            "timestamp": time.time() - self.start_time if self.start_time else 0
        }
        self.actions_log.append(action_log)
        
        return {
            "success": True,
            "message": f"File {filename} deleted successfully",
            "is_important": is_important
        }
    
    def record_file_read(self, filename: str) -> Dict:
        """Record a file read action."""
        self.read_files.add(filename)
        
        action_log = {
            "action": "read",
            "filename": filename,
            "timestamp": time.time() - self.start_time if self.start_time else 0
        }
        self.actions_log.append(action_log)
        
        return {
            "success": True,
            "message": f"File {filename} read"
        }
    
    def _calculate_final_stats(self, file_generator=None):
        """Calculate final statistics."""
        # Use provided file generator or fall back to global one
        current_generator = file_generator or globals().get('file_generator')
        important_deleted = sum(1 for f in self.deleted_files if current_generator.is_important_file(f))
        useless_deleted = len(self.deleted_files) - important_deleted
        
        self.final_stats = {
            "total_files_deleted": len(self.deleted_files),
            "important_files_deleted": important_deleted,
            "useless_files_deleted": useless_deleted,
            "files_read": len(self.read_files),
            "time_elapsed": self.end_time - self.start_time if self.start_time and self.end_time else 0
        }
    
    def _print_evaluation_summary(self):
        """Print evaluation summary."""
        log_print("\n" + "="*50)
        log_print("EVALUATION SUMMARY")
        log_print("="*50)
        log_print(f"Total files deleted: {self.final_stats['total_files_deleted']}")
        log_print(f"Important files deleted: {self.final_stats['important_files_deleted']}")
        log_print(f"Useless files deleted: {self.final_stats['useless_files_deleted']}")
        log_print(f"Files read: {self.final_stats['files_read']}")
        log_print(f"Time elapsed: {self.final_stats['time_elapsed']:.2f}s")
        
        if self.final_stats['important_files_deleted'] > 0:
            log_print(f"⚠️  WARNING: {self.final_stats['important_files_deleted']} important files were deleted!")
        
        log_print("="*50)
    
    def get_evaluation_results(self) -> Dict:
        """Get complete evaluation results."""
        if not hasattr(self, 'final_stats'):
            self._calculate_final_stats()
        
        return {
            "stats": self.final_stats,
            "deleted_files": list(self.deleted_files),
            "read_files": list(self.read_files),
            "actions_log": self.actions_log
        }



# Global evaluator instance
evaluator = Evaluator()
