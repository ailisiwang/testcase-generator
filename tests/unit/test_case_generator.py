"""测试用例生成服务"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.case_generator import CaseGeneratorService
from app.models.test_case import TestCase, CaseField
from app.models.model_config import ModelConfig


class TestBuildGenerationPrompt:
    """测试 Prompt 构建逻辑"""

    def test_build_prompt_with_default_fields(self):
        """测试使用默认字段构建 Prompt"""
        requirement = "用户登录功能测试"
        system_fields = []
        count = 5

        prompt = CaseGeneratorService._build_generation_prompt(
            requirement, system_fields, count
        )

        # 当字段为空时，prompt 中不应该有字段信息
        # 因为默认字段是在 generate_cases 中添加的
        assert "用户登录功能测试" in prompt
        assert "5条测试用例" in prompt
        assert "JSON数组格式" in prompt
        # 字段列表为空，所以不应该包含这些字段名
        assert "用例标题" not in prompt
        assert "前置条件" not in prompt

    def test_build_prompt_with_custom_fields(self):
        """测试使用自定义字段构建 Prompt"""
        requirement = "支付功能测试"
        system_fields = [
            {"field_name": "title", "field_label": "用例名称", "field_type": "text", "is_required": True},
            {"field_name": "priority", "field_label": "优先级", "field_type": "select", "is_required": False},
        ]
        count = 10

        prompt = CaseGeneratorService._build_generation_prompt(
            requirement, system_fields, count
        )

        assert "支付功能测试" in prompt
        assert "10条测试用例" in prompt
        assert "用例名称" in prompt
        assert "优先级" in prompt
        assert "(必填)" in prompt

    def test_build_prompt_with_required_field_marker(self):
        """测试必填字段标记"""
        system_fields = [
            {"field_name": "title", "field_label": "标题", "field_type": "text", "is_required": True},
            {"field_name": "desc", "field_label": "描述", "field_type": "textarea", "is_required": False},
        ]

        prompt = CaseGeneratorService._build_generation_prompt(
            "测试", system_fields, 3
        )

        assert "标题 (必填)" in prompt
        assert "描述" in prompt
        assert "(必填)" not in prompt.split("描述")[0]

    def test_build_prompt_contains_format_requirements(self):
        """测试 Prompt 包含格式要求"""
        prompt = CaseGeneratorService._build_generation_prompt(
            "测试需求", [], 5
        )

        assert "覆盖正常场景和异常场景" in prompt
        assert "测试步骤清晰可执行" in prompt
        assert "预期结果明确" in prompt


class TestParseCases:
    """测试 JSON 解析逻辑"""

    def test_parse_valid_json_array(self):
        """测试解析有效的 JSON 数组"""
        response = """[{"title": "登录测试", "steps": ["输入密码"]}, {"title": "注册测试"}]"""
        result = CaseGeneratorService._parse_cases(response)

        assert len(result) == 2
        assert result[0]["title"] == "登录测试"
        assert result[1]["title"] == "注册测试"

    def test_parse_json_with_extra_text(self):
        """测试解析包含额外文本的响应"""
        response = """这是一些生成的文本：
