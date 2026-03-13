import React, { useEffect, useState } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  message,
  Popconfirm,
  Typography
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  FolderOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { systemApi } from '../../api/services'
import type { System } from '../../types'

const { Title } = Typography
const { TextArea } = Input

const Systems: React.FC = () => {
  const navigate = useNavigate()
  const [systems, setSystems] = useState<System[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingSystem, setEditingSystem] = useState<System | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchSystems()
  }, [])

  const fetchSystems = async () => {
    try {
      const res = await systemApi.getSystems({ page_size: 100 })
      setSystems(res.data || [])
    } catch (error) {
      message.error('获取系统列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingSystem(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: System) => {
    setEditingSystem(record)
    form.setFieldsValue({
      name: record.name,
      description: record.description,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await systemApi.deleteSystem(id)
      message.success('删除成功')
      fetchSystems()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: { name: string; description?: string }) => {
    try {
      if (editingSystem) {
        await systemApi.updateSystem(editingSystem.id, values)
        message.success('更新成功')
      } else {
        await systemApi.createSystem(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchSystems()
    } catch (error) {
      message.error(editingSystem ? '更新失败' : '创建失败')
    }
  }

  const columns = [
    {
      title: '系统名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: System) => (
        <Space>
          <FolderOutlined style={{ color: '#1890ff' }} />
          <a onClick={() => navigate(`/systems/${record.id}/modules`)}>{name}</a>
        </Space>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (desc: string) => desc || '-',
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: System) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<FolderOutlined />}
            onClick={() => navigate(`/systems/${record.id}/modules`)}
          >
            模块
          </Button>
          <Button
            type="link"
            size="small"
            icon={<SettingOutlined />}
            onClick={() => navigate(`/cases/generate/${record.id}`)}
          >
            生成
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定删除此系统？"
            description="删除后相关模块和用例也将被删除"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" size="small" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>测试系统管理</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建系统
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={systems}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={editingSystem ? '编辑系统' : '新建系统'}
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
            label="系统名称"
            rules={[{ required: true, message: '请输入系统名称' }]}
          >
            <Input placeholder="请输入系统名称" />
          </Form.Item>
          <Form.Item
            name="description"
            label="描述"
          >
            <TextArea rows={3} placeholder="请输入系统描述" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Systems
