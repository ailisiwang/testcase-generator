"""Case generation service"""
import json
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.test_case import TestCase, CaseVersion
from app.models.model_config import ModelConfig
from app.models.system import TestSystem
from app.utils.security import decrypt_api_key
from app.llm.base import get_llm_provider


class CaseGeneratorService:
    """Test case generation service"""
    
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

请以JSON数组格式返回，每条用例是一个完整的测试用例对象。
要求：
1. 覆盖正常场景和异常场景
2. 测试步骤清晰可执行
3. 预期结果明确
4. 返回有效的JSON数组格式

直接返回JSON数组，不要其他内容："""
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
        
        # Build prompt
        prompt = CaseGeneratorService._build_generation_prompt(requirement, system_fields, count)
        
        # Generate cases
        try:
            result = await llm.generate_async(prompt)
            
            # Parse JSON response
            cases = CaseGeneratorService._parse_cases(result)
            return cases
        except Exception as e:
            raise ValueError(f"Failed to generate cases: {str(e)}")
    
    @staticmethod
    def _parse_cases(response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to cases"""
        # Try to extract JSON array
        try:
            # Find JSON array in response
            start = response.find('[')
            end = response.rfind(']') + 1
            
            if start != -1 and end != 0:
                json_str = response[start:end]
                cases = json.loads(json_str)
                return cases
        except json.JSONDecodeError:
            pass
        
        # Return empty list if parsing fails
        return []
    
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
{file_content}

请以JSON数组格式返回测试用例，包含：用例标题、前置条件、测试步骤、预期结果等字段。
直接返回JSON数组："""
        
        result = await llm.generate_async(prompt)
        return CaseGeneratorService._parse_cases(result)
