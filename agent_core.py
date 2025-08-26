"""
Core agent implementation that handles model communication and tool execution.
"""
import requests
import json
import time
import re
import uuid
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    AutoTokenizer = None
from base_tools import ToolRegistry, ToolCallParser
from logger import log_print


class Logger:
    """Logger for inputs and outputs."""
    
    def __init__(self, task_name: str = "default"):
        self.task_name = task_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_dir = "logs"
        self.task_dir = os.path.join(self.log_dir, task_name)
        self.log_file = os.path.join(self.task_dir, f"{task_name}_{self.timestamp}.log")
        
        # Create directories if they don't exist
        os.makedirs(self.task_dir, exist_ok=True)
    
    def log_input(self, text: str, context: str = ""):
        """Log input."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"INPUT - {timestamp}\n")
            f.write(f"Context: {context}\n")
            f.write(f"{'='*80}\n")
            f.write(text)
            f.write(f"\n{'='*80}\n")
    
    def log_output(self, text: str, context: str = ""):
        """Log output."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"OUTPUT - {timestamp}\n")
            f.write(f"Context: {context}\n")
            f.write(f"{'='*80}\n")
            f.write(text)
            f.write(f"\n{'='*80}\n")
    
    def log_full_conversation_history(self, conversation_history: List[Dict], conversation_log: List[Dict]):
        """Log the complete conversation history at the end of execution."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"\n{'='*80}\n")
            f.write(f"FULL CONVERSATION HISTORY - {timestamp}\n")
            f.write(f"{'='*80}\n")
            
            # Add developer message first, then system message from conversation history
            for entry in conversation_history:
                if entry["role"] == "developer":
                    f.write(f"<|start|>developer<|message|>{entry['content']}<|end|>\n")
            
            for entry in conversation_history:
                if entry["role"] == "system":
                    f.write(f"<|start|>system<|message|>{entry['content']}<|end|>\n")
            
            # Add user and assistant messages from conversation log
            for entry in conversation_log:
                if entry["role"] == "user":
                    f.write(f"<|start|>user<|message|>{entry['content']}<|end|>\n")
                else:  # assistant
                    f.write(f"{entry['content']}\n")
            
            f.write(f"\n{'='*80}\n")
    
    def get_log_path(self) -> str:
        """Get the path to the log file."""
        return self.log_file


class AgentCore:
    """Core agent that handles model communication and tool execution."""
    
    def __init__(self, model_name: str = "gpt-oss:20b", ollama_url: str = "http://localhost:11434", 
                 hf_id: str = "openai/gpt-oss-20b", evaluation_type: str = "default", reasoning_level: str = "medium"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.hf_id = hf_id
        self.evaluation_type = evaluation_type
        self.reasoning_level = reasoning_level.lower()  # Normalize to lowercase
        self.conversation_history = []
        self.tool_registry = ToolRegistry()
        self.tool_parser = ToolCallParser(self.tool_registry)
        self.execution_context = {}  # Context for tool execution
        self.safe_mode = False  # Safe mode flag
        self.safety_reminder = ""  # Safety reminder to repeat
        self.step_count = 0  # Step counter for progress tracking
        
        # Initialize logger with evaluation type
        self.logger = Logger(evaluation_type)
        self.tokenizer = AutoTokenizer.from_pretrained(hf_id)
        self.harmony_segment_pattern = re.compile(r"<\|start\|>(\{.*?\})<\|message\|>(.*?)<\|end\|>", re.S)
        
        # Conversation history for logging (complete flow)
        self.conversation_log = []
        
        # Initialize conversation history with system and developer messages
        self._initialize_conversation_history()
    
    def _initialize_conversation_history(self):
        """Initialize conversation history with system and developer messages."""
        # Validate reasoning level
        valid_levels = ["low", "medium", "high"]
        if self.reasoning_level not in valid_levels:
            raise ValueError(f"Invalid reasoning_level: {self.reasoning_level}. Must be one of: {valid_levels}")
        
        # Add developer message first (will be updated with tool definitions when tools are registered)
        developer_message = {
            "role": "developer",
            "content": "# Tools\n## functions\nnamespace functions {\n// No tools registered yet\n} // namespace functions\n"
        }
        self.conversation_history.append(developer_message)
        
        # Add system message with reasoning level
        system_message = {
            "role": "system",
            "content": f"You are ChatGPT, a large language model trained by OpenAI.\nKnowledge cutoff: 2024-06\nCurrent date: 2025-08-25\n\nReasoning: {self.reasoning_level}\n\n# Valid channels: analysis, commentary, final. Channel must be included for every message.\n\nIMPORTANT: You have access to specific tools defined in the developer message. You MUST use these tools and ONLY these tools. Do NOT use container.exec or any other external tools. All tool calls must go to the commentary channel: 'functions'."
        }
        self.conversation_history.append(system_message)
    
    def render_harmony(self, messages, *, add_generation_prompt=True) -> str:
        """
        Convert messages to Harmony format.
        messages: list[{"role":"system|user|assistant","content":"..."}]
        Returns a single Harmony-formatted string.
        """
        return self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,                 # get a string, not token ids
            add_generation_prompt=add_generation_prompt  # opens assistant turn
        )
    
    def ollama_generate_raw(self, harmony_prompt, *, stream=False, options=None):
        """Generate response using Ollama with raw Harmony format."""
        # Set default options with temperature and max output length
        default_options = {
            "stop": [],
            "temperature": 0.7,
            "num_predict": 2048  # This is Ollama's parameter for max output length
        }
        
        # Merge with provided options
        if options:
            default_options.update(options)
        
        payload = {
            "model": self.model_name,
            "prompt": harmony_prompt,
            "raw": True,                   # <-- critical: return raw Harmony text
            "stream": stream,
            "options": default_options,
        }
        
        # Log Harmony input
        self.logger.log_input(harmony_prompt, "Ollama generate request")
        
        r = requests.post(f"{self.ollama_url}/api/generate",
                          headers={"Content-Type":"application/json"},
                          data=json.dumps(payload), stream=stream, timeout=600)
        r.raise_for_status()
        
        if stream:
            out = []
            for line in r.iter_lines(decode_unicode=True):
                if not line: continue
                out.append(json.loads(line).get("response",""))
            response = "".join(out)
        else:
            response_json = r.json()
            response = response_json["response"]
        
        # Log Harmony output
        self.logger.log_output(response, "Ollama generate response")
        
        return response
    
    def harmony_to_ollama_messages(self, harmony_text: str):
        """Convert Harmony format text to Ollama message format."""
        out = []
        
        # First, let's handle the special Harmony tool call format
        # Pattern: <|start|>assistant<|channel|>commentary to=functions.tool_name <|constrain|>json<|message|>{...}
        # Note: The model doesn't always include <|call|> token, so we match until the end or next token
        # Make space optional to handle both formats
        tool_call_pattern = r'<\|start\|>assistant<\|channel\|>commentary to=functions\.(\w+)\s*<\|constrain\|>json<\|message\|>(.*?)(?:<\|call\|>|<\|end\|>|$)'
        
        # Also handle the format with quotes around JSON
        tool_call_pattern_quoted = r'<\|start\|>assistant<\|channel\|>commentary to=functions\.(\w+)\s*<\|constrain\|>json<\|message\|>"(.*?)"(?:<\|call\|>|<\|end\|>|$)'
        
        # Handle the format where tool name and arguments are in JSON: to=functions <|constrain|>json<|message|>{"name":"tool_name","arguments":{}}
        tool_call_json_pattern = r'<\|start\|>assistant<\|channel\|>commentary to=functions\s*<\|constrain\|>json<\|message\|>(.*?)(?:<\|call\|>|<\|end\|>|$)'
        
        # Try both patterns: regular JSON and quoted JSON
        tool_call_matches = list(re.finditer(tool_call_pattern, harmony_text, re.S))
        tool_call_matches_quoted = list(re.finditer(tool_call_pattern_quoted, harmony_text, re.S))
        tool_call_json_matches = list(re.finditer(tool_call_json_pattern, harmony_text, re.S))
        
        # Process regular JSON matches
        for match in tool_call_matches:
            tool_name = match.group(1)
            arguments_text = match.group(2).strip()

            
            try:
                arguments = json.loads(arguments_text)
                tool_call = {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments, separators=(",", ":"))
                    }
                }
                out.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                log_print(f"✅ Successfully parsed tool call: {tool_name}")
                continue
            except Exception as e:
                log_print(f"❌ Failed to parse tool call for {tool_name}: {e}")
                # fall through to regular parsing
        
        # Process quoted JSON matches
        for match in tool_call_matches_quoted:
            tool_name = match.group(1)
            arguments_text = match.group(2).strip()

            
            try:
                arguments = json.loads(arguments_text)
                tool_call = {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments, separators=(",", ":"))
                    }
                }
                out.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                log_print(f"✅ Successfully parsed quoted tool call: {tool_name}")
                continue
            except Exception as e:
                log_print(f"❌ Failed to parse quoted tool call for {tool_name}: {e}")
                # fall through to regular parsing
        
        # Process JSON format matches (where tool name and arguments are in JSON)
        for match in tool_call_json_matches:
            json_text = match.group(1).strip()
            
            try:
                tool_data = json.loads(json_text)
                tool_name = tool_data.get("name", "unknown_tool")
                arguments = tool_data.get("arguments", {})
                
                tool_call = {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": json.dumps(arguments, separators=(",", ":"))
                    }
                }
                out.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                log_print(f"✅ Successfully parsed JSON format tool call: {tool_name}")
                continue
            except Exception as e:
                log_print(f"❌ Failed to parse JSON format tool call: {e}")
                # fall through to regular parsing
        
        # Now handle regular Harmony segments
        for meta_s, content in self.harmony_segment_pattern.findall(harmony_text):
            try:
                meta = json.loads(meta_s)
            except Exception:
                meta = {"role": "assistant"}  # fallback

            role = (meta.get("role") or "assistant").lower()
            chan = (meta.get("channel") or "final").lower()

            # Skip if this segment was already handled as a tool call
            if role == "assistant" and chan == "commentary":
                continue

            # Heuristic: assistant tool call segment (legacy format)
            if role == "assistant" and chan in ("tool","tools","function","functions"):
                try:
                    obj = json.loads(content.strip())  # expect {"name":..., "arguments": {...}, "id": "...?"}
                    tool_call = {
                        "id": obj.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": obj.get("name") or obj.get("tool_name") or obj.get("function") or obj.get("fn") or "unknown_tool",
                            "arguments": json.dumps(obj.get("arguments") or obj.get("args") or {}, separators=(",", ":"))
                        }
                    }
                    out.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                    continue
                except Exception:
                    # fall through to plain assistant content
                    pass

            if role in ("system","user","assistant"):
                out.append({"role": role, "content": content})
            elif role == "tool":
                msg = {"role": "tool", "content": content}
                tcid = meta.get("tool_call_id") or meta.get("id")
                if tcid: msg["tool_call_id"] = tcid
                out.append(msg)
            else:
                out.append({"role": "assistant", "content": content})
        return out
    
    def register_tools(self, tools: List):
        """Register tools with the agent."""
        self.tool_registry.register_tools(tools)
        # Update the parser with the new registry
        self.tool_parser = ToolCallParser(self.tool_registry)
        
        # Update developer message with tool definitions
        self._update_developer_message()
    
    def _update_developer_message(self):
        """Update the developer message with current tool definitions."""
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
        
        if tools:
            # Create tool definitions
            tool_definitions = "# Available Tools\n## functions\nnamespace functions {\n"
            tool_definitions += "// These are the ONLY tools you have access to. Use these tools and ONLY these tools.\n"
            tool_definitions += "// Do NOT use container.exec or any other external tools.\n\n"
            
            for tool in tools:
                tool_definitions += f"// {tool['function']['description']}\n"
                tool_definitions += f"type {tool['function']['name']} = (_: {{\n"
                for param_name, param_info in tool['function']['parameters']['properties'].items():
                    if 'description' in param_info:
                        tool_definitions += f"// {param_info['description']}\n"
                    tool_definitions += f"{param_name}: {param_info.get('type', 'string')}"
                    if param_name not in tool['function']['parameters'].get('required', []):
                        tool_definitions += "?"
                    tool_definitions += ",\n"
                tool_definitions += "}) => any;\n\n"
            tool_definitions += "} // namespace functions\n"
            
            # Update developer message in conversation history
            for entry in self.conversation_history:
                if entry["role"] == "developer":
                    entry["content"] = tool_definitions
                    break
    
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
        # Add safety reminder if in safe mode
        message_with_reminder = message
        if self.safe_mode and self.safety_reminder:
            message_with_reminder = f"{self.safety_reminder}\n\n{message}"
        
        # Update developer message with current tool definitions
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
        
        # Create tool definitions string
        tool_definitions = ""
        for tool_name, tool in self.tool_registry.get_all_tools().items():
            tool_definitions += f"// {tool.description}\n"
            tool_definitions += f"type {tool_name} = (_: {{\n"
            for param_name, param_info in tool.parameters.items():
                param_type = param_info.get("type", "any")
                param_desc = param_info.get("description", "")
                if param_desc:
                    tool_definitions += f"  // {param_desc}\n"
                tool_definitions += f"  {param_name}: {param_type},\n"
            tool_definitions += f"}}) => any;\n\n"
        
        developer_content = f"# Available Tools\n## functions\nnamespace functions {{\n{tool_definitions}}} // namespace functions\n"
        
        # Update the developer message in conversation history
        for msg in self.conversation_history:
            if msg["role"] == "developer":
                msg["content"] = developer_content
                break
        else:
            # If no developer message exists, add one
            self.conversation_history.append({
                "role": "developer",
                "content": developer_content
            })
        
        # Create messages for Harmony format
        # Include system message with reasoning level and developer message with tool definitions
        messages = self.conversation_history + [{"role": "user", "content": message_with_reminder}]
        
        # Convert to Harmony format
        harmony_prompt = self.render_harmony(messages, add_generation_prompt=True)
        
        # Generate response using Harmony format
        harmony_response = self.ollama_generate_raw(harmony_prompt)
        
        # Convert Harmony response back to messages
        response_messages = self.harmony_to_ollama_messages(harmony_response)
        
        # Debug logging for tool call parsing

        for i, msg in enumerate(response_messages):
            if "tool_calls" in msg:
                pass
        
        # Extract content from the response
        content = ""
        reasoning = ""
        result = {"choices": [{"message": {}}]}
        
        # First, try to extract analysis and final content directly from Harmony response
        analysis_pattern = r'<\|channel\|>analysis<\|message\|>(.*?)<\|end\|>'
        final_pattern = r'<\|start\|>assistant<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|$)'
        
        # Extract analysis content for reasoning
        analysis_matches = re.findall(analysis_pattern, harmony_response, re.S)
        if analysis_matches:
            reasoning = analysis_matches[-1].strip()
        
        # Extract final content
        final_matches = re.findall(final_pattern, harmony_response, re.S)
        if final_matches:
            content = final_matches[-1].strip()
            log_print(f"✅ Final response extracted: {content[:100]}...")
        
        # If no final content found, try alternative patterns
        if not content:
            # Try pattern without start tag
            alt_final_pattern = r'<\|channel\|>final<\|message\|>(.*?)(?:<\|end\|>|$)'
            alt_final_matches = re.findall(alt_final_pattern, harmony_response, re.S)
            if alt_final_matches:
                content = alt_final_matches[-1].strip()
                log_print(f"✅ Alternative final response extracted: {content[:100]}...")
        
        # Extract tool calls from parsed messages regardless of content
        for msg in response_messages:
            if msg["role"] == "assistant" and "tool_calls" in msg:
                result["choices"][0]["message"]["tool_calls"] = msg["tool_calls"]
                log_print(f"✅ Tool calls extracted: {msg['tool_calls']}")
                break
        
        # Fallback to parsed messages if still no content
        if not content:
            for msg in response_messages:
                if msg["role"] == "assistant":
                    content = msg.get("content", "")
                    break
        
        # Add to conversation history for model interaction
        self.conversation_history.append({"role": "user", "content": message})
        
        # Log analysis and tool calls for debugging, but keep conversation history simple
        if reasoning:
            pass
        
        # Create simple assistant message with just the final content
        assistant_message = {"role": "assistant", "content": content}
        
        # If we have tool calls, include them in the message
        if "tool_calls" in result["choices"][0]["message"]:
            assistant_message["tool_calls"] = result["choices"][0]["message"]["tool_calls"]
        
        self.conversation_history.append(assistant_message)
        
        # Add to conversation log for complete history
        self._add_to_conversation_log(message, harmony_response)
        
        return content, result, reasoning
    
    def _add_to_conversation_log(self, user_message: str, harmony_response: str):
        """Add user message and complete model response to conversation log."""
        # Add user message
        self.conversation_log.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Add complete model response (preserving all Harmony format)
        self.conversation_log.append({
            "role": "assistant", 
            "content": harmony_response,
            "timestamp": datetime.now().isoformat()
        })
    
    def _format_complete_conversation(self) -> str:
        """Format the complete conversation history for logging."""
        formatted = []
        
        # Add metadata header
        formatted.append(f"# Complete Conversation History")
        formatted.append(f"# Timestamp: {datetime.now().isoformat()}")
        formatted.append(f"# Step Count: {self.step_count}")
        formatted.append(f"# Evaluation Type: {self.evaluation_type}")
        formatted.append(f"# Model: {self.model_name}")
        formatted.append("")
        
        # Add system and developer messages from conversation history only once at the beginning
        system_added = False
        developer_added = False
        
        for entry in self.conversation_history:
            if entry["role"] == "system" and not system_added:
                formatted.append(f"<|start|>system<|message|>{entry['content']}<|end|>")
                system_added = True
            elif entry["role"] == "developer" and not developer_added:
                formatted.append(f"<|start|>developer<|message|>{entry['content']}<|end|>")
                developer_added = True
        
        # Add user and assistant messages from conversation log
        for entry in self.conversation_log:
            if entry["role"] == "user":
                formatted.append(f"<|start|>user<|message|>{entry['content']}<|end|>")
            else:  # assistant
                # The assistant content is already in Harmony format
                formatted.append(entry["content"])
        
        # Add execution context summary
        if self.execution_context:
            formatted.append("")
            formatted.append("# Execution Context Summary:")
            formatted.append(json.dumps(self.execution_context, indent=2))
        
        return "\n".join(formatted)
    
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
            
            self.step_count += 1
            log_print(f"--- Step {self.step_count} ---")
            log_print(f"Executing tool: {tool_name}")
            log_print(f"Tool args: {args}")
            
            # Execute the tool with context
            tool_response = self.execute_tool(tool_name, args, self.execution_context)
            log_print(f"Tool result: {tool_response}")
            
            return tool_response
        
        return None
    
    def run_conversation_loop(self, initial_prompt: str, max_steps: int = 50, 
                            completion_phrase: str = "TASK COMPLETED", 
                            step_delay: float = 0.5) -> Dict[str, Any]:
        """Run the main conversation loop with the agent."""
        log_print("Starting Agent Conversation with Harmony Format")
        log_print("=" * 50)
        
        # Send initial prompt
        response, result, reasoning = self.chat_with_model(initial_prompt)
        
        # Main conversation loop
        step = 1
        tool_executions = []
        
        while step <= max_steps:
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
            else:
                # No tool call detected, ask model to continue
                available_tools = ", ".join(self.tool_registry.get_tool_names())
                response, result, reasoning = self.chat_with_model(
                    f"Please continue with your task. You can use the available tools: {available_tools}."
                )
            
            step += 1
            
            # Small delay to prevent overwhelming the model
            time.sleep(step_delay)
        
        # Log the full conversation history at the end
        self.logger.log_full_conversation_history(
            self.conversation_history,
            self.conversation_log
        )
        
        return {
            "total_steps": step - 1,
            "completed": step <= max_steps and completion_phrase.upper() in response.upper(),
            "final_response": response,
            "tool_executions": tool_executions,
            "conversation_history": self.conversation_history,
            "log_path": self.logger.get_log_path()
        }
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
    
    def get_log_path(self) -> str:
        """Get the path to the log file."""
        return self.logger.get_log_path()
