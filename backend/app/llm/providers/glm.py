"""GLM Provider - 智谱GLM"""
from typing import Optional, AsyncGenerator
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from app.llm.base import BaseLLMProvider


class GLMProvider(BaseLLMProvider):
    """GLM provider using LangChain 1.x"""

    def __init__(self, api_key: str, model_name: str = "glm-4",
                 api_base_url: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 2048)

        # Build model kwargs
        model_kwargs = {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # Handle custom API base URL for ZhipuAI
        if api_base_url:
            model_kwargs["zhipuai_api_base"] = api_base_url

        # Initialize using LangChain 1.x init_chat_model
        self.model = init_chat_model(
            model=model_name,
            model_provider="zhipuai",
            zhipuai_api_key=api_key,
            **model_kwargs
        )

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text synchronously"""
        messages = [HumanMessage(content=prompt)]
        response = self.model.invoke(messages)
        return response.content

    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Generate text asynchronously"""
        messages = [HumanMessage(content=prompt)]
        response = await self.model.ainvoke(messages)
        return response.content

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text"""
        messages = [HumanMessage(content=prompt)]
        async for chunk in self.model.astream(messages):
            if chunk.content:
                yield chunk.content
