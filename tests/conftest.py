"""
测试公共配置和共享 Fixtures
"""
import os
import sys
import pytest
from unittest.mock import MagicMock, AsyncMock
from typing import Generator
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加后端路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# 测试数据库配置
TEST_DATABASE_URL = "sqlite:///./test.db"

# Mock 用户数据
TEST_USER_DATA = {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "employee_id": "EMP001",
    "is_active": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

TEST_USER_PASSWORD = "testpassword123"

# Mock 测试系统数据
TEST_SYSTEM_DATA = {
    "id": 1,
    "user_id": 1,
    "name": "测试系统",
    "description": "这是一个测试系统",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Mock 模块数据
TEST_MODULE_DATA = {
    "id": 1,
    "system_id": 1,
    "name": "用户管理",
    "parent_id": None,
    "description": "用户管理模块",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Mock 测试用例数据
TEST_CASE_DATA = {
    "id": 1,
    "system_id": 1,
    "module_id": 1,
    "case_data": {
        "title": "用户登录测试",
        "precondition": "用户已注册",
        "steps": ["打开登录页面", "输入用户名密码", "点击登录"],
        "expected": "登录成功"
    },
    "version": 1,
    "status": "draft",
    "created_by": 1,
    "reviewer_id": None,
    "review_status": "pending",
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}

# Mock 模型配置数据
TEST_MODEL_CONFIG_DATA = {
    "id": 1,
    "user_id": 1,
    "provider": "zhipu",
    "model_name": "glm-4",
    "api_key_encrypted": "encrypted_key_here",
    "api_base_url": "https://open.bigmodel.cn/api/paas/v4",
    "temperature": 0.7,
    "max_tokens": 2048,
    "is_active": True,
    "created_at": datetime.utcnow(),
    "updated_at": datetime.utcnow()
}


@pytest.fixture
def mock_db_session():
    """Mock 数据库会话"""
    session = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Mock 用户对象"""
    user = MagicMock()
    user.id = TEST_USER_DATA["id"]
    user.username = TEST_USER_DATA["username"]
    user.email = TEST_USER_DATA["email"]
    user.employee_id = TEST_USER_DATA["employee_id"]
    user.is_active = TEST_USER_DATA["is_active"]
    user.password_hash = "hashed_password"
    return user


@pytest.fixture
def mock_test_system():
    """Mock 测试系统对象"""
    system = MagicMock()
    system.id = TEST_SYSTEM_DATA["id"]
    system.user_id = TEST_SYSTEM_DATA["user_id"]
    system.name = TEST_SYSTEM_DATA["name"]
    system.description = TEST_SYSTEM_DATA["description"]
    return system


@pytest.fixture
def mock_module():
    """Mock 模块对象"""
    module = MagicMock()
    module.id = TEST_MODULE_DATA["id"]
    module.system_id = TEST_MODULE_DATA["system_id"]
    module.name = TEST_MODULE_DATA["name"]
    module.parent_id = TEST_MODULE_DATA["parent_id"]
    module.description = TEST_MODULE_DATA["description"]
    return module


@pytest.fixture
def mock_test_case():
    """Mock 测试用例对象"""
    case = MagicMock()
    case.id = TEST_CASE_DATA["id"]
    case.system_id = TEST_CASE_DATA["system_id"]
    case.module_id = TEST_CASE_DATA["module_id"]
    case.case_data = TEST_CASE_DATA["case_data"]
    case.version = TEST_CASE_DATA["version"]
    case.status = TEST_CASE_DATA["status"]
    case.created_by = TEST_CASE_DATA["created_by"]
    case.reviewer_id = TEST_CASE_DATA["reviewer_id"]
    case.review_status = TEST_CASE_DATA["review_status"]
    return case


@pytest.fixture
def mock_model_config():
    """Mock 模型配置对象"""
    config = MagicMock()
    config.id = TEST_MODEL_CONFIG_DATA["id"]
    config.user_id = TEST_MODEL_CONFIG_DATA["user_id"]
    config.provider = TEST_MODEL_CONFIG_DATA["provider"]
    config.model_name = TEST_MODEL_CONFIG_DATA["model_name"]
    config.api_key_encrypted = TEST_MODEL_CONFIG_DATA["api_key_encrypted"]
    config.api_base_url = TEST_MODEL_CONFIG_DATA["api_base_url"]
    config.temperature = TEST_MODEL_CONFIG_DATA["temperature"]
    config.max_tokens = TEST_MODEL_CONFIG_DATA["max_tokens"]
    config.is_active = TEST_MODEL_CONFIG_DATA["is_active"]
    return config


@pytest.fixture
def mock_llm_stream():
    """Mock LLM 流式输出"""
    async def generate():
        chunks = [
            "测试",
            "用例",
            "生成",
            "中..."
        ]
        for chunk in chunks:
            yield chunk
    
    return generate()


@pytest.fixture
def sample_jwt_token():
    """生成测试用 JWT Token"""
    from jose import jwt
    from datetime import datetime, timedelta
    
    SECRET_KEY = "test_secret_key"
    ALGORITHM = "HS256"
    
    payload = {
        "sub": "1",
        "username": "testuser",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def sample_refresh_token():
    """生成测试用 Refresh Token"""
    from jose import jwt
    from datetime import datetime, timedelta
    
    SECRET_KEY = "test_secret_key"
    ALGORITHM = "HS256"
    
    payload = {
        "sub": "1",
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@pytest.fixture
def sample_excel_content():
    """生成测试用 Excel 内容"""
    return {
        "headers": ["用例ID", "标题", "前置条件", "测试步骤", "预期结果"],
        "rows": [
            [1, "用户登录-正确密码", "用户已注册", "1. 打开登录页\n2. 输入用户名密码\n3. 点击登录", "登录成功"],
            [2, "用户登录-错误密码", "用户已注册", "1. 打开登录页\n2. 输入错误密码\n3. 点击登录", "提示密码错误"]
        ]
    }


@pytest.fixture
def sample_text_content():
    """生成测试用文本内容"""
    return """
    需求文档:
    用户登录功能
    1. 用户可以通过用户名和密码登录
    2. 登录成功后跳转到首页
    3. 登录失败时显示错误提示
    """


@pytest.fixture
def sample_pdf_content():
    """生成测试用 PDF 内容"""
    return b"%PDF-1.4 Mock PDF Content"


@pytest.fixture
def mock_file_upload():
    """Mock 文件上传"""
    file = MagicMock()
    file.filename = "test_requirement.txt"
    file.content_type = "text/plain"
    file.read = MagicMock(return_value=b"Test content")
    return file
