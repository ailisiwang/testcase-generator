"""测试流式生成功能"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from app.llm.streaming import StreamManager, stream_generate_cases
from app.llm.agent import TestCaseAgent, generate_cases_with_agent


class TestStreamManager:
    """测试StreamManager"""

    def test_create_task(self):
        """测试创建流式任务"""
        manager = StreamManager()
        task_id = manager.create_task()

        assert task_id is not None
        assert task_id in manager._streams

    def test_create_task_with_custom_id(self):
        """测试使用自定义ID创建任务"""
        manager = StreamManager()
        custom_id = "test-task-123"
        task_id = manager.create_task(task_id=custom_id)

        assert task_id == custom_id
        assert custom_id in manager._streams

    @pytest.mark.asyncio
    async def test_put_and_get(self):
        """测试放入和获取数据"""
        manager = StreamManager()
        task_id = manager.create_task()
        test_data = {"type": "test", "content": "hello"}

        await manager.put(task_id, test_data)
        result = await manager.get(task_id)

        assert result == test_data

    @pytest.mark.asyncio
    async def test_close_task(self):
        """测试关闭任务"""
        manager = StreamManager()
        task_id = manager.create_task()

        assert task_id in manager._streams
        manager.close(task_id)
        assert task_id not in manager._streams


class TestLLMProviderStreaming:
    """测试LLM Provider流式输出"""

    @pytest.mark.asyncio
    @patch('app.llm.providers.glm.init_chat_model')
    async def test_glm_provider_stream(self, mock_init):
        """测试GLM Provider流式输出"""
        # Setup mock model
        mock_model = Mock()
        mock_init.return_value = mock_model

        # Create mock chunks
        async def mock_stream(messages):
            chunks = ["Hello", " World", "!"]
            for chunk in chunks:
                mock_chunk = Mock()
                mock_chunk.content = chunk
                yield mock_chunk

        mock_model.astream = mock_stream

        from app.llm.providers.glm import GLMProvider

        provider = GLMProvider(api_key="test", model_name="glm-4")

        # Collect streamed content
        content_parts = []
        async for chunk in provider.stream("test prompt"):
            content_parts.append(chunk)

        assert "".join(content_parts) == "Hello World!"

    @pytest.mark.asyncio
    @patch('app.llm.providers.gpt.init_chat_model')
    async def test_gpt_provider_stream(self, mock_init):
        """测试GPT Provider流式输出"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        async def mock_stream(messages):
            mock_chunk = Mock()
            mock_chunk.content = "Test response"
            yield mock_chunk

        mock_model.astream = mock_stream

        from app.llm.providers.gpt import GPTProvider

        provider = GPTProvider(api_key="test", model_name="gpt-4")

        content = ""
        async for chunk in provider.stream("test"):
            content += chunk

        assert content == "Test response"


class TestCaseAgentStreaming:
    """测试Agent流式生成"""

    @pytest.mark.asyncio
    @patch('app.llm.agent.init_chat_model')
    @patch('app.llm.agent.create_agent')
    async def test_agent_run_streaming(self, mock_create_agent, mock_init):
        """测试Agent运行流式输出"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        # Mock agent graph
        mock_agent = Mock()

        async def mock_astream(input_dict):
            # Simulate streaming response
            yield {"messages": [Mock(content="First chunk")]}
            yield {"messages": [Mock(content="Second chunk")]}

        mock_agent.astream = mock_astream
        mock_create_agent.return_value = mock_agent

        agent = TestCaseAgent(
            provider="glm",
            api_key="test",
            model_name="glm-4"
        )
        agent.create_agent("You are a test engineer")

        # Collect streamed chunks
        chunks = []
        async for chunk in agent.run("Generate test cases"):
            chunks.append(chunk)

        assert len(chunks) > 0


class TestCaseGenerationStreaming:
    """测试用例生成流式功能"""

    @pytest.mark.asyncio
    @patch('app.llm.streaming.get_llm_provider')
    async def test_stream_generate_cases(self, mock_get_provider):
        """测试流式生成用例"""
        # Mock LLM provider
        mock_provider = Mock()

        async def mock_stream(prompt):
            yield '[{"title": "Test 1", "steps": "Step 1"}'
            yield ',{"title": "Test 2", "steps": "Step 2"}]'

        mock_provider.stream = mock_stream
        mock_get_provider.return_value = mock_provider

        # Collect streamed output
        results = []
        async for line in stream_generate_cases(
            provider="glm",
            api_key="test",
            model_name="glm-4",
            requirement="Test requirement",
            system_fields=[],
            count=2
        ):
            data = json.loads(line)
            results.append(data)

        # Should have start, chunks, and complete events
        event_types = [r.get("type") for r in results]
        assert "start" in event_types
        assert "chunk" in event_types
        assert "complete" in event_types

    @pytest.mark.asyncio
    @patch('app.llm.agent.init_chat_model')
    @patch('app.llm.agent.create_agent')
    async def test_generate_cases_with_agent(self, mock_create_agent, mock_init):
        """测试使用Agent生成用例"""
        mock_model = Mock()
        mock_init.return_value = mock_model

        mock_agent = Mock()

        async def mock_astream(input_dict):
            yield {"messages": [Mock(content="Generated test case 1")]}
            yield {"messages": [Mock(content="Generated test case 2")]}

        mock_agent.astream = mock_astream
        mock_create_agent.return_value = mock_agent

        # Collect results
        results = []
        async for chunk in generate_cases_with_agent(
            provider="glm",
            api_key="test",
            model_name="glm-4",
            requirement="Test requirement",
            count=2
        ):
            results.append(chunk)

        assert len(results) > 0


class TestStreamErrorHandling:
    """测试流式错误处理"""

    @pytest.mark.asyncio
    async def test_stream_timeout(self):
        """测试流式超时"""
        manager = StreamManager()
        task_id = manager.create_task()

        # Try to get data with timeout (no data put)
        result = await manager.get(task_id)

        # Should return None on timeout
        assert result is None

    @pytest.mark.asyncio
    @patch('app.llm.streaming.get_llm_provider')
    async def test_stream_with_llm_error(self, mock_get_provider):
        """测试LLM错误时的流式处理"""
        mock_provider = Mock()

        async def mock_stream(prompt):
            yield "Some data"
            raise Exception("LLM API Error")

        mock_provider.stream = mock_stream
        mock_get_provider.return_value = mock_provider

        # Should handle errors gracefully
        results = []
        try:
            async for line in stream_generate_cases(
                provider="glm",
                api_key="test",
                model_name="glm-4",
                requirement="Test",
                system_fields=[],
                count=1
            ):
                results.append(json.loads(line))
        except Exception:
            pass  # Expected to have errors

        # Should have collected some data before error
        assert len(results) > 0


@pytest.mark.integration
class TestEndToEndStreaming:
    """端到端流式生成测试（需要真实API Key时运行）"""

    @pytest.mark.skip(reason="Requires real API key")
    @pytest.mark.asyncio
    async def test_real_llm_streaming(self):
        """测试真实LLM流式输出"""
        # This test requires a real API key
        # Run with: pytest -m integration --api-key YOUR_KEY
        pass
