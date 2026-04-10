"""Case generation service"""
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Type
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, create_model

from app.models.test_case import TestCase, CaseVersion
from app.models.model_config import ModelConfig
from app.models.system import TestSystem
from app.utils.security import decrypt_api_key
from app.llm.base import get_llm_provider


class CaseGeneratorService:
    """Test case generation service"""
    
    @staticmethod
    def _create_schema(system_fields: List[Dict]) -> Type[BaseModel]:
        """Create Pydantic schema dynamically based on system fields"""
        model_fields = {}
        for f in system_fields:
            field_name = f["field_name"]
            description = f.get("field_label", field_name)
            # Type mapping
            if f.get("field_type") in ["select", "radio"]:
                field_type = str
            elif f.get("field_type") in ["checkbox"]:
                field_type = List[str]
            else:
                field_type = str
                
            if f.get("is_required"):
                model_fields[field_name] = (field_type, Field(..., description=description))
            else:
                model_fields[field_name] = (Optional[field_type], Field(None, description=description))
                
        TestCaseModel = create_model('TestCaseModel', **model_fields)
        
        class TestCaseList(BaseModel):
            cases: List[TestCaseModel] = Field(..., description="生成的测试用例列表")
            
        return TestCaseList

    @staticmethod
    def _build_generation_prompt(requirement: str, system_fields: List[Dict], count: int) -> str:
        """Build prompt for case generation"""
        field_info = []
        for f in system_fields:
            required_mark = " (必填)" if f.get("is_required") else ""
            field_info.append(f"- {f['field_name']}: {f['field_label']}{required_mark}")

        prompt = f"""请根据以下需求生成{count}条测试用例。

需求描述：
{requirement}

测试用例字段：
{chr(10).join(field_info)}

要求：
1. 覆盖正常场景和异常场景
2. 测试步骤清晰可执行
3. 预期结果明确"""
        return prompt
    
    @staticmethod
    async def generate_cases(
        db: Session,
        system_id: int,
        requirement: str,
        model_config_id: Optional[int] = None,
        count: int = 5,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate test cases using LLM"""
        
        # Get system fields
        system = db.query(TestSystem).filter(TestSystem.id == system_id).first()
        if not system:
            raise ValueError("System not found")
        
        fields = system.fields or []
        system_fields = [
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "field_type": f.field_type,
                "is_required": f.is_required
            }
            for f in fields
        ]
        
        # Default fields if none configured
        if not system_fields:
            system_fields = [
                {"field_name": "title", "field_label": "用例标题", "field_type": "text", "is_required": True},
                {"field_name": "precondition", "field_label": "前置条件", "field_type": "textarea", "is_required": True},
                {"field_name": "test_steps", "field_label": "测试步骤", "field_type": "textarea", "is_required": True},
                {"field_name": "expected_result", "field_label": "预期结果", "field_type": "textarea", "is_required": True},
            ]
        
        # Get model config
        if model_config_id:
            if user_id is None:
                raise ValueError("User not specified")
            config = db.query(ModelConfig).filter(
                ModelConfig.id == model_config_id,
                ModelConfig.user_id == user_id,
                ModelConfig.is_active == True
            ).first()
        else:
            # Get default active config for user
            config = db.query(ModelConfig).filter(
                ModelConfig.user_id == user_id,
                ModelConfig.is_active == True
            ).first()
        
        if not config:
            raise ValueError("No active model configuration found")
        
        # Decrypt API key
        try:
            api_key = decrypt_api_key(config.api_key_encrypted)
        except ValueError:
            raise ValueError("Failed to decrypt API key")
        
        # Get LLM provider
        llm = get_llm_provider(
            provider=config.provider,
            api_key=api_key,
            model_name=config.model_name,
            api_base_url=config.api_base_url,
            temperature=config.temperature
        )
        
        # Build prompt and schema
        prompt = CaseGeneratorService._build_generation_prompt(requirement, system_fields, count)
        schema = CaseGeneratorService._create_schema(system_fields)

        # Generate cases using structured output
        try:
            result = await llm.generate_structured_async(prompt, schema)
            # Handle Pydantic V1/V2 dict compatibility
            return [case.model_dump() if hasattr(case, 'model_dump') else case.dict() for case in result.cases]
        except Exception as e:
            raise ValueError(f"Failed to generate cases: {str(e)}")

    @staticmethod
    async def generate_from_file(
        db: Session,
        system_id: int,
        file_content: str,
        model_config_id: Optional[int] = None,
        count: int = 5,
        user_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Generate test cases from file content"""
        
        # Get system fields
        system = db.query(TestSystem).filter(TestSystem.id == system_id).first()
        if not system:
            raise ValueError("System not found")
        
        fields = system.fields or []
        system_fields = [
            {
                "field_name": f.field_name,
                "field_label": f.field_label,
                "field_type": f.field_type,
                "is_required": f.is_required
            }
            for f in fields
        ]
        
        if not system_fields:
            system_fields = [
                {"field_name": "title", "field_label": "用例标题", "field_type": "text", "is_required": True},
                {"field_name": "precondition", "field_label": "前置条件", "field_type": "textarea", "is_required": True},
                {"field_name": "test_steps", "field_label": "测试步骤", "field_type": "textarea", "is_required": True},
                {"field_name": "expected_result", "field_label": "预期结果", "field_type": "textarea", "is_required": True},
            ]
        
        # Get model config
        if model_config_id:
            if user_id is None:
                raise ValueError("User not specified")
            config = db.query(ModelConfig).filter(
                ModelConfig.id == model_config_id,
                ModelConfig.user_id == user_id,
                ModelConfig.is_active == True
            ).first()
        else:
            config = db.query(ModelConfig).filter(
                ModelConfig.user_id == user_id,
                ModelConfig.is_active == True
            ).first()
        
        if not config:
            raise ValueError("No active model configuration found")
        
        try:
            api_key = decrypt_api_key(config.api_key_encrypted)
        except ValueError:
            raise ValueError("Failed to decrypt API key")
        
        llm = get_llm_provider(
            provider=config.provider,
            api_key=api_key,
            model_name=config.model_name,
            api_base_url=config.api_base_url,
            temperature=config.temperature
        )
        
        prompt = f"""请根据以下需求文档生成{count}条测试用例。

需求文档：
{file_content}"""

        schema = CaseGeneratorService._create_schema(system_fields)

        try:
            result = await llm.generate_structured_async(prompt, schema)
            return [case.model_dump() if hasattr(case, 'model_dump') else case.dict() for case in result.cases]
        except Exception as e:
            raise ValueError(f"Failed to generate cases from file: {str(e)}")

    @staticmethod
    async def generate_script(
        db: Session,
        case_id: int,
        framework: str,
        user_id: int
    ) -> str:
        """Generate automation script for a specific test case"""
        # Get test case
        case = db.query(TestCase).join(TestSystem).filter(
            TestCase.id == case_id,
            TestSystem.user_id == user_id
        ).first()
        
        if not case:
            raise ValueError("Test case not found")
            
        # Get default active config for user
        config = db.query(ModelConfig).filter(
            ModelConfig.user_id == user_id,
            ModelConfig.is_active == True
        ).first()

        if not config:
            raise ValueError("No active model configuration found")

        try:
            api_key = decrypt_api_key(config.api_key_encrypted)
        except ValueError:
            raise ValueError("Failed to decrypt API key")

        llm = get_llm_provider(
            provider=config.provider,
            api_key=api_key,
            model_name=config.model_name,
            api_base_url=config.api_base_url,
            temperature=config.temperature
        )

        prompt = f"""你是一个专业的自动化测试开发工程师。
请根据以下测试用例数据，生成使用 {framework} 框架的自动化测试脚本。

测试用例数据：
{json.dumps(case.case_data, ensure_ascii=False, indent=2)}

要求：
1. 代码结构清晰，符合 {framework} 的最佳实践。
2. 包含必要的注释、断言(Assertions)和等待机制。
3. 请只返回代码内容，不要使用Markdown代码块包裹(不要使用```python等)，直接输出纯文本代码。"""

        result = await llm.generate_async(prompt)
        
        # Clean markdown code block if model still outputs it
        if result.startswith("```"):
            lines = result.split("\n")
            if len(lines) > 1 and lines[0].startswith("```"):
                lines = lines[1:]
            if len(lines) > 0 and lines[-1].startswith("```"):
                lines = lines[:-1]
            result = "\n".join(lines)
            
        return result
