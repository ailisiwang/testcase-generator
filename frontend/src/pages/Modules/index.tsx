import React, { useEffect, useState } from 'react'
import {
  Card,
  Tree,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Typography,
  Breadcrumb,
  Spin
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
  FolderOpenOutlined,
  HomeOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import { systemApi, moduleApi } from '../../api/services'
import type { Module } from '../../types'

const { Title } = Typography

const Modules: React.FC = () => {
  const { systemId } = useParams<{ systemId: string }>()
  const navigate = useNavigate()
  const [modules, setModules] = useState<Module[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingModule, setEditingModule] = useState<Module | null>(null)
  const [parentId, setParentId] = useState<number | null>(null)
  const [systemName, setSystemName] = useState('')
  const [form] = Form.useForm()

  useEffect(() => {
    if (systemId) {
      fetchData()
    }
  }, [systemId])

  const fetchData = async () => {
    try {
      // 获取系统信息
      const systemRes = await systemApi.getSystem(Number(systemId))
      setSystemName(systemRes.data.name)
      
      // 获取模块列表
      const modulesRes = await moduleApi.getModules(Number(systemId))
      const treeData = buildTree(modulesRes.data.items || [])
      setModules(treeData)
    } catch (error) {
      message.error('获取数据失败')
    } finally {
      setLoading(false)
    }
  }

  // 构建树形结构
  const buildTree = (items: Module[]): Module[] => {
    const map: Record<number, Module> = {}
    const roots: Module[] = []

    items.forEach((item) => {
      map[item.id] = { ...item, children: [] }
    })

    items.forEach((item) => {
      if (item.parent_id && map[item.parent_id]) {
        map[item.parent_id].children!.push(map[item.id])
      } else {
        roots.push(map[item.id])
      }
    })

    return roots
  }

  const handleCreate = (parentId?: number) => {
    setEditingModule(null)
    setParentId(parentId || null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Module) => {
    setEditingModule(record)
    setParentId(record.parent_id)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await moduleApi.deleteModule(id)
      message.success('删除成功')
      fetchData()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: { name: string; description?: string }) => {
    try {
      if (editingModule) {
        await moduleApi.updateModule(editingModule.id, values)
        message.success('更新成功')
      } else {
        await moduleApi.createModule(Number(systemId), {
          ...values,
          parent_id: parentId || undefined,
        })
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchData()
    } catch (error) {
      message.error(editingModule ? '更新失败' : '创建失败')
    }
  }

  const renderTreeNodes = (data: Module[]): any[] => {
    return data.map((item) => ({
      key: item.id,
      title: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
          <span>
            {item.children?.length ? <FolderOpenOutlined /> : <FolderOutlined />}
            {' '}{item.name}
          </span>
          <Space size="small" onClick={(e) => e.stopPropagation()}>
            <Button type="text" size="small" icon={<PlusOutlined />} onClick={() => handleCreate(item.id)} />
            <Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(item)} />
            <Popconfirm
              title="确定删除此模块？"
              description="删除后子模块也将被删除"
              onConfirm={() => handleDelete(item.id)}
            >
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          </Space>
        </div>
      ),
      children: item.children ? renderTreeNodes(item.children) : [],
    }))
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div>
      <Breadcrumb
        style={{ marginBottom: 16 }}
        items={[
          { title: <a onClick={() => navigate('/systems')}>测试系统</a> },
          { title: systemName },
        ]}
      />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          模块管理 - {systemName}
        </Title>
        <Space>
          <Button icon={<HomeOutlined />} onClick={() => handleCreate(undefined)}>
            新建根模块
          </Button>
        </Space>
      </div>

      <Card>
        <Tree
          className="module-tree"
          treeData={renderTreeNodes(modules)}
          defaultExpandAll
          showIcon
          blockNode
        />
        {modules.length === 0 && (
          <div style={{ textAlign: 'center', padding: 40, color: '#999' }}>
            暂无模块，请点击"新建根模块"创建
          </div>
        )}
      </Card>

      <Modal
        title={editingModule ? '编辑模块' : (parentId ? '新建子模块' : '新建根模块')}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={500}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="模块名称"
            rules={[{ required: true, message: '请输入模块名称' }]}
          >
            <Input placeholder="请输入模块名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea rows={2} placeholder="请输入模块描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Modules
