"""GLM Provider - 智谱GLM (OpenAI 兼容模式)"""
from typing import Optional, AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.llm.base import BaseLLMProvider


class GLMProvider(BaseLLMProvider):
    """GLM provider using LangChain 1.x with OpenAI compatibility"""

    def __init__(self, api_key: str, model: str = "glm-4",
                 api_base_url: Optional[str] = None, **kwargs):
        self.model_name = model
        self.temperature = kwargs.pop("temperature", 0.7)
        self.max_tokens = kwargs.pop("max_tokens", 2048)
        
        # Default to ZhipuAI API endpoint
        if not api_base_url:
            api_base_url = "https://open.bigmodel.cn/api/coding/paas/v4"

        # Initialize using LangChain with OpenAI-compatible API
        self.model = ChatOpenAI(
            model=model,
            openai_api_key=api_key,
            openai_api_base=api_base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            **kwargs
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
