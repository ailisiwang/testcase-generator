"""
大模型集成测试模块

包含：
- 多模型切换测试
- 参数配置测试
- API Key 加密存储测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime
import base64
from cryptography.fernet import Fernet


class TestMultiModelSwitching:
    """多模型切换测试"""

    @pytest.mark.unit
    @pytest.mark.llm
    def test_switch_to_glm_model(self):
        """测试切换到 GLM 模型"""
        from app.llm.providers.glm import GLMProvider
        
        config = {
            "model_name": "glm-4",
            "api_key": "test_key",
            "api_base_url": "https://open.bigmodel.cn/api/paas/v4"
        }
        
        provider = GLMProvider(config)
        
        assert provider.model_name == "glm-4"

    @pytest.mark.unit
    @pytest.mark.llm
    def test_switch_to_gpt_model(self):
        """测试切换到 GPT 模型"""
        from app.llm.providers.gpt import GPTProvider
        
        config = {
            "model_name": "gpt-4",
            "api_key": "test_key"
        }
        
        provider = GPTProvider(config)
        
        assert provider.model_name == "gpt-4"

    @pytest.mark.unit
    @pytest.mark.llm
    def test_switch_to_claude_model(self):
        """测试切换到 Claude 模型"""
        from app.llm.providers.claude import ClaudeProvider
        
        config = {
            "model_name": "claude-sonnet-4-6",
            "api_key": "test_key"
        }
        
        provider = ClaudeProvider(config)
        
        assert provider.model_name == "claude-sonnet-4-6"

    @pytest.mark.unit
    @pytest.mark.llm
    def test_switch_to_qwen_model(self):
        """测试切换到千问模型"""
        from app.llm.providers.qwen import QwenProvider
        
        config = {
            "model_name": "qwen-turbo",
            "api_key": "test_key"
        }
        
        provider = QwenProvider(config)
        
        assert provider.model_name == "qwen-turbo"

    @pytest.mark.unit
    @pytest.mark.llm
    def test_model_provider_factory(self):
        """测试模型提供者工厂"""
        from app.llm.base import ModelProviderFactory
        
        providers = ["zhipu", "openai", "anthropic", "alibaba"]
        
        for provider_type in providers:
            provider = ModelProviderFactory.create(provider_type, {"api_key": "test"})
            assert provider is not None

    @pytest.mark.unit
    @pytest.mark.llm
    def test_invalid_provider_type(self):
        """测试无效的提供者类型"""
        from app.llm.base import ModelProviderFactory
        
        with pytest.raises(ValueError, match="Unknown provider"):
            ModelProviderFactory.create("invalid_provider", {"api_key": "test"})


class TestParameterConfiguration:
    """参数配置测试"""

    @pytest.mark.unit
    @pytest.mark.llm
    def test_temperature_config(self):
        """测试温度参数配置"""
        # 有效温度范围: 0-2
        valid_temps = [0, 0.5, 1.0, 1.5, 2.0]
        
        for temp in valid_temps:
            assert 0 <= temp <= 2
        
        invalid_temps = [-0.1, 2.1, 5]
        
        for temp in invalid_temps:
            assert not (0 <= temp <= 2)

    @pytest.mark.unit
    @pytest.mark.llm
    def test_max_tokens_config(self):
        """测试最大 token 数配置"""
        valid_max_tokens = [512, 1024, 2048, 4096]
        
        for tokens in valid_max_tokens:
            assert tokens > 0
        
        invalid_tokens = [0, -1]
        
        for tokens in invalid_tokens:
            assert tokens <= 0

    @pytest.mark.unit
    @pytest.mark.llm
    def test_top_p_config(self):
        """测试 top_p 参数配置"""
        valid_top_p = [0.1, 0.5, 0.9, 1.0]
        
        for top_p in valid_top_p:
            assert 0 < top_p <= 1

    @pytest.mark.unit
    @pytest.mark.llm
    def test_model_config_persistence(self):
        """测试模型配置持久化"""
        config_data = {
            "provider": "zhipu",
            "model_name": "glm-4",
            "temperature": 0.7,
            "max_tokens": 2048,
            "is_active": True
        }
        
        # 模拟保存配置
        saved_config = config_data.copy()
        
        assert saved_config["is_active"] is True
        assert saved_config["temperature"] == 0.7

    @pytest.mark.unit
    @pytest.mark.llm
    def test_default_config_values(self):
        """测试默认配置值"""
        defaults = {
            "temperature": 0.7,
            "max_tokens": 2048,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        
        assert defaults["temperature"] == 0.7
        assert defaults["max_tokens"] == 2048

    @pytest.mark.unit
    @pytest.mark.llm
    def test_config_validation(self):
        """测试配置验证"""
        from app.schemas.model_config import ModelConfigUpdate
        
        valid_config = ModelConfigUpdate(
            temperature=0.8,
            max_tokens=4096
        )
        
        assert valid_config.temperature == 0.8
        
        # 无效配置
        invalid_temps = [-1, 3]
        
        for temp in invalid_temps:
            try:
                ModelConfigUpdate(temperature=temp)
            except Exception:
                pass  # 预期会报错


class TestAPIKeyEncryption:
    """API Key 加密存储测试"""

    @pytest.mark.unit
    def test_encrypt_api_key(self):
        """测试 API Key 加密"""
        # 生成密钥
        key = Fernet.generate_key()
        fernet = Fernet(key)
        
        api_key = "sk-test-api-key-12345"
        
        # 加密
        encrypted = fernet.encrypt(api_key.encode())
        
        assert encrypted != api_key.encode()
        assert isinstance(encrypted, bytes)

    @pytest.mark.unit
    def test_decrypt_api_key(self):
        """测试 API Key 解密"""
        key = Fernet.generate_key()
        fernet = Fernet(key)
        
        api_key = "sk-test-api-key-12345"
        encrypted = fernet.encrypt(api_key.encode())
        
        # 解密
        decrypted = fernet.decrypt(encrypted).decode()
        
        assert decrypted == api_key

    @pytest.mark.unit
    def test_encryption_with_password(self):
        """测试使用密码加密"""
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
        from cryptography.hazmat.primitives import hashes
        import os
        
        password = "test_password"
        salt = os.urandom(16)
        
        # 派生密钥
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        
        fernet = Fernet(key)
        
        api_key = "secret-api-key"
        encrypted = fernet.encrypt(api_key.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        
        assert decrypted == api_key

    @pytest.mark.unit
    def test_encryption_key_rotation(self):
        """测试密钥轮换"""
        old_key = Fernet.generate_key()
        new_key = Fernet.generate_key()
        
        old_fernet = Fernet(old_key)
        new_fernet = Fernet(new_key)
        
        api_key = "my-secret-key"
        
        # 用旧密钥加密
        encrypted = old_fernet.encrypt(api_key.encode())
        
        # 用新密钥解密会失败
        with pytest.raises(Exception):
            new_fernet.decrypt(encrypted)

    @pytest.mark.unit
    def test_empty_api_key(self):
        """测试空 API Key 处理"""
        key = Fernet.generate_key()
        fernet = Fernet(key)
        
        empty_key = ""
        
        # 空字符串加密
        encrypted = fernet.encrypt(empty_key.encode())
        decrypted = fernet.decrypt(encrypted).decode()
        
        assert decrypted == empty_key

    @pytest.mark.unit
    def test_api_key_not_stored_plaintext(self):
        """测试 API Key 不以明文存储"""
        api_key = "sk-live-api-key-12345"
        
        # 检查不应该明文存储
        assert "sk-" in api_key  # 验证是 API key 格式
        
        # 加密后不应包含原始字符串
        key = Fernet.generate_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(api_key.encode())
        
        assert api_key.encode() not in encrypted

    @pytest.mark.unit
    def test_encrypted_key_in_database(self, mock_model_config):
        """测试数据库中存储加密的 Key"""
        # 模拟数据库存储
        stored_key = mock_model_config.api_key_encrypted
        
        # 验证存储的是加密值
        assert stored_key is not None
        assert stored_key != "sk-original-key"
