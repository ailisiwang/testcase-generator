"""LangChain Agent wrapper - Using LangChain 1.x create_agent syntax"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage


# Provider mapping for init_chat_model
PROVIDER_MAP = {
    "glm": ("zhipuai", "zhipuai_api_key"),
    "doubao": ("openai", "api_key"),
    "qwen": ("openai", "api_key"),
    "gpt": ("openai", "api_key"),
    "claude": ("anthropic", "anthropic_api_key"),
}


class TestCaseAgent:
    """Test case generation agent using LangChain 1.x"""

    def __init__(self, provider: str, api_key: str, model_name: str,
                 api_base_url: Optional[str] = None, temperature: float = 0.7):
        self.provider = provider.lower()
        self.api_key = api_key
        self.model_name = model_name
        self.api_base_url = api_base_url
        self.temperature = temperature

        # Get the LangChain model provider name and API key param
        self.model_provider, self.api_key_param = PROVIDER_MAP.get(
            self.provider, ("openai", "api_key")
        )

        # Initialize the LLM using init_chat_model
        model_kwargs = {
            "temperature": temperature,
            "max_tokens": 4096,
            self.api_key_param: api_key,
        }

        # Add API base URL for custom endpoints
        if api_base_url:
            if self.model_provider == "zhipuai":
                model_kwargs["zhipuai_api_base"] = api_base_url
            elif self.model_provider == "openai":
                model_kwargs["base_url"] = api_base_url
            elif self.model_provider == "anthropic":
                model_kwargs["anthropic_api_url"] = api_base_url

        self.llm = init_chat_model(
            model=model_name,
            model_provider=self.model_provider,
            **model_kwargs
        )

        self.tools = []
        self.agent = None
        self.system_prompt = None

    def _create_tools(self, system_fields: Optional[List[Dict[str, Any]]] = None) -> List:
        """Create tools for the agent"""

        @tool
        def generate_test_cases(requirement: str, count: int = 5) -> str:
            """Generate test cases based on requirement.

            Args:
                requirement: The requirement or feature description
                count: Number of test cases to generate

            Returns:
                Generated test cases in JSON format
            """
            return f"Generated {count} test cases for: {requirement}"

        @tool
        def validate_case_structure(case_data: str) -> str:
            """Validate a test case structure and completeness.

            Args:
                case_data: JSON string of test case data

            Returns:
                Validation result with any issues found
            """
            import json
            try:
                case = json.loads(case_data)
                required_fields = ["title", "precondition", "test_steps", "expected_result"]
                missing = [f for f in required_fields if f not in case]
                if missing:
                    return f"Validation failed: Missing fields: {', '.join(missing)}"
                return "Test case validation passed"
            except json.JSONDecodeError:
                return "Validation failed: Invalid JSON format"

        return [generate_test_cases, validate_case_structure]

    def create_agent(self, system_prompt: str, system_fields: Optional[List] = None):
        """Create the agent using LangChain 1.x create_agent syntax

        Args:
            system_prompt: System prompt for the agent
            system_fields: Optional field configurations for test cases
        """
        self.system_prompt = system_prompt
        self.tools = self._create_tools(system_fields)

        # Create agent using LangChain 1.x create_agent
        # This returns a CompiledStateGraph
        self.agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=system_prompt,
            debug=False
        )

    async def run(self, input_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the agent with streaming output

        Args:
            input_text: User input text

        Yields:
            Dict containing streaming chunks with type and content
        """
        if not self.agent:
            self.create_agent(
                "你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。"
            )

        # Stream the agent execution using astream
        async for chunk in self.agent.astream(
            {"messages": [HumanMessage(content=input_text)]}
        ):
            # Process different stream events
            if isinstance(chunk, dict):
                if "messages" in chunk:
                    for msg in chunk["messages"]:
                        if hasattr(msg, "content"):
                            yield {
                                "type": "message",
                                "content": msg.content
                            }
                elif "output" in chunk:
                    yield {
                        "type": "output",
                        "content": chunk["output"]
                    }
            elif hasattr(chunk, "content"):
                yield {
                    "type": "content",
                    "content": chunk.content
                }

    async def run_stream_events(self, input_text: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Run the agent with detailed streaming events

        Args:
            input_text: User input text

        Yields:
            Dict containing detailed event information
        """
        if not self.agent:
            self.create_agent(
                "你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。"
            )

        # Stream with detailed events
        async for event in self.agent.astream_events(
            {"messages": [HumanMessage(content=input_text)]},
            version="v1"
        ):
            # Filter for relevant events
            if event["event"] in ["on_chat_model_start", "on_chat_model_stream", "on_chat_model_end"]:
                yield {
                    "type": "llm_event",
                    "event": event["event"],
                    "data": event.get("data", {})
                }
            elif event["event"] in ["on_tool_start", "on_tool_end", "on_tool_error"]:
                yield {
                    "type": "tool_event",
                    "event": event["event"],
                    "tool": event.get("name", ""),
                    "data": event.get("data", {})
                }

    async def run_sync_return(self, input_text: str) -> str:
        """Run the agent and return final result

        Args:
            input_text: User input text

        Returns:
            Agent output content
        """
        if not self.agent:
            self.create_agent(
                "你是一个专业的测试工程师，擅长根据需求生成高质量的测试用例。"
            )

        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=input_text)]}
        )

        # Extract the final message content
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            if hasattr(last_message, "content"):
                return last_message.content
            return str(last_message)

        return str(result)


async def generate_cases_with_agent(
    provider: str,
    api_key: str,
    model_name: str,
    requirement: str,
    system_fields: Optional[List[Dict[str, Any]]] = None,
    count: int = 5,
    api_base_url: Optional[str] = None,
    temperature: float = 0.7
) -> AsyncGenerator[Dict[str, Any], None]:
    """Helper function to generate test cases using agent

    Args:
        provider: LLM provider name
        api_key: API key
        model_name: Model name
        requirement: Requirement description
        system_fields: Field configurations
        count: Number of cases to generate
        api_base_url: Optional API base URL
        temperature: Temperature setting

    Yields:
        Streaming output chunks
    """
    agent = TestCaseAgent(
        provider=provider,
        api_key=api_key,
        model_name=model_name,
        api_base_url=api_base_url,
        temperature=temperature
    )

    system_prompt = f"""你是一个专业的测试工程师，擅长根据需求生成测试用例。

请根据用户的需求描述，生成{count}条高质量的测试用例。
测试用例应包含：
- 用例标题
- 前置条件
- 测试步骤
- 预期结果

要求：
1. 覆盖正常场景和异常场景
2. 测试步骤清晰可执行
3. 预期结果明确具体
"""

    agent.create_agent(system_prompt, system_fields)

    async for chunk in agent.run(requirement):
        yield chunk
