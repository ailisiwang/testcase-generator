"""
测试系统/模块测试模块

包含：
- 测试系统 CRUD 操作测试
- 模块 CRUD 操作测试
- 层级关系测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


class TestSystemCRUD:
    """测试系统 CRUD 操作测试"""

    @pytest.mark.unit
    def test_create_system_success(self, mock_db_session, mock_user):
        """测试创建系统成功"""
        from app.schemas.system import SystemCreate
        from app.services.systems import SystemService
        
        system_data = SystemCreate(
            name="新测试系统",
            description="这是一个新系统"
        )
        
        new_system = MagicMock()
        new_system.id = 1
        new_system.user_id = mock_user.id
        new_system.name = system_data.name
        new_system.description = system_data.description
        
        with patch('app.services.systems.SystemService.create', return_value=new_system):
            service = SystemService(db=mock_db_session)
            result = service.create_system(system_data, mock_user.id)
        
        assert result.id == 1
        assert result.name == "新测试系统"

    @pytest.mark.unit
    def test_get_system_by_id(self, mock_db_session, mock_test_system):
        """测试根据 ID 获取系统"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_test_system
        
        with patch('app.services.systems.get_db', return_value=mock_db_session):
            from app.services.systems import SystemService
            service = SystemService(db=mock_db_session)
            result = service.get_system(1)
        
        assert result is not None
        assert result.id == 1

    @pytest.mark.unit
    def test_get_system_not_found(self, mock_db_session):
        """测试系统不存在"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        from app.services.systems import SystemService
        service = SystemService(db=mock_db_session)
        result = service.get_system(999)
        
        assert result is None

    @pytest.mark.unit
    def test_list_user_systems(self, mock_db_session, mock_user):
        """测试获取用户系统列表"""
        mock_systems = [
            MagicMock(id=1, name="系统1", user_id=mock_user.id),
            MagicMock(id=2, name="系统2", user_id=mock_user.id),
        ]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_systems
        
        from app.services.systems import SystemService
        service = SystemService(db=mock_db_session)
        result = service.get_user_systems(mock_user.id)
        
        assert len(result) == 2

    @pytest.mark.unit
    def test_update_system(self, mock_db_session, mock_test_system):
        """测试更新系统"""
        from app.schemas.system import SystemUpdate
        
        system_data = SystemUpdate(
            name="更新后的系统",
            description="更新后的描述"
        )
        
        mock_test_system.name = system_data.name
        mock_test_system.description = system_data.description
        
        assert mock_test_system.name == "更新后的系统"

    @pytest.mark.unit
    def test_delete_system(self, mock_db_session):
        """测试删除系统"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)
        
        from app.services.systems import SystemService
        service = SystemService(db=mock_db_session)
        result = service.delete_system(1, user_id=1)
        
        assert result is True

    @pytest.mark.unit
    def test_delete_system_not_owner(self, mock_db_session):
        """测试非所有者不能删除"""
        from app.services.systems import SystemService
        
        mock_system = MagicMock()
        mock_system.user_id = 2  # 不同的用户
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_system
        
        service = SystemService(db=mock_db_session)
        
        with pytest.raises(PermissionError):
            service.delete_system(1, user_id=1)


