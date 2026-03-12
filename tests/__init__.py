"""
测试初始化文件
"""

# 测试配置
TEST_CONFIG = {
    "database_url": "sqlite:///./test.db",
    "jwt_secret": "test_secret_key_for_testing_only",
    "jwt_algorithm": "HS256",
    "jwt_expiration_hours": 24,
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "allowed_file_types": [".txt", ".pdf", ".docx", ".md"],
}

# Mock 配置
MOCK_CONFIG = {
    "enable_mocks": True,
    "mock_llm_responses": True,
    "mock_db": True,
}
