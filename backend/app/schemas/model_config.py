"""Model config schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ModelConfigBase(BaseModel):
    provider: str  # glm, doubao, qwen, gpt, claude
    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    user_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Provider info
class ProviderInfo(BaseModel):
    id: str
    name: str
    models: list[str]


AVAILABLE_PROVIDERS = [
    ProviderInfo(id="glm", name="智谱GLM", models=["glm-4", "glm-4-flash", "glm-3-turbo"]),
    ProviderInfo(id="doubao", name="字节豆包", models=["doubao-pro-32k", "doubao-lite-32k"]),
    ProviderInfo(id="qwen", name="阿里千问", models=["qwen-turbo", "qwen-plus", "qwen-max"]),
    ProviderInfo(id="gpt", name="OpenAI GPT", models=["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]),
    ProviderInfo(id="claude", name="Anthropic Claude", models=["claude-sonnet-4-6", "claude-opus-4-5"]),
]
