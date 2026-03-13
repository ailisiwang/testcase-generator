"""测试安全工具模块"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

from app.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    create_fernet,
    encrypt_api_key,
    decrypt_api_key
)


class TestPasswordHashing:
    """密码哈希测试"""

    def test_get_password_hash_returns_string(self):
        """测试密码哈希返回字符串"""
        password = "test_password_123"
        hashed = get_password_hash(password)

        assert isinstance(hashed, str)
        assert len(hashed) > 0
        assert hashed != password

    def test_password_hash_is_unique(self):
        """测试相同密码生成不同哈希值（盐值）"""
        password = "same_password"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """测试验证正确的密码"""
        password = "correct_password"
        hashed = get_password_hash(password)

        result = verify_password(password, hashed)

        assert result is True

    def test_verify_password_incorrect(self):
        """测试验证错误的密码"""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = get_password_hash(password)

        result = verify_password(wrong_password, hashed)

        assert result is False

    def test_verify_password_empty_plain(self):
        """测试空密码验证"""
        hashed = get_password_hash("some_password")

        result = verify_password("", hashed)

        assert result is False

    def test_verify_password_empty_hash(self):
        """测试空哈希验证"""
        result = verify_password("password", "")

        assert result is False

    def test_verify_password_both_empty(self):
        """测试两者都为空"""
        result = verify_password("", "")

        assert result is False


class TestJWTTokens:
    """JWT Token 测试"""

    def test_create_access_token_returns_string(self):
        """测试创建访问令牌返回字符串"""
        data = {"sub": "123"}

        token = create_access_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """测试创建带过期时间的访问令牌"""
        data = {"sub": "123"}
        expires = timedelta(minutes=30)

        token = create_access_token(data, expires)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_contains_type(self):
        """测试访问令牌包含类型字段"""
        data = {"sub": "123"}

        token = create_access_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["type"] == "access"
        assert "exp" in payload

    def test_create_refresh_token_returns_string(self):
        """测试创建刷新令牌返回字符串"""
        data = {"sub": "123"}

        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_type(self):
        """测试刷新令牌包含类型字段"""
        data = {"sub": "123"}

        token = create_refresh_token(data)
        payload = decode_token(token)

        assert payload is not None
        assert payload["type"] == "refresh"
        assert "exp" in payload

    def test_decode_token_valid(self):
        """测试解码有效令牌"""
        data = {"sub": "123", "username": "testuser"}
        token = create_access_token(data)

        payload = decode_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["username"] == "testuser"

    def test_decode_token_invalid(self):
        """测试解码无效令牌"""
        invalid_token = "invalid.token.here"

        payload = decode_token(invalid_token)

        assert payload is None

    def test_decode_token_empty(self):
        """测试解码空令牌"""
        payload = decode_token("")

        assert payload is None

    def test_access_token_expiry_future(self):
        """测试访问令牌未来过期时间"""
        data = {"sub": "123"}
        token = create_access_token(data)

        payload = decode_token(token)
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        assert exp_time > now

    def test_refresh_token_expiry_longer(self):
        """测试刷新令牌有过期时间更长"""
        data = {"sub": "123"}
        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = decode_token(access_token)
        refresh_payload = decode_token(refresh_token)

        # 刷新令牌应该有过期时间（7天）
        assert refresh_payload["exp"] > access_payload["exp"]


class TestFernetEncryption:
    """Fernet 加密测试"""

    def test_create_fernet_returns_instance(self):
        """测试创建 Fernet 实例"""
        # 使用默认的 settings，_get_encryption_key 会生成正确的 key
        f = create_fernet()

        assert f is not None

    def test_encrypt_api_key_returns_string(self):
        """测试加密 API Key 返回字符串"""
        api_key = "sk-test-api-key-12345"

        encrypted = encrypt_api_key(api_key)

        assert isinstance(encrypted, str)
        # 当加密成功时，密文应该不同于原文
        assert encrypted != api_key

    def test_decrypt_api_key_returns_original(self):
        """测试解密 API Key 返回原始值"""
        api_key = "sk-test-api-key-12345"

        encrypted = encrypt_api_key(api_key)
        decrypted = decrypt_api_key(encrypted)

        assert decrypted == api_key

    def test_encrypt_decrypt_cycle(self):
        """测试加密解密循环"""
        original_keys = [
            "sk-test-key-1",
            "sk-1234567890",
            "a" * 50,  # 长字符串
            "special!@#$%^&*()_+-=[]{}|;:',.<>?/`~"
        ]

        for key in original_keys:
            encrypted = encrypt_api_key(key)
            decrypted = decrypt_api_key(encrypted)
            assert decrypted == key

    def test_decrypt_invalid_string(self):
        """测试解密无效字符串"""
        invalid_encrypted = "not-encrypted-data"

        # 应该返回原始字符串或捕获异常
        result = decrypt_api_key(invalid_encrypted)

        # 根据实现，应该返回原始字符串
        assert result == invalid_encrypted

    def test_decrypt_empty_string(self):
        """测试解密空字符串"""
        result = decrypt_api_key("")

        assert result == ""

    def test_encrypt_empty_string(self):
        """测试加密空字符串"""
        encrypted = encrypt_api_key("")
        decrypted = decrypt_api_key(encrypted)

        assert decrypted == ""

    def test_encrypt_key_different_each_time(self):
        """测试加密产生不同的结果（由于随机性）"""
        api_key = "sk-test-key"

        encrypted1 = encrypt_api_key(api_key)
        encrypted2 = encrypt_api_key(api_key)

        # Fernet 加密包含时间戳，每次结果不同
        # 但解密后应该相同
        assert encrypted1 != encrypted2
        assert decrypt_api_key(encrypted1) == api_key
        assert decrypt_api_key(encrypted2) == api_key


class TestEdgeCases:
    """边界条件测试"""

    def test_token_with_unicode_data(self):
        """测试包含 Unicode 数据的令牌"""
        data = {"sub": "123", "name": "测试用户"}

        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["name"] == "测试用户"

    def test_password_hash_unicode(self):
        """测试 Unicode 密码哈希"""
        password = "密码测试123!@#"

        hashed = get_password_hash(password)
        result = verify_password(password, hashed)

        assert result is True

    def test_very_long_password(self):
        """测试超长密码 - bcrypt 限制为 72 字节"""
        # bcrypt 限制密码最大 72 字节
        password = "a" * 50  # 使用合理长度

        hashed = get_password_hash(password)
        result = verify_password(password, hashed)

        assert result is True

    def test_password_too_long_for_bcrypt(self):
        """测试超过 bcrypt 限制的密码"""
        # bcrypt 限制密码最大 72 字节，超过会抛出异常
        password = "a" * 100

        with pytest.raises(ValueError, match="password cannot be longer than 72 bytes"):
            get_password_hash(password)

    def test_token_with_special_characters(self):
        """测试包含特殊字符的令牌数据"""
        data = {"sub": "123", "data": "!@#$%^&*()_+-=[]{}|;:',.<>?/"}

        token = create_access_token(data)
        payload = decode_token(token)

        assert payload["data"] == data["data"]
