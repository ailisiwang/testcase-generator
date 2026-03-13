"""LLM base module - LangChain 1.x integration"""
from typing import Optional, AsyncGenerator, Dict, Any
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    async def generate_async(self, prompt: str, **kwargs) -> str:
        """Async generate text from prompt"""
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream generate text from prompt"""
        pass


def get_llm_provider(provider: str, api_key: str, model_name: str, 
                      api_base_url: Optional[str] = None, **kwargs) -> BaseLLMProvider:
    """
    Get LLM provider instance
    
    Args:
        provider: Provider name (glm, doubao, qwen, gpt, claude)
        api_key: API key
        model_name: Model name
        api_base_url: Optional API base URL
        **kwargs: Additional parameters
    
    Returns:
        LLM provider instance
    """
    from app.llm.providers.glm import GLMProvider
    from app.llm.providers.doubao import DoubaoProvider
    from app.llm.providers.qwen import QwenProvider
    from app.llm.providers.gpt import GPTProvider
    from app.llm.providers.claude import ClaudeProvider
    
    providers = {
        "glm": GLMProvider,
        "doubao": DoubaoProvider,
        "qwen": QwenProvider,
        "gpt": GPTProvider,
        "claude": ClaudeProvider,
        "custom": GLMProvider,  # custom 也使用 GLM
    }
    
    provider_lower = provider.lower()
    provider_class = providers.get(provider_lower)
    if not provider_class:
        # 未知供应商，默认使用 GLM
        provider_class = GLMProvider
    
    return provider_class(api_key=api_key, model_name=model_name, 
                         api_base_url=api_base_url, **kwargs)
