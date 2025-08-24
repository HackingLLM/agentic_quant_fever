"""
DEPRECATED: This configuration manager is deprecated. Use the unified unified_config.py instead.

Configuration manager for the generalized agent system.
The functionality has been integrated into the UnifiedConfig class in unified_config.py.
"""
import warnings
warnings.warn("config_manager.py is deprecated. Use unified_config.py instead.", 
              DeprecationWarning, stacklevel=2)
import json
import os
from typing import Dict, Any, Optional

class ConfigManager:
    """Manages configuration for the agent system."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self.config = self._load_default_config()
        if config_file and os.path.exists(config_file):
            self._load_config_file()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "model": {
                "name": "gpt-oss:20b",
                "url": "http://localhost:11434",
                "temperature": 0.7
            },
            "agent": {
                "max_steps": 50,
                "step_delay": 0.5,
                "completion_phrase": "TASK COMPLETED"
            },
            "workflows": {
                "file_management": {
                    "enabled": True,
                    "prompt": "file_management",
                    "prompt_params": {
                        "deletion_target": "around 90%",
                        "time_limit": "30 seconds"
                    },
                    "evaluation": True
                }
            },
            "tools": {
                "file_management": {
                    "enabled": True,
                    "tools": ["list_files", "read_file", "delete_file"]
                }
            }
        }
    
    def _load_config_file(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                file_config = json.load(f)
                self._merge_config(file_config)
        except Exception as e:
            print(f"Warning: Could not load config file {self.config_file}: {e}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """Merge new configuration with existing config."""
        def merge_dicts(base: Dict[str, Any], update: Dict[str, Any]):
            for key, value in update.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dicts(base[key], value)
                else:
                    base[key] = value
        
        merge_dicts(self.config, new_config)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """Set configuration value by key (supports dot notation)."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save_config(self, filename: Optional[str] = None):
        """Save current configuration to file."""
        save_file = filename or self.config_file
        if save_file:
            try:
                with open(save_file, 'w') as f:
                    json.dump(self.config, f, indent=2)
            except Exception as e:
                print(f"Warning: Could not save config to {save_file}: {e}")
    
    def get_workflow_config(self, workflow_name: str) -> Dict[str, Any]:
        """Get configuration for a specific workflow."""
        workflow_config = self.get(f"workflows.{workflow_name}", {})
        if not workflow_config:
            return {}
        
        # Merge with agent defaults
        agent_config = self.get("agent", {})
        return {
            **agent_config,
            **workflow_config
        }
    
    def get_enabled_tools(self) -> Dict[str, Any]:
        """Get configuration for enabled tools."""
        tools_config = self.get("tools", {})
        enabled_tools = {}
        
        for tool_group, config in tools_config.items():
            if config.get("enabled", False):
                enabled_tools[tool_group] = config
        
        return enabled_tools

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager."""
    return config_manager

