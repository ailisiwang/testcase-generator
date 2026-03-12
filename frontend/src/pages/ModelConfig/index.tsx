import React, { useEffect, useState } from 'react'
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  message, 
  Popconfirm,
  Typography,
  Switch,
  Divider,
  Alert
} from 'antd'
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SettingOutlined,
  CheckCircleOutlined,
  SyncOutlined
} from '@ant-design/icons'
import { modelApi } from '../../api/services'

const { Title, Text } = Typography

interface ModelConfig {
  id: number
  provider: string
  model_name: string
  api_base_url?: string
  temperature: number
  max_tokens: number
  is_active: boolean
  is_default: boolean
  created_at: string
  updated_at: string
}

const MODEL_PROVIDERS = [
  { value: 'zhipu', label: '智谱 GLM', baseUrl: 'https://open.bigmodel.cn/api/paas/v4' },
  { value: 'openai', label: 'OpenAI', baseUrl: 'https://api.openai.com/v1' },
  { value: 'anthropic', label: 'Anthropic Claude', baseUrl: 'https://api.anthropic.com/v1' },
  { value: 'alibaba', label: '阿里千问', baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1' },
  { value: 'doubao', label: '字节豆包', baseUrl: 'https://ark.cn-beijing.volces.com/api/v3' },
  { value: 'custom', label: '自定义', baseUrl: '' },
]

const MODEL_OPTIONS: Record<string, string[]> = {
  zhipu: ['glm-4', 'glm-4-flash', 'glm-4-plus', 'glm-3-turbo'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229'],
  alibaba: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-max-longcontext'],
  doubao: ['doubao-pro-32k', 'doubao-lite-32k'],
  custom: [],
}

const ModelConfigPage: React.FC = () => {
  const [models, setModels] = useState<ModelConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null)
  const [selectedProvider, setSelectedProvider] = useState<string>('zhipu')
  const [testingId, setTestingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const res = await modelApi.getModels({ page_size: 100 })
      setModels(res.data.items || [])
    } catch (error) {
      message.error('获取模型配置失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingModel(null)
    setSelectedProvider('zhipu')
    form.resetFields()
    form.setFieldsValue({
      provider: 'zhipu',
      model_name: 'glm-4',
      temperature: 0.7,
      max_tokens: 2048,
    })
    setModalVisible(true)
  }

  const handleEdit = (record: ModelConfig) => {
    setEditingModel(record)
    setSelectedProvider(record.provider)
    form.setFieldsValue({
      provider: record.provider,
      model_name: record.model_name,
      api_key: '••••••••', // 不显示真实 key
      api_base_url: record.api_base_url,
      temperature: record.temperature,
      max_tokens: record.max_tokens,
      is_active: record.is_active,
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await modelApi.deleteModel(id)
      message.success('删除成功')
      fetchModels()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: { 
    provider: string;
    model_name: string;
    api_key?: string;
    api_base_url?: string;
    temperature: number;
    max_tokens: number;
    is_active?: boolean;
  }) => {
    try {
      const data = {
        provider: values.provider,
        model_name: values.model_name,
        api_key: values.api_key === '••••••••' ? undefined : values.api_key,
        api_base_url: values.api_base_url,
        temperature: values.temperature,
        max_tokens: values.max_tokens,
        is_active: values.is_active ?? true,
      }

      if (editingModel) {
        await modelApi.updateModel(editingModel.id, data)
        message.success('更新成功')
      } else {
        if (!values.api_key) {
          message.error('请输入 API Key')
          return
        }
        await modelApi.createModel(data)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchModels()
    } catch (error: any) {
      message.error(error.response?.data?.detail || (editingModel ? '更新失败' : '创建失败'))
    }
  }

  const handleTest = async (id: number) => {
    setTestingId(id)
    try {
      await modelApi.testModel(id)
      message.success('连接测试成功')
    } catch (error: any) {
      message.error(error.response?.data?.detail || '测试失败')
    } finally {
      setTestingId(null)
    }
  }

  const handleToggleActive = async (record: ModelConfig) => {
    try {
      await modelApi.updateModel(record.id, { is_active: !record.is_active })
      message.success(record.is_active ? '已禁用' : '已启用')
      fetchModels()
    } catch (error) {
      message.error('操作失败')
    }
  }

  const columns = [
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (provider: string) => {
        const p = MODEL_PROVIDERS.find(p => p.value === provider)
        return p?.label || provider
      },
    },
    {
      title: '模型',
      dataIndex: 'model_name',
      key: 'model_name',
      render: (name: string) => <Tag>{name}</Tag>,
    },
    {
      title: 'API 地址',
      dataIndex: 'api_base_url',
      key: 'api_base_url',
      ellipsis: true,
      render: (url: string) => (
        <Text type="secondary" style={{ fontSize: 12 }}>{url || '-'}</Text>
      ),
    },
    {
      title: '参数',
      key: 'params',
      render: (_: any, record: ModelConfig) => (
        <Space>
          <Tag>温度: {record.temperature}</Tag>
          <Tag>Max: {record.max_tokens}</Tag>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean, record: ModelConfig) => (
        <Switch
          checked={active}
          onChange={() => handleToggleActive(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
        />
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ModelConfig) => (
        <Space>
          <Button
            type="link"
            size="small"
            icon={<SyncOutlined spin={testingId === record.id} />}
            onClick={() => handleTest(record.id)}
            loading={testingId === record.id}
          >
            测试
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
            title="确定删除此模型配置？"
            onConfirm={() => handleDelete(record.id)}
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
        <Title level={2} style={{ margin: 0 }}>模型配置</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          新建配置
        </Button>
      </div>

      <Alert
        message="配置说明"
        description="在此页面配置大模型的 API Key 和参数。系统支持智谱 GLM、OpenAI、Claude、阿里千问、字节豆包等多种模型。"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Card>
        <Table
          columns={columns}
          dataSource={models}
          rowKey="id"
          loading={loading}
          pagination={false}
        />
      </Card>

      <Modal
        title={editingModel ? '编辑模型配置' : '新建模型配置'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="provider"
            label="模型提供商"
            rules={[{ required: true, message: '请选择模型提供商' }]}
          >
            <Select
              placeholder="选择提供商"
              onChange={setSelectedProvider}
              options={MODEL_PROVIDERS.map(p => ({ label: p.label, value: p.value }))}
            />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入或选择模型名称' }]}
          >
            {selectedProvider === 'custom' ? (
              <Input placeholder="请输入模型名称" />
            ) : (
              <Select
                placeholder="选择模型"
                options={(MODEL_OPTIONS[selectedProvider] || []).map(m => ({ label: m, value: m }))}
              />
            )}
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={[{ required: !editingModel, message: '请输入 API Key' }]}
            extra={editingModel ? '留空则不修改当前 API Key' : ''}
          >
            <Input.Password placeholder="请输入 API Key" />
          </Form.Item>

          <Form.Item
            name="api_base_url"
            label="API Base URL"
            extra={MODEL_PROVIDERS.find(p => p.value === selectedProvider)?.baseUrl}
          >
            <Input placeholder="留空使用默认值" />
          </Form.Item>

          <Divider>模型参数</Divider>

          <Form.Item
            name="temperature"
            label="Temperature (0-1)"
            initialValue={0.7}
          >
            <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="max_tokens"
            label="Max Tokens"
            initialValue={2048}
          >
            <InputNumber min={100} max={32000} step={100} style={{ width: '100%' }} />
          </Form.Item>

          {editingModel && (
            <Form.Item
              name="is_active"
              label="启用状态"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch checkedChildren="启用" unCheckedChildren="禁用" />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default ModelConfigPage
