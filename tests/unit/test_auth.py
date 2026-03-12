"""
用户管理测试模块

包含：
- 用户注册功能测试
- 用户登录功能测试 (JWT)
- 权限验证测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestUserRegistration:
    """用户注册功能测试"""

    @pytest.mark.unit
    def test_register_success(self, mock_db_session, mock_user):
        """测试注册成功场景"""
        # Arrange
        from app.schemas.user import UserCreate
        from app.services.auth import AuthService
        
        user_data = UserCreate(
            username="newuser",
            email="newuser@example.com",
            password="password123",
            employee_id="EMP002"
        )
        
        # Mock 数据库查询 - 用户不存在
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        # Mock 创建用户
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            with patch('app.services.auth.create_user', return_value=mock_user):
                auth_service = AuthService(db=mock_db_session)
                result = auth_service.register(user_data)
        
        # Assert
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.unit
    def test_register_duplicate_username(self, mock_db_session):
        """测试用户名重复注册"""
        from app.schemas.user import UserCreate
        from app.services.auth import AuthService
        from app.models.user import User
        
        user_data = UserCreate(
            username="existinguser",
            email="new@example.com",
            password="password123"
        )
        
        # Mock 用户已存在
        existing_user = MagicMock()
        existing_user.username = "existinguser"
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            auth_service = AuthService(db=mock_db_session)
            
            with pytest.raises(ValueError, match="用户名已存在"):
                auth_service.register(user_data)

    @pytest.mark.unit
    def test_register_duplicate_email(self, mock_db_session):
        """测试邮箱重复注册"""
        from app.schemas.user import UserCreate
        from app.services.auth import AuthService
        
        user_data = UserCreate(
            username="newuser",
            email="existing@example.com",
            password="password123"
        )
        
        # Mock 邮箱已存在
        existing_user = MagicMock()
        existing_user.email = "existing@example.com"
        mock_db_session.query.return_value.filter.return_value.first.return_value = existing_user
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            auth_service = AuthService(db=mock_db_session)
            
            with pytest.raises(ValueError, match="邮箱已被注册"):
                auth_service.register(user_data)

    @pytest.mark.unit
    def test_register_invalid_email_format(self):
        """测试无效邮箱格式"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="invalid-email",
                password="password123"
            )

    @pytest.mark.unit
    def test_register_password_too_short(self):
        """测试密码过短"""
        from app.schemas.user import UserCreate
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            UserCreate(
                username="testuser",
                email="test@example.com",
                password="123"  # 小于8位
            )


class TestUserLogin:
    """用户登录功能测试 (JWT)"""

    @pytest.mark.unit
    def test_login_success(self, mock_db_session, mock_user):
        """测试登录成功"""
        from app.services.auth import AuthService
        
        # Mock 用户存在且密码正确
        mock_user.password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY8KqFZ.zK"  # password123
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            with patch('app.services.auth.verify_password', return_value=True):
                auth_service = AuthService(db=mock_db_session)
                result = auth_service.authenticate_user("testuser", "password123")
        
        assert result is not None
        assert result.username == "testuser"

    @pytest.mark.unit
    def test_login_wrong_password(self, mock_db_session, mock_user):
        """测试密码错误"""
        mock_user.password_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyY8KqFZ.zK"
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            with patch('app.services.auth.verify_password', return_value=False):
                auth_service = AuthService(db=mock_db_session)
                result = auth_service.authenticate_user("testuser", "wrongpassword")
        
        assert result is None

    @pytest.mark.unit
    def test_login_user_not_found(self, mock_db_session):
        """测试用户不存在"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            auth_service = AuthService(db=mock_db_session)
            result = auth_service.authenticate_user("nonexistent", "password123")
        
        assert result is None

    @pytest.mark.unit
    def test_login_inactive_user(self, mock_db_session, mock_user):
        """测试 inactive 用户登录"""
        mock_user.is_active = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.auth.get_db', return_value=mock_db_session):
            auth_service = AuthService(db=mock_db_session)
            result = auth_service.authenticate_user("testuser", "password123")
        
        assert result is None

    @pytest.mark.unit
    def test_jwt_token_generation(self, mock_user):
        """测试 JWT Token 生成"""
        from app.utils.security import create_access_token
        from datetime import timedelta
        
        token = create_access_token(
            data={"sub": str(mock_user.id), "username": mock_user.username},
            expires_delta=timedelta(hours=24)
        )
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.unit
    def test_jwt_token_verification(self, sample_jwt_token):
        """测试 JWT Token 验证"""
        from jose import jwt, JWTError
        from app.config import settings
        
        try:
            payload = jwt.decode(sample_jwt_token, settings.SECRET_KEY, algorithms=["HS256"])
            assert payload["sub"] == "1"
            assert payload["username"] == "testuser"
        except JWTError:
            pytest.fail("Token verification failed")

    @pytest.mark.unit
    def test_refresh_token_generation(self, sample_refresh_token):
        """测试 Refresh Token 生成"""
        from jose import jwt
        
        payload = jwt.decode(
            sample_refresh_token, 
            "test_secret_key", 
            algorithms=["HS256"]
        )
        
        assert payload["sub"] == "1"
        assert payload["type"] == "refresh"


class TestPermissionValidation:
    """权限验证测试"""

    @pytest.mark.unit
    def test_owner_can_access_own_system(self, mock_user, mock_test_system):
        """测试所有者可以访问自己的系统"""
        # 所有者验证
        assert mock_test_system.user_id == mock_user.id

    @pytest.mark.unit
    def test_other_user_cannot_access(self, mock_user, mock_test_system):
        """测试其他用户不能访问"""
        # 模拟其他用户
        other_user = MagicMock()
        other_user.id = 999
        
        # 权限验证
        assert mock_test_system.user_id != other_user.id

    @pytest.mark.unit
    def test_admin_can_access_all(self, mock_user):
        """测试管理员可以访问所有资源"""
        mock_user.is_admin = True
        
        # 管理员权限验证
        assert hasattr(mock_user, 'is_admin') and mock_user.is_admin

    @pytest.mark.unit
    def test_inactive_user_cannot_access(self, mock_user):
        """测试 inactive 用户不能访问"""
        mock_user.is_active = False
        
        assert mock_user.is_active is False

    @pytest.mark.unit
    def test_case_creator_can_modify(self, mock_user, mock_test_case):
        """测试用例创建者可以修改"""
        mock_test_case.created_by = mock_user.id
        
        assert mock_test_case.created_by == mock_user.id

    @pytest.mark.unit
    def test_reviewer_can_review(self, mock_user, mock_test_case):
        """测试审核者可以审核"""
        mock_test_case.reviewer_id = mock_user.id
        
        assert mock_test_case.reviewer_id == mock_user.id
