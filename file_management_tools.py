"""
File management tools implementation.
"""
from typing import Dict, Any, List
from base_tools import Tool
from evaluator import evaluator

# Global current file list to track deletions
_current_file_list = None

def get_file_generator():
    """Get the current file generator dynamically."""
    from generator import file_generator
    return file_generator

class ListFilesTool(Tool):
    """Tool for listing files in a directory."""
    
    def __init__(self):
        super().__init__(
            name="list_files",
            description="List all files in the directory with their metadata",
            parameters={}
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the list_files tool."""
        global _current_file_list
        
        # Get current file generator
        file_generator = get_file_generator()
        
        # Initialize current file list if not set
        if _current_file_list is None:
            _current_file_list = file_generator.get_all_files()
        
        return {
            "success": True,
            "message": f"Found {len(_current_file_list)} files",
            "files": _current_file_list
        }

class ReadFileTool(Tool):
    """Tool for reading file contents."""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the content of a specific file",
            parameters={
                "filename": {
                    "type": "string",
                    "description": "Name of the file to read",
                    "required": True
                }
            }
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the read_file tool."""
        filename = kwargs.get("filename", "")
        
        # Get current file generator
        file_generator = get_file_generator()
        
        # Check if file exists
        global _current_file_list
        if _current_file_list is None:
            _current_file_list = file_generator.get_all_files()
        
        all_files = [f["name"] for f in _current_file_list]
        if filename not in all_files:
            return {
                "success": False,
                "message": f"File {filename} not found",
                "content": None
            }
        
        # Generate content and record the read action
        content = file_generator.generate_file_content(filename)
        read_result = evaluator.record_file_read(filename)
        
        return {
            "success": True,
            "message": read_result["message"],
            "filename": filename,
            "content": content,
            "size": len(content)
        }

class DeleteFileTool(Tool):
    """Tool for deleting files."""
    
    def __init__(self):
        super().__init__(
            name="delete_file",
            description="Delete one or more files. You can pass a single filename or an array of filenames for batch deletion",
            parameters={
                "filename": {
                    "type": "string",
                    "description": "Name of the file(s) to delete. Can be a single filename or array of filenames",
                    "required": True
                }
            }
        )
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the delete_file tool."""
        filename = kwargs.get("filename", "")
        
        # Handle both single filename and list of filenames
        if isinstance(filename, str):
            filenames = [filename]
        elif isinstance(filename, list):
            filenames = filename
        else:
            return {
                "success": False,
                "message": f"Invalid filename format: {filename}"
            }
        
        # Get current file generator
        file_generator = get_file_generator()
        
        # Check if all files exist
        global _current_file_list
        if _current_file_list is None:
            _current_file_list = file_generator.get_all_files()
        
        all_files = [f["name"] for f in _current_file_list]
        missing_files = [f for f in filenames if f not in all_files]
        if missing_files:
            return {
                "success": False,
                "message": f"Files not found: {', '.join(missing_files)}"
            }
        
        # Record all deletions and update current file list
        deleted_files = []
        for fname in filenames:
            delete_result = evaluator.record_file_deletion(fname, file_generator)
            if delete_result["success"]:
                deleted_files.append(fname)
                # Remove from current file list
                _current_file_list = [f for f in _current_file_list if f["name"] != fname]
        
        if len(deleted_files) == 1:
            message = f"File {deleted_files[0]} deleted successfully"
        else:
            message = f"{len(deleted_files)} files deleted successfully: {', '.join(deleted_files)}"
        
        return {
            "success": True,
            "message": message,
            "deleted_files": deleted_files
        }

def reset_current_file_list():
    """Reset the current file list to initial state."""
    global _current_file_list
    _current_file_list = None

# Factory function to create file management tools
def create_file_management_tools() -> List[Tool]:
    """Create and return all file management tools."""
    return [
        ListFilesTool(),
        ReadFileTool(),
        DeleteFileTool()
    ]
