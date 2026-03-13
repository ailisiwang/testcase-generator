"""测试用户认证"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.services.auth import AuthService
from app.schemas.user import UserCreate, LoginRequest
from app.models.user import User


class TestUserRegistration:
    """用户注册测试"""

    def test_register_success(self, mock_db_session):
        """测试成功注册"""
        # Arrange
        user_data = UserCreate(
            username="newuser",
            email="new@example.com",
            password="password123",
            employee_id="EMP001"
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Mock the User object creation
        mock_user = Mock()
        mock_user.username = "newuser"
        mock_user.email = "new@example.com"
        mock_user.employee_id = "EMP001"
        mock_user.id = 1
        mock_user.is_active = True
        mock_user.created_at = datetime.utcnow()

        with patch('app.services.auth.User', return_value=mock_user):
            with patch('app.services.auth.get_password_hash', return_value='hashed_password'):
                # Act
                result = AuthService.register(mock_db_session, user_data)

        # Assert
        assert result.username == "newuser"
        assert result.email == "new@example.com"
        assert result.employee_id == "EMP001"
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    def test_register_duplicate_username(self, mock_db_session, mock_user):
        """测试重复用户名"""
        user_data = UserCreate(
            username="testuser",
            email="new@example.com",
            password="password123"
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(ValueError) as exc_info:
            AuthService.register(mock_db_session, user_data)

        assert "Username or email already exists" in str(exc_info.value)

    def test_register_duplicate_email(self, mock_db_session, mock_user):
        """测试重复邮箱"""
        user_data = UserCreate(
            username="newuser",
            email="test@example.com",
            password="password123"
        )

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

        with pytest.raises(ValueError) as exc_info:
            AuthService.register(mock_db_session, user_data)

        assert "Username or email already exists" in str(exc_info.value)

    def test_register_invalid_email_format(self):
        """测试无效邮箱格式"""
        with pytest.raises(Exception):
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123"
            )

    def test_register_password_too_short(self):
        """测试密码太短 - 由应用层验证，这里测试schema接受"""
        user_data = UserCreate(
            username="testuser",
            email="test@example.com",
            password="short"
        )
        # Schema 不验证密码长度，应该能创建
        assert user_data.password == "short"


class TestUserLogin:
    """用户登录测试"""

    def test_login_success(self, mock_db_session, mock_user):
        """测试成功登录"""
        login_data = LoginRequest(username="testuser", password="testpassword123")

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('app.services.auth.verify_password', return_value=True):
            result = AuthService.authenticate(mock_db_session, login_data)

        assert result is not None
        assert result.username == "testuser"

    def test_login_wrong_password(self, mock_db_session, mock_user):
        """测试错误密码"""
        login_data = LoginRequest(username="testuser", password="wrongpassword")

        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('app.services.auth.verify_password', return_value=False):
            result = AuthService.authenticate(mock_db_session, login_data)

        assert result is None

    def test_login_user_not_found(self, mock_db_session):
        """测试用户不存在"""
        login_data = LoginRequest(username="nonexistent", password="password123")

        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        result = AuthService.authenticate(mock_db_session, login_data)

        assert result is None

    def test_login_inactive_user(self, mock_db_session):
        """测试未激活用户"""
        login_data = LoginRequest(username="inactive", password="password123")

        inactive_user = Mock()
        inactive_user.is_active = False
        inactive_user.password_hash = "hash"

        mock_db_session.query.return_value.filter.return_value.first.return_value = inactive_user

        with patch('app.services.auth.verify_password', return_value=True):
            result = AuthService.authenticate(mock_db_session, login_data)

        assert result is None

    def test_jwt_token_verification(self, sample_jwt_token):
        """测试 JWT token 验证"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "1",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1)
            }

            mock_user = Mock()
            mock_user.id = 1

            mock_db = Mock()
            mock_db.query.return_value.filter.return_value.first.return_value = mock_user

            result = AuthService.get_current_user(mock_db, sample_jwt_token)

            assert result is not None
            assert result.id == 1

    def test_jwt_token_invalid(self, mock_db_session):
        """测试无效 JWT token"""
        with patch('app.services.auth.decode_token', return_value=None):
            result = AuthService.get_current_user(mock_db_session, "invalid_token")

            assert result is None

    def test_jwt_token_wrong_type(self, mock_db_session):
        """测试错误类型的 JWT token"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "1",
                "type": "wrong_type"
            }

            result = AuthService.get_current_user(mock_db_session, "token")

            assert result is None


class TestTokenCreation:
    """Token 创建测试"""

    def test_create_access_and_refresh_tokens(self):
        """测试创建访问令牌和刷新令牌"""
        user_id = 1

        tokens = AuthService.create_tokens(user_id)

        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"
        assert len(tokens["access_token"]) > 0
        assert len(tokens["refresh_token"]) > 0

    def test_refresh_access_token_success(self, sample_refresh_token):
        """测试刷新访问令牌成功"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "123",
                "type": "refresh",
                "exp": datetime.utcnow() + timedelta(days=1)
            }

            result = AuthService.refresh_access_token(sample_refresh_token)

            assert result is not None
            assert isinstance(result, str)

    def test_refresh_access_token_invalid(self):
        """测试刷新令牌无效"""
        with patch('app.services.auth.decode_token', return_value=None):
            result = AuthService.refresh_access_token("invalid_token")

            assert result is None

    def test_refresh_access_token_wrong_type(self):
        """测试刷新令牌类型错误"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "type": "access",
                "sub": "123"
            }

            result = AuthService.refresh_access_token("token")

            assert result is None

    def test_refresh_access_token_no_user_id(self):
        """测试刷新令牌缺少用户ID"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "type": "refresh"
            }

            result = AuthService.refresh_access_token("token")

            assert result is None


class TestGetCurrentUser:
    """获取当前用户测试"""

    def test_get_current_user_success(self, mock_db_session, mock_user):
        """测试成功获取当前用户"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "1",
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1)
            }

            mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user

            result = AuthService.get_current_user(mock_db_session, "valid_token")

            assert result is not None
            assert result.id == 1

    def test_get_current_user_invalid_token(self, mock_db_session):
        """测试无效令牌获取用户"""
        with patch('app.services.auth.decode_token', return_value=None):
            result = AuthService.get_current_user(mock_db_session, "invalid_token")

            assert result is None

    def test_get_current_user_not_found_in_db(self, mock_db_session):
        """测试令牌有效但用户不存在"""
        with patch('app.services.auth.decode_token') as mock_decode:
            mock_decode.return_value = {
                "sub": "999",
                "type": "access"
            }

            mock_db_session.query.return_value.filter.return_value.first.return_value = None

            result = AuthService.get_current_user(mock_db_session, "token")

            assert result is None