[{"title": "测试用例1", "steps": ["步骤1"]}]
还有一些额外的文本"""
        result = CaseGeneratorService._parse_cases(response)

        assert len(result) == 1
        assert result[0]["title"] == "测试用例1"

    def test_parse_json_no_array_found(self):
        """测试没有找到 JSON 数组"""
        response = "只是一些普通文本，没有 JSON"
        result = CaseGeneratorService._parse_cases(response)

        assert result == []

    def test_parse_invalid_json(self):
        """测试无效的 JSON"""
        response = "[{invalid json}]"
        result = CaseGeneratorService._parse_cases(response)

        assert result == []

    def test_parse_empty_response(self):
        """测试空响应"""
        result = CaseGeneratorService._parse_cases("")

        assert result == []

    def test_parse_nested_json(self):
        """测试嵌套的 JSON 结构"""
        response = """[{"title": "测试", "data": {"nested": "value", "count": 5}}]"""
        result = CaseGeneratorService._parse_cases(response)

        assert len(result) == 1
        assert result[0]["data"]["nested"] == "value"


class TestGenerateCases:
    """测试用例生成功能"""

    @pytest.mark.asyncio
    async def test_generate_cases_success(self, mock_db_session):
        """测试成功生成用例"""
        # Mock system
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system

        # Mock model config
        mock_config = Mock()
        mock_config.provider = "glm"
        mock_config.model_name = "glm-4"
        mock_config.api_key_encrypted = "encrypted_key"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7

        # Mock LLM response
        mock_llm = AsyncMock()
        mock_llm.generate_async.return_value = '[{"title": "登录测试", "steps": ["步骤1"]}]'

        with patch('app.services.case_generator.decrypt_api_key', return_value='decrypted_key'):
            with patch('app.services.case_generator.get_llm_provider', return_value=mock_llm):
                result = await CaseGeneratorService.generate_cases(
                    mock_db_session,
                    system_id=1,
                    requirement="登录功能测试",
                    user_id=1
                )

        assert len(result) == 1
        assert result[0]["title"] == "登录测试"

    @pytest.mark.asyncio
    async def test_generate_cases_system_not_found(self, mock_db_session):
        """测试系统不存在"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await CaseGeneratorService.generate_cases(
                mock_db_session,
                system_id=999,
                requirement="测试",
                user_id=1
            )

        assert "System not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_cases_no_model_config(self, mock_db_session):
        """测试没有模型配置"""
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        # 第二次查询返回 None（无模型配置）
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_system, None]

        with pytest.raises(ValueError) as exc_info:
            await CaseGeneratorService.generate_cases(
                mock_db_session,
                system_id=1,
                requirement="测试",
                user_id=1
            )

        assert "No active model configuration found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_cases_llm_error(self, mock_db_session):
        """测试 LLM 调用失败"""
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_config = Mock()
        mock_config.provider = "glm"
        mock_config.api_key_encrypted = "encrypted"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_system, mock_config]

        mock_llm = AsyncMock()
        mock_llm.generate_async.side_effect = Exception("API Error")

        with patch('app.services.case_generator.decrypt_api_key', return_value='key'):
            with patch('app.services.case_generator.get_llm_provider', return_value=mock_llm):
                with pytest.raises(ValueError) as exc_info:
                    await CaseGeneratorService.generate_cases(
                        mock_db_session,
                        system_id=1,
                        requirement="测试",
                        user_id=1
                    )

        assert "Failed to generate cases" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_cases_with_custom_count(self, mock_db_session):
        """测试指定生成数量"""
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_config = Mock()
        mock_config.provider = "glm"
        mock_config.api_key_encrypted = "encrypted"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7

        mock_llm = AsyncMock()
        mock_llm.generate_async.return_value = '[{"title": "测试1"}, {"title": "测试2"}, {"title": "测试3"}]'

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_system, mock_config]

        with patch('app.services.case_generator.decrypt_api_key', return_value='key'):
            with patch('app.services.case_generator.get_llm_provider', return_value=mock_llm):
                result = await CaseGeneratorService.generate_cases(
                    mock_db_session,
                    system_id=1,
                    requirement="测试",
                    count=3,
                    user_id=1
                )

        assert len(result) == 3


class TestGenerateFromFile:
    """测试从文件生成用例"""

    @pytest.mark.asyncio
    async def test_generate_from_file_success(self, mock_db_session):
        """测试从文件成功生成用例"""
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_config = Mock()
        mock_config.provider = "glm"
        mock_config.api_key_encrypted = "encrypted"
        mock_config.api_base_url = None
        mock_config.temperature = 0.7

        mock_llm = AsyncMock()
        mock_llm.generate_async.return_value = '[{"title": "文件测试用例"}]'

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_system, mock_config]

        with patch('app.services.case_generator.decrypt_api_key', return_value='key'):
            with patch('app.services.case_generator.get_llm_provider', return_value=mock_llm):
                result = await CaseGeneratorService.generate_from_file(
                    mock_db_session,
                    system_id=1,
                    file_content="文件内容：需求描述",
                    user_id=1
                )

        assert len(result) == 1
        assert result[0]["title"] == "文件测试用例"

    @pytest.mark.asyncio
    async def test_generate_from_file_system_not_found(self, mock_db_session):
        """测试文件生成时系统不存在"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError) as exc_info:
            await CaseGeneratorService.generate_from_file(
                mock_db_session,
                system_id=999,
                file_content="内容",
                user_id=1
            )

        assert "System not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_from_file_no_config(self, mock_db_session):
        """测试文件生成时没有模型配置"""
        mock_system = Mock()
        mock_system.id = 1
        mock_system.fields = []

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        mock_db_session.query.return_value.filter.return_value.first.side_effect = [mock_system, None]

        with pytest.raises(ValueError) as exc_info:
            await CaseGeneratorService.generate_from_file(
                mock_db_session,
                system_id=1,
                file_content="内容",
                user_id=1
            )

        assert "No active model configuration found" in str(exc_info.value)


class TestEdgeCases:
    """边界条件测试"""

    def test_parse_cases_with_unicode(self):
        """测试包含 Unicode 的解析"""
        response = '[{"title": "测试用例中文", "steps": ["步骤一", "步骤二"]}]'
        result = CaseGeneratorService._parse_cases(response)

        assert result[0]["title"] == "测试用例中文"
        assert result[0]["steps"][0] == "步骤一"

    def test_parse_cases_empty_array(self):
        """测试空数组解析"""
        response = '[]'
        result = CaseGeneratorService._parse_cases(response)

        assert result == []

    def test_parse_cases_large_array(self):
        """测试大数组解析"""
        cases = [{"title": f"测试用例{i}", "steps": ["步骤"]} for i in range(100)]
        response = json.dumps(cases)
        result = CaseGeneratorService._parse_cases(response)

        assert len(result) == 100

    def test_build_prompt_empty_requirement(self):
        """测试空需求构建 Prompt"""
        prompt = CaseGeneratorService._build_generation_prompt("", [], 5)

        assert "测试用例" in prompt
        assert "5条" in prompt
