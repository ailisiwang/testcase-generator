"""LangChain Agent wrapper - Using LangChain 1.x create_agent syntax"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from langchain.agents import create_agent, AgentExecutor
from langchain.tools import tool
from langchain.memory import ConversationBufferMemory

from app.llm.base import get_llm_provider


class TestCaseAgent:
    """Test case generation agent using LangChain 1.x"""
    
    def __init__(self, provider: str, api_key: str, model_name: str,
                 api_base_url: Optional[str] = None, temperature: float = 0.7):
        self.llm = get_llm_provider(
            provider=provider,
            api_key=api_key,
            model_name=model_name,
            api_base_url=api_base_url,
            temperature=temperature
        )
        self.memory = ConversationBufferMemory()
        self.agent = None
        self.agent_executor = None
    
    def _create_tools(self, system_fields: List[Dict[str, Any]]) -> List:
        """Create tools for the agent"""
        
        @tool
        def generate_test_cases(requirement: str, count: int = 5) -> str:
            """Generate test cases based on requirement.
            
            Args:
                requirement: The requirement or feature description
                count: Number of test cases to generate
            """
            # This is a placeholder - actual implementation would generate cases
            return f"Generated {count} test cases for: {requirement}"
        
        @tool
        def validate_case(case_data: str) -> str:
            """Validate a test case structure and completeness."""
            return "Test case validation complete"
        
        return [generate_test_cases, validate_case]
    
    def create_agent(self, system_prompt: str, system_fields: Optional[List] = None):
        """Create the agent using LangChain 1.x syntax"""
        tools = self._create_tools(system_fields or [])
        
        self.agent = create_agent(
            model=model_name if (model_name := getattr(self.llm, 'model_name', None)) else "glm-4",
            model_provider=f"langchain.Chat{self._get_provider_prefix()}",
            tools=tools,
            system_prompt=system_prompt
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            memory=self.memory,
            verbose=True
        )
    
    def _get_provider_prefix(self) -> str:
        """Get provider prefix for model provider"""
        provider_map = {
            "glm": "ZhipuAI",
            "doubao": "OpenAI",  # Doubao uses OpenAI compatible API
            "qwen": "Alibaba",
            "gpt": "OpenAI",
            "claude": "Anthropic",
        }
        # This is simplified - actual implementation needs the provider name
        return "ZhipuAI"
    
    async def run(self, input_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the agent with streaming"""
        if not self.agent_executor:
            self.create_agent("你是一个专业的测试工程师，擅长根据需求生成测试用例")
        
        async for event in self.agent_executor.astream_events(
            {"messages": [("user", input_text)]},
            version="v1"
        ):
            if event["event"] == "on_chat_model_stream":
                yield {"content": event["data"]["chunk"].content}
    
    def run_sync(self, input_text: str) -> str:
        """Run the agent synchronously"""
        if not self.agent_executor:
            self.create_agent("你是一个专业的测试工程师，擅长根据需求生成测试用例")
        
        result = self.agent_executor.invoke({"messages": [("user", input_text)]})
        return result.get("output", "")
