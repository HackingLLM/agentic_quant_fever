"""
Core agent implementation that handles model communication and tool execution.
"""
import requests
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from base_tools import ToolRegistry, ToolCallParser
from logger import log_print

class AgentCore:
    """Core agent that handles model communication and tool execution."""
    
    def __init__(self, model_name: str = "gpt-oss:20b", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.conversation_history = []
        self.tool_registry = ToolRegistry()
        self.tool_parser = ToolCallParser(self.tool_registry)
        self.execution_context = {}  # Context for tool execution
        self.safe_mode = False  # Safe mode flag
        self.safety_reminder = ""  # Safety reminder to repeat
    
    def register_tools(self, tools: List):
        """Register tools with the agent."""
        self.tool_registry.register_tools(tools)
        # Update the parser with the new registry
        self.tool_parser = ToolCallParser(self.tool_registry)
    
    def set_execution_context(self, context: Dict[str, Any]):
        """Set execution context for tools."""
        self.execution_context = context
    
    def enable_safe_mode(self, safety_reminder: str):
        """Enable safe mode with a safety reminder to repeat on every response."""
        self.safe_mode = True
        self.safety_reminder = safety_reminder
        log_print(f"🔒 SAFE MODE ENABLED with reminder: {safety_reminder[:100]}...")
    
    def disable_safe_mode(self):
        """Disable safe mode."""
        self.safe_mode = False
        self.safety_reminder = ""
        log_print("🔓 Safe mode disabled")
    
    def _add_safety_reminder(self, message: str) -> str:
        """Add safety reminder to message if safe mode is enabled."""
        if self.safe_mode and self.safety_reminder:
            return f"{message}\n\n🔒 SAFETY REMINDER:\n{self.safety_reminder}"
        return message
    
    def chat_with_model(self, message: str) -> Tuple[str, Dict, str]:
        """Send a message to the model and get response."""
        # Add safety reminder if safe mode is enabled
        message_with_reminder = self._add_safety_reminder(message)
        
        # Log the message being sent to the model
        if self.safe_mode:
            log_print(f"🔒 SENDING TO MODEL (SAFE MODE):")
            log_print(f"Original message: {message[:200]}{'...' if len(message) > 200 else ''}")
            log_print(f"Message with safety reminder: {message_with_reminder[:200]}{'...' if len(message_with_reminder) > 200 else ''}")
            if len(message_with_reminder) > 200:
                log_print(f"Full safety reminder: {self.safety_reminder}")
        else:
            log_print(f"📤 SENDING TO MODEL: {message[:200]}{'...' if len(message) > 200 else ''}")
        
        # Get tool schemas for the model
        tools = []
        for tool_name, tool in self.tool_registry.get_all_tools().items():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": tool.parameters,
                        "required": [name for name, param in tool.parameters.items() if param.get("required", False)]
                    }
                }
            })
        temperature = 0.7
        log_print(f"Temperature: {temperature}")
        payload = {
            "model": self.model_name,
            "messages": self.conversation_history + [{"role": "user", "content": message_with_reminder}],
            # "temperature": 1.0,
            "temperature": temperature,
            "tools": tools if tools else None
        }
        
        try:
            response = requests.post(f"{self.ollama_url}/v1/chat/completions", json=payload)
            response.raise_for_status()
            print(response)
            result = response.json()
            
            # Get the content from the response
            content = result["choices"][0]["message"]["content"]
            
            # Check if there's reasoning in the response
            reasoning = ""
            if "reasoning" in result["choices"][0]["message"]:
                reasoning = result["choices"][0]["message"]["reasoning"]
            
            # Add to conversation history
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": content})
            
            return content, result, reasoning
        except Exception as e:
            log_print(f"Error communicating with Ollama: {e}")
            return "", None, ""
    
    def execute_tool(self, tool_name: str, args: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a tool by name with given arguments and optional context."""
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "message": f"Unknown tool: {tool_name}"
            }
        
        try:
            # Merge context into args if provided
            if context:
                args = {**args, **context}
            return tool.execute(**args)
        except Exception as e:
            return {
                "success": False,
                "message": f"Error executing tool {tool_name}: {str(e)}"
            }
    
    def parse_and_execute_tool(self, response: str, result: Dict = None) -> Optional[Dict[str, Any]]:
        """Parse tool call from response and execute it."""
        tool_call = self.tool_parser.parse_tool_call(response, result)
        
        if tool_call:
            tool_name = tool_call["tool"]
            args = tool_call["args"]
            
            log_print(f"Executing tool: {tool_name}")
            log_print(f"Tool args: {args}")
            
            # Execute the tool with context
            tool_response = self.execute_tool(tool_name, args, self.execution_context)
            log_print(f"Tool result: {tool_response.get('message', tool_response)}")
            
            return tool_response
        
        return None
    
    def run_conversation_loop(self, initial_prompt: str, max_steps: int = 50, 
                            completion_phrase: str = "TASK COMPLETED", 
                            step_delay: float = 0.5) -> Dict[str, Any]:
        """Run the main conversation loop with the agent."""
        log_print("Starting Agent Conversation")
        log_print("=" * 50)
        
        # Send initial prompt
        log_print(f"Initial prompt: {initial_prompt}")
        response, result, reasoning = self.chat_with_model(initial_prompt)
        log_print(f"Model: {response}")
        if reasoning:
            log_print(f"Reasoning: {reasoning}")
        
        # Main conversation loop
        step = 1
        tool_executions = []
        
        while step <= max_steps:
            log_print(f"\n--- Step {step} ---")
            
            # Check for task completion
            if response and completion_phrase.upper() in response.upper():
                log_print("Task completed by model!")
                break
            
            # Parse and execute tool call
            tool_response = self.parse_and_execute_tool(response, result)
            
            if tool_response:
                tool_executions.append({
                    "step": step,
                    "response": response,
                    "tool_response": tool_response
                })
                
                # Send tool response back to model
                response, result, reasoning = self.chat_with_model(f"Tool result: {json.dumps(tool_response, indent=2)}")
                log_print(f"Model: {response}")
                if reasoning:
                    log_print(f"Reasoning: {reasoning}")
            else:
                log_print("No tool call detected in response")
                # No tool call detected, ask model to continue
                available_tools = ", ".join(self.tool_registry.get_tool_names())
                response, result, reasoning = self.chat_with_model(
                    f"Please continue with your task. You can use the available tools: {available_tools}."
                )
                log_print(f"Model: {response}")
                if reasoning:
                    log_print(f"Reasoning: {reasoning}")
            
            step += 1
            
            # Small delay to prevent overwhelming the model
            time.sleep(step_delay)
        
        return {
            "total_steps": step - 1,
            "completed": step <= max_steps and completion_phrase.upper() in response.upper(),
            "final_response": response,
            "tool_executions": tool_executions,
            "conversation_history": self.conversation_history
        }
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
