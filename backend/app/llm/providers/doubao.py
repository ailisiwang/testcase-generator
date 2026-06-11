"""Doubao Provider - 字节豆包"""
from typing import Optional, AsyncGenerator
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from app.llm.base import BaseLLMProvider


class DoubaoProvider(BaseLLMProvider):
    """Doubao provider using LangChain 1.x"""

    def __init__(self, api_key: str, model_name: str = "doubao-pro-32k",
                 api_base_url: Optional[str] = None, **kwargs):
        self.model_name = model_name
        self.temperature = kwargs.get("temperature", 0.7)
        self.max_tokens = kwargs.get("max_tokens", 2048)

        # Use custom or default base URL for Doubao
        base_url = api_base_url or "https://ark.cn-beijing.volces.com/api/v3"

        self.model = init_chat_model(
            model=model_name,
            model_provider="openai",
            api_key=api_key,
            base_url=base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def generate(self, prompt: str, **kwargs) -> str:
        messages = [HumanMessage(content=prompt)]
        response = self.model.invoke(messages)
        return response.content

    async def generate_async(self, prompt: str, **kwargs) -> str:
        messages = [HumanMessage(content=prompt)]
        response = await self.model.ainvoke(messages)
        return response.content

    async def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream text generation asynchronously"""
        messages = [HumanMessage(content=prompt)]
        
        async for chunk in self.model.astream(messages):
            if hasattr(chunk, "content"):
                yield chunk.content
            else:
                yield str(chunk)

    async def generate_structured_async(self, prompt: str, schema: Type[T], **kwargs) -> T:
        """Generate structured output asynchronously"""
        messages = [HumanMessage(content=prompt)]
        structured_llm = self.model.with_structured_output(schema)
        return await structured_llm.ainvoke(messages)
