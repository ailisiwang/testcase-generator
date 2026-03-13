"""测试大模型集成 - Provider初始化和功能验证"""
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.llm.providers.glm import GLMProvider
from app.llm.providers.gpt import GPTProvider
from app.llm.providers.claude import ClaudeProvider
from app.llm.providers.qwen import QwenProvider
from app.llm.providers.doubao import DoubaoProvider
from app.llm.base import get_llm_provider
from app.llm.agent import TestCaseAgent


class TestGLMProvider:
    """测试GLM Provider"""

    @patch('app.llm.providers.glm.init_chat_model')
    def test_glm_provider_initialization(self, mock_init):
        """测试GLM Provider初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = GLMProvider(
            api_key="test_key",
            model_name="glm-4",
            temperature=0.7,
            max_tokens=2048
        )

        # Verify init_chat_model was called with correct parameters
        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['model'] == "glm-4"
        assert call_kwargs['model_provider'] == "zhipuai"
        assert call_kwargs['zhipuai_api_key'] == "test_key"
        assert call_kwargs['temperature'] == 0.7
        assert call_kwargs['max_tokens'] == 2048
        assert provider.model_name == "glm-4"

    @patch('app.llm.providers.glm.init_chat_model')
    def test_glm_provider_with_custom_base_url(self, mock_init):
        """测试GLM Provider自定义base URL"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = GLMProvider(
            api_key="test_key",
            model_name="glm-4",
            api_base_url="https://custom.api.com"
        )

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['zhipuai_api_base'] == "https://custom.api.com"


class TestGPTProvider:
    """测试GPT Provider"""

    @patch('app.llm.providers.gpt.init_chat_model')
    def test_gpt_provider_initialization(self, mock_init):
        """测试GPT Provider初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = GPTProvider(
            api_key="test_key",
            model_name="gpt-4"
        )

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['model'] == "gpt-4"
        assert call_kwargs['model_provider'] == "openai"
        assert call_kwargs['api_key'] == "test_key"

    @patch('app.llm.providers.gpt.init_chat_model')
    def test_gpt_provider_with_custom_base_url(self, mock_init):
        """测试GPT Provider自定义base URL"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = GPTProvider(
            api_key="test_key",
            api_base_url="https://custom.openai.com"
        )

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['base_url'] == "https://custom.openai.com"


class TestClaudeProvider:
    """测试Claude Provider"""

    @patch('app.llm.providers.claude.init_chat_model')
    def test_claude_provider_initialization(self, mock_init):
        """测试Claude Provider初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = ClaudeProvider(
            api_key="test_key",
            model_name="claude-sonnet-4-6"
        )

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['model'] == "claude-sonnet-4-6"
        assert call_kwargs['model_provider'] == "anthropic"
        assert call_kwargs['anthropic_api_key'] == "test_key"


class TestQwenProvider:
    """测试Qwen Provider"""

    @patch('app.llm.providers.qwen.init_chat_model')
    def test_qwen_provider_initialization(self, mock_init):
        """测试Qwen Provider初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = QwenProvider(
            api_key="test_key",
            model_name="qwen-turbo"
        )

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['model'] == "qwen-turbo"
        assert call_kwargs['model_provider'] == "openai"  # Qwen uses OpenAI-compatible API
        assert call_kwargs['api_key'] == "test_key"
        assert "dashscope.aliyuncs.com" in call_kwargs['base_url']

    @patch('app.llm.providers.qwen.init_chat_model')
    def test_qwen_provider_with_custom_base_url(self, mock_init):
        """测试Qwen Provider自定义base URL"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = QwenProvider(
            api_key="test_key",
            api_base_url="https://custom.qwen.com"
        )

        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['base_url'] == "https://custom.qwen.com"


class TestDoubaoProvider:
    """测试Doubao Provider"""

    @patch('app.llm.providers.doubao.init_chat_model')
    def test_doubao_provider_initialization(self, mock_init):
        """测试Doubao Provider初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        provider = DoubaoProvider(
            api_key="test_key",
            model_name="doubao-pro-32k"
        )

        mock_init.assert_called_once()
        call_kwargs = mock_init.call_args.kwargs
        assert call_kwargs['model'] == "doubao-pro-32k"
        assert call_kwargs['model_provider'] == "openai"  # Doubao uses OpenAI-compatible API
        assert call_kwargs['api_key'] == "test_key"
        assert "volces.com" in call_kwargs['base_url']


