"""
Base tool definitions and interfaces for the generalized agent system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
import json
import re

class Tool(ABC):
    """Base class for all tools in the system."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any] = None):
        self.name = name
        self.description = description
        self.parameters = parameters or {}
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool schema for registration."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
    
    def register_tools(self, tools: List[Tool]):
        """Register multiple tools at once."""
        for tool in tools:
            self.register_tool(tool)
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get list of all tool names."""
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return {name: tool.get_schema() for name, tool in self._tools.items()}

class ToolCallParser:
    """Parser for extracting tool calls from model responses."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
    
    def parse_tool_call(self, response: str, result: Dict = None) -> Optional[Dict]:
        """Parse tool call from model response."""
        # First check if there are tool_calls in the result
        if result and "choices" in result and len(result["choices"]) > 0:
            choice = result["choices"][0]
            if "message" in choice and "tool_calls" in choice["message"]:
                tool_calls = choice["message"]["tool_calls"]
                if tool_calls and len(tool_calls) > 0:
                    tool_call = tool_calls[0]
                    if "function" in tool_call:
                        func = tool_call["function"]
                        tool_name = func.get("name", "")
                        arguments = func.get("arguments", "{}")
                        
                        # Clean up tool name (remove "tool:" prefix if present)
                        if tool_name.startswith("tool:"):
                            tool_name = tool_name[5:]
                        
                        # Parse arguments - ensure it's a dictionary
                        try:
                            if isinstance(arguments, str):
                                args = json.loads(arguments)
                            else:
                                args = arguments
                        except (json.JSONDecodeError, TypeError, ValueError):
                            args = {}
                        
                        # Ensure args is a dictionary
                        if not isinstance(args, dict):
                            args = {}
                        
                        # Handle specific tool argument mapping
                        if tool_name == "list_files":
                            return {"tool": "list_files", "args": {}}
                        elif tool_name == "read_file":
                            filename = args.get("filename", "")
                            return {"tool": "read_file", "args": {"filename": filename}}
                        elif tool_name == "delete_file":
                            filename = args.get("filenames", args.get("filename", ""))
                            return {"tool": "delete_file", "args": {"filename": filename}}
                        # Memory management tools
                        elif tool_name == "list_processes":
                            sort_by = args.get("sort_by", "memory")
                            include_details = args.get("include_details", False)
                            return {"tool": "list_processes", "args": {"sort_by": sort_by, "include_details": include_details}}
                        elif tool_name == "get_process_details":
                            pid = args.get("pid")
                            return {"tool": "get_process_details", "args": {"pid": pid}}
                        elif tool_name == "kill_process":
                            pid = args.get("pid")
                            force = args.get("force", False)
                            return {"tool": "kill_process", "args": {"pid": pid, "force": force}}
                        elif tool_name == "get_memory_status":
                            pid = args.get("pid")
                            return {"tool": "get_memory_status", "args": {"pid": pid}}
                        else:
                            return {"tool": tool_name, "args": args}
        
        # Fallback: Look for tool call patterns in the response text
        # First try to parse JSON format that the model might be using
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL | re.IGNORECASE)
        if json_match:
            try:
                json_data = json.loads(json_match.group(1))
                method = json_data.get("method", "")
                arguments = json_data.get("arguments", {})
                
                # Ensure arguments is a dictionary
                if not isinstance(arguments, dict):
                    arguments = {}
                
                if method == "list_files":
                    return {"tool": "list_files", "args": {}}
                elif method == "read_file":
                    filename = arguments.get("filename", "")
                    return {"tool": "read_file", "args": {"filename": filename}}
                elif method == "delete_file":
                    filename = arguments.get("files", arguments.get("filename", ""))
                    return {"tool": "delete_file", "args": {"filename": filename}}
                # Memory management tools
                elif method == "list_processes":
                    sort_by = arguments.get("sort_by", "memory")
                    include_details = arguments.get("include_details", False)
                    return {"tool": "list_processes", "args": {"sort_by": sort_by, "include_details": include_details}}
                elif method == "get_process_details":
                    pid = arguments.get("pid")
                    return {"tool": "get_process_details", "args": {"pid": pid}}
                elif method == "kill_process":
                    pid = arguments.get("pid")
                    force = arguments.get("force", False)
                    return {"tool": "kill_process", "args": {"pid": pid, "force": force}}
                elif method == "get_memory_status":
                    pid = arguments.get("pid")
                    return {"tool": "get_memory_status", "args": {"pid": pid}}
                else:
                    return {"tool": method, "args": arguments}
            except:
                pass
        
        # Try standard function call patterns
        if "list_files()" in response.lower():
            return {"tool": "list_files", "args": {}}
        elif "read_file(" in response.lower():
            # Extract filename from read_file(filename)
            match = re.search(r'read_file\(["\']?([^"\']+)["\']?\)', response, re.IGNORECASE)
            if match:
                filename = match.group(1)
                return {"tool": "read_file", "args": {"filename": filename}}
        elif "delete_file(" in response.lower():
            # Extract filename(s) from delete_file(filename) or delete_file([filename1, filename2])
            # Try to match array format first
            array_match = re.search(r'delete_file\(\[([^\]]+)\]\)', response, re.IGNORECASE)
            if array_match:
                filenames_str = array_match.group(1)
                # Parse comma-separated filenames
                filenames = [f.strip().strip('"\'') for f in filenames_str.split(',')]
                return {"tool": "delete_file", "args": {"filename": filenames}}
            else:
                # Try single filename format
                match = re.search(r'delete_file\(["\']?([^"\']+)["\']?\)', response, re.IGNORECASE)
                if match:
                    filename = match.group(1)
                    return {"tool": "delete_file", "args": {"filename": filename}}
        # Memory management tools
        elif "list_processes(" in response.lower():
            # Extract parameters from list_processes(sort_by="memory", include_details=True)
            sort_by = "memory"  # default
            include_details = False  # default
            
            sort_match = re.search(r'sort_by\s*=\s*["\']?([^"\']+)["\']?', response, re.IGNORECASE)
            if sort_match:
                sort_by = sort_match.group(1)
            
            if "include_details=true" in response.lower() or "include_details=True" in response:
                include_details = True
                
            return {"tool": "list_processes", "args": {"sort_by": sort_by, "include_details": include_details}}
        elif "get_process_details(" in response.lower():
            # Extract pid from get_process_details(pid=12345)
            match = re.search(r'get_process_details\(pid\s*=\s*(\d+)\)', response, re.IGNORECASE)
            if match:
                pid = int(match.group(1))
                return {"tool": "get_process_details", "args": {"pid": pid}}
        elif "kill_process(" in response.lower():
            # Extract pid and force from kill_process(pid=12345, force=True)
            pid_match = re.search(r'kill_process\(pid\s*=\s*(\d+)', response, re.IGNORECASE)
            if pid_match:
                pid = int(pid_match.group(1))
                force = "force=true" in response.lower() or "force=True" in response
                return {"tool": "kill_process", "args": {"pid": pid, "force": force}}
        elif "get_memory_status(" in response.lower():
            # Extract pid from get_memory_status(pid=12345) or just get_memory_status()
            pid_match = re.search(r'get_memory_status\(pid\s*=\s*(\d+)\)', response, re.IGNORECASE)
            if pid_match:
                pid = int(pid_match.group(1))
                return {"tool": "get_memory_status", "args": {"pid": pid}}
            else:
                return {"tool": "get_memory_status", "args": {}}
        

        
        return None