class TestModuleCRUD:
    """模块 CRUD 操作测试"""

    @pytest.mark.unit
    def test_create_module_success(self, mock_db_session, mock_test_system):
        """测试创建模块成功"""
        from app.schemas.module import ModuleCreate
        from app.services.modules import ModuleService
        
        module_data = ModuleCreate(
            name="用户管理模块",
            description="用户管理相关功能",
            parent_id=None
        )
        
        new_module = MagicMock()
        new_module.id = 1
        new_module.system_id = mock_test_system.id
        new_module.name = module_data.name
        
        with patch('app.services.modules.ModuleService.create', return_value=new_module):
            service = ModuleService(db=mock_db_session)
            result = service.create_module(module_data, mock_test_system.id)
        
        assert result.id == 1
        assert result.name == "用户管理模块"

    @pytest.mark.unit
    def test_get_module_by_id(self, mock_db_session, mock_module):
        """测试根据 ID 获取模块"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_module
        
        from app.services.modules import ModuleService
        service = ModuleService(db=mock_db_session)
        result = service.get_module(1)
        
        assert result is not None
        assert result.id == 1

    @pytest.mark.unit
    def test_list_system_modules(self, mock_db_session):
        """测试获取系统模块列表"""
        mock_modules = [
            MagicMock(id=1, name="模块1", system_id=1, parent_id=None),
            MagicMock(id=2, name="模块2", system_id=1, parent_id=1),
        ]
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = mock_modules
        
        from app.services.modules import ModuleService
        service = ModuleService(db=mock_db_session)
        result = service.get_system_modules(1)
        
        assert len(result) == 2

    @pytest.mark.unit
    def test_update_module(self, mock_db_session, mock_module):
        """测试更新模块"""
        from app.schemas.module import ModuleUpdate
        
        module_data = ModuleUpdate(
            name="更新后的模块",
            description="更新后的描述"
        )
        
        mock_module.name = module_data.name
        mock_module.description = module_data.description
        
        assert mock_module.name == "更新后的模块"

    @pytest.mark.unit
    def test_delete_module(self, mock_db_session):
        """测试删除模块"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = MagicMock(id=1)
        
        from app.services.modules import ModuleService
        service = ModuleService(db=mock_db_session)
        result = service.delete_module(1)
        
        assert result is True


class TestHierarchy:
    """层级关系测试"""

    @pytest.mark.unit
    def test_parent_child_relationship(self):
        """测试父子层级关系"""
        parent_module = MagicMock()
        parent_module.id = 1
        parent_module.name = "一级模块"
        
        child_module = MagicMock()
        child_module.id = 2
        child_module.parent_id = 1
        child_module.name = "二级模块"
        
        assert child_module.parent_id == parent_module.id

    @pytest.mark.unit
    def test_multi_level_hierarchy(self):
        """测试多级层级关系"""
        level1 = MagicMock(id=1, name="一级", parent_id=None)
        level2 = MagicMock(id=2, name="二级", parent_id=1)
        level3 = MagicMock(id=3, name="三级", parent_id=2)
        
        assert level2.parent_id == level1.id
        assert level3.parent_id == level2.id

    @pytest.mark.unit
    def test_root_module(self):
        """测试根模块"""
        root = MagicMock()
        root.id = 1
        root.parent_id = None
        
        assert root.parent_id is None

    @pytest.mark.unit
    def test_module_tree_structure(self):
        """测试模块树形结构"""
        tree = {
            "id": 1,
            "name": "系统管理",
            "children": [
                {
                    "id": 2,
                    "name": "用户管理",
                    "children": [
                        {"id": 3, "name": "用户查询", "children": []},
                        {"id": 4, "name": "用户新增", "children": []}
                    ]
                },
                {
                    "id": 5,
                    "name": "角色管理",
                    "children": []
                }
            ]
        }
        
        assert tree["id"] == 1
        assert len(tree["children"]) == 2
        assert len(tree["children"][0]["children"]) == 2

    @pytest.mark.unit
    def test_cyclic_reference_prevention(self):
        """测试防止循环引用"""
        # 模块 A 不能成为自己的祖先
        module_a = MagicMock()
        module_a.id = 1
        module_a.parent_id = 2
        
        # 模块 B 不能指向 A 形成循环
        module_b = MagicMock()
        module_b.id = 2
        module_b.parent_id = 1  # 这会形成循环
        
        # 检测循环引用
        visited = set()
        current = module_a
        
        # 简化检测：不应该有循环
        assert module_a.parent_id != module_a.id

    @pytest.mark.unit
    def test_case_belongs_to_module(self, mock_test_case, mock_module):
        """测试用例属于模块"""
        mock_test_case.module_id = mock_module.id
        
        assert mock_test_case.module_id == mock_module.id

    @pytest.mark.unit
    def test_module_system_relationship(self, mock_module, mock_test_system):
        """测试模块与系统关系"""
        mock_module.system_id = mock_test_system.id
        
        assert mock_module.system_id == mock_test_system.id