class TestGetLLMProvider:
    """测试LLM Provider工厂函数"""

    def test_get_glm_provider(self):
        """测试获取GLM Provider"""
        with patch('app.llm.providers.glm.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model

            provider = get_llm_provider(
                provider="glm",
                api_key="test_key",
                model_name="glm-4"
            )

            assert isinstance(provider, GLMProvider)

    def test_get_gpt_provider(self):
        """测试获取GPT Provider"""
        with patch('app.llm.providers.gpt.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model

            provider = get_llm_provider(
                provider="gpt",
                api_key="test_key",
                model_name="gpt-4"
            )

            assert isinstance(provider, GPTProvider)

    def test_get_claude_provider(self):
        """测试获取Claude Provider"""
        with patch('app.llm.providers.claude.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model

            provider = get_llm_provider(
                provider="claude",
                api_key="test_key",
                model_name="claude-sonnet-4-6"
            )

            assert isinstance(provider, ClaudeProvider)

    def test_get_qwen_provider(self):
        """测试获取Qwen Provider"""
        with patch('app.llm.providers.qwen.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model

            provider = get_llm_provider(
                provider="qwen",
                api_key="test_key",
                model_name="qwen-turbo"
            )

            assert isinstance(provider, QwenProvider)

    def test_get_doubao_provider(self):
        """测试获取Doubao Provider"""
        with patch('app.llm.providers.doubao.init_chat_model') as mock_init:
            mock_model = Mock()
            mock_init.return_value = mock_model

            provider = get_llm_provider(
                provider="doubao",
                api_key="test_key",
                model_name="doubao-pro-32k"
            )

            assert isinstance(provider, DoubaoProvider)

    def test_invalid_provider(self):
        """测试无效Provider"""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_llm_provider(
                provider="invalid",
                api_key="test_key",
                model_name="model"
            )


class TestTestCaseAgent:
    """测试TestCaseAgent"""

    @patch('app.llm.agent.init_chat_model')
    def test_agent_initialization(self, mock_init):
        """测试Agent初始化"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        agent = TestCaseAgent(
            provider="glm",
            api_key="test_key",
            model_name="glm-4"
        )

        assert agent.provider == "glm"
        assert agent.model_name == "glm-4"
        assert agent.model_provider == "zhipuai"

    @patch('app.llm.agent.init_chat_model')
    @patch('app.llm.agent.create_agent')
    def test_agent_create_agent(self, mock_create_agent, mock_init):
        """测试Agent创建"""
        mock_model = Mock()
        mock_init.return_value = mock_model
        mock_agent_graph = Mock()
        mock_create_agent.return_value = mock_agent_graph

        agent = TestCaseAgent(
            provider="glm",
            api_key="test_key",
            model_name="glm-4"
        )

        agent.create_agent("You are a test engineer")

        # Verify agent was created
        assert agent.agent is not None
        mock_create_agent.assert_called_once()

    @patch('app.llm.agent.init_chat_model')
    def test_agent_provider_mapping(self, mock_init):
        """测试Agent Provider映射"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        providers_map = {
            "glm": "zhipuai",
            "gpt": "openai",
            "claude": "anthropic",
            "qwen": "openai",
            "doubao": "openai"
        }

        for provider, expected_model_provider in providers_map.items():
            agent = TestCaseAgent(
                provider=provider,
                api_key="test_key",
                model_name="model"
            )
            assert agent.model_provider == expected_model_provider


class TestAPIKeyEncryption:
    """测试 API Key 加密"""

    @patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key-for-encryption-32bytes!'})
    def test_encryption_decryption(self):
        """测试API Key加密解密"""
        import os
        os.environ['SECRET_KEY'] = 'test-secret-key-for-encryption-32bytes!'
        from app.utils.security import encrypt_api_key, decrypt_api_key

        api_key = "sk-test-key-12345"
        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)

        # Encrypted should be different from original
        assert encrypted != api_key
        # Decrypted should match original
        assert decrypted == api_key

    @patch.dict('os.environ', {'SECRET_KEY': 'test-secret-key-for-encryption-32bytes!'})
    def test_encryption_different_keys(self):
        """测试不同API Key产生不同密文"""
        import os
        os.environ['SECRET_KEY'] = 'test-secret-key-for-encryption-32bytes!'
        from app.utils.security import encrypt_api_key, decrypt_api_key

        key1 = "sk-test-key-11111"
        key2 = "sk-test-key-22222"

        encrypted1 = encrypt_api_key(key1)
        encrypted2 = encrypt_api_key(key2)

        # Different keys should produce different encrypted values
        assert encrypted1 != encrypted2

        # But decryption should work correctly for each
        assert decrypt_api_key(encrypted1) == key1
        assert decrypt_api_key(encrypted2) == key2
