"""
Qwen-Agent Adapter for The Archivist
- Integration with Qwen-Agent's advanced reasoning capabilities
- Tool use, planning, and autonomous task execution
- Enhanced reasoning for cognitive synthesis

References:
- Qwen-Agent: https://github.com/QwenLM/Qwen-Agent
"""
import logging
import time
from typing import Dict, Any, List, Optional, Union, Callable


class QwenToolStub:
    """Stub for Qwen-Agent tool if the real package isn't available"""
    
    def __init__(self, name: str, description: str, function: Optional[Callable] = None):
        self.name = name
        self.description = description
        self.function = function or (lambda **kwargs: {"result": f"Stub result for {name}"})
        self.call_count = 0
        
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool function"""
        self.call_count += 1
        if self.function:
            try:
                return self.function(**kwargs)
            except Exception as e:
                return {"error": str(e)}
        return {"result": f"Stub result for {self.name} (call #{self.call_count})"}


class QwenAgentStub:
    """Stub for Qwen-Agent if the real package isn't available"""
    
    def __init__(self, model_name: str = "qwen-14b-agent"):
        self.model_name = model_name
        self.tools = {}
        self.memory = {}
        self.call_history = []
        
    def register_tool(self, name: str, description: str, function: Optional[Callable] = None) -> bool:
        """Register a tool with the agent"""
        self.tools[name] = QwenToolStub(name, description, function)
        return True
        
    def reason(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Perform reasoning about a query"""
        # Convert query to string if it's a dict
        query_str = str(query)
        
        # Record the call
        call_id = len(self.call_history) + 1
        call_data = {
            "id": call_id,
            "query": query,
            "timestamp": time.time()
        }
        
        # Determine if we should use tools
        used_tools = []
        for name, tool in self.tools.items():
            # Simple check if tool might be relevant
            if name.lower() in query_str.lower():
                result = tool.execute(query=query)
                used_tools.append({"tool": name, "result": result})
        
        # Generate a response
        reasoning = {
            "id": call_id,
            "thoughts": f"Analyzed query: {query_str[:50]}...",
            "used_tools": used_tools,
            "conclusion": f"Stub reasoning conclusion for query. Used {len(used_tools)} tools.",
            "confidence": 0.8
        }
        
        # Update call with results
        call_data["result"] = reasoning
        self.call_history.append(call_data)
        
        return reasoning
    
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Chat with the agent"""
        history = history or []
        
        # Record in history
        response = {
            "id": len(self.call_history) + 1,
            "message": f"This is a stub response to: {message[:30]}...",
            "used_tools": []
        }
        
        self.call_history.append({
            "type": "chat",
            "message": message,
            "history": history,
            "response": response,
            "timestamp": time.time()
        })
        
        return response


# Try to load the real Qwen-Agent or fall back to stub
try:
    from qwen_agent import QwenAgent, QwenTool
    logging.info("Loaded real Qwen-Agent components")
except ImportError:
    QwenAgent = QwenAgentStub
    QwenTool = QwenToolStub
    logging.warning("Using Qwen-Agent stub implementations - for real functionality, install Qwen-Agent")


class QwenAgentAdapter:
    """Adapter for Qwen-Agent functionality in The Archivist"""
    
    def __init__(self, model_name: str = "qwen-14b-agent"):
        self.agent = QwenAgent(model_name=model_name)
        self.recent_calls = []
        self.max_recent = 50
        
        # Register some basic tools
        self.register_default_tools()
        
    def register_default_tools(self):
        """Register default tools with the Qwen-Agent"""
        # Example tool functions
        def web_search(query: str) -> Dict[str, Any]:
            return {"results": [f"Search result for: {query}"]}
            
        def calculator(expression: str) -> Dict[str, Any]:
            try:
                return {"result": eval(expression)}
            except:
                return {"error": "Invalid expression"}
                
        # Register tools
        self.agent.register_tool("web_search", "Search the web for information", web_search)
        self.agent.register_tool("calculator", "Calculate mathematical expressions", calculator)
        
    def register_tool(self, name: str, description: str, function: Callable) -> bool:
        """Register a custom tool with the Qwen-Agent"""
        return self.agent.register_tool(name, description, function)
        
    def reason(self, query: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Use Qwen-Agent for reasoning"""
        # Convert string to dict if needed
        if isinstance(query, str):
            query = {"query": query}
            
        result = self.agent.reason(query)
        
        # Track recent calls
        self.recent_calls.append({
            "type": "reasoning",
            "query": query,
            "result": result,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_calls) > self.max_recent:
            self.recent_calls.pop(0)
            
        return result
        
    def chat(self, message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Chat with the Qwen-Agent"""
        result = self.agent.chat(message, history)
        
        # Track recent calls
        self.recent_calls.append({
            "type": "chat",
            "message": message,
            "history": history,
            "result": result,
            "timestamp": time.time()
        })
        
        # Limit history size
        if len(self.recent_calls) > self.max_recent:
            self.recent_calls.pop(0)
            
        return result
        
    def get_recent_interactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent interactions with the agent"""
        return sorted(self.recent_calls, key=lambda x: x["timestamp"], reverse=True)[:limit]
