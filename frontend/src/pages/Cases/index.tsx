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
  Select,
  message,
  Typography,
  Drawer,
  Descriptions,
  Divider,
  Dropdown,
  Row,
  Col
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  HistoryOutlined,
  DownloadOutlined,
  MoreOutlined,
  FilterOutlined,
  CodeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons'
import { useSearchParams } from 'react-router-dom'
import { caseApi, systemApi, moduleApi } from '../../api/services'
import type { TestCase, System, Module, CaseData } from '../../types'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { TextArea } = Input

interface VersionData {
  id: number
  version: number
  case_data: CaseData
  created_at: string
  change_summary?: string
}

const Cases: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [cases, setCases] = useState<TestCase[]>([])
  const [systems, setSystems] = useState<System[]>([])
  const [modules, setModules] = useState<Module[]>([])
  const [loading, setLoading] = useState(true)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 10, total: 0 })
  const [filters, setFilters] = useState({
    system_id: searchParams.get('system_id') ? Number(searchParams.get('system_id')) : undefined,
    module_id: searchParams.get('module_id') ? Number(searchParams.get('module_id')) : undefined,
    status: searchParams.get('status') || undefined,
    keyword: '',
  })
  const [modalVisible, setModalVisible] = useState(false)
  const [editingCase, setEditingCase] = useState<TestCase | null>(null)
  const [viewDrawer, setViewDrawer] = useState(false)
  const [selectedCase, setSelectedCase] = useState<TestCase | null>(null)
  const [versionDrawer, setVersionDrawer] = useState(false)
  const [versions, setVersions] = useState<any[]>([])
  const [filterVisible, setFilterVisible] = useState(false)
  const [scriptModalVisible, setScriptModalVisible] = useState(false)
  const [generatedScript, setGeneratedScript] = useState('')
  const [generatingScript, setGeneratingScript] = useState(false)
  const [scriptFramework, setScriptFramework] = useState('pytest')
  const [form] = Form.useForm()

  useEffect(() => {
    fetchSystems()
  }, [])

  useEffect(() => {
    if (filters.system_id) {
      fetchModules(filters.system_id)
    }
  }, [filters.system_id])

  useEffect(() => {
    fetchCases()
  }, [pagination.current, pagination.pageSize, filters])

  const fetchSystems = async () => {
    try {
      const res = await systemApi.getSystems({ page_size: 100 })
      setSystems(res.data || [])
    } catch (error) {
      console.error(error)
    }
  }

  const fetchModules = async (systemId: number) => {
    try {
      const res = await moduleApi.getModules(systemId)
      setModules(res.data || [])
    } catch (error) {
      console.error(error)
    }
  }

  const fetchCases = async () => {
    setLoading(true)
    try {
      const res = await caseApi.getCases({
        page: pagination.current,
        page_size: pagination.pageSize,
        system_id: filters.system_id,
        module_id: filters.module_id,
        status: filters.status,
        keyword: filters.keyword,
      })
      setCases(res.data.items || [])
      setPagination({ ...pagination, total: res.data.total || 0 })
    } catch (error) {
      message.error('获取用例列表失败')
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    setEditingCase(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: TestCase) => {
    setEditingCase(record)
    form.setFieldsValue({
      module_id: record.module_id,
      case_data: JSON.stringify(record.case_data, null, 2),
      status: record.status,
    })
    setModalVisible(true)
  }

  const handleView = (record: TestCase) => {
    setSelectedCase(record)
    setViewDrawer(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await caseApi.deleteCase(id)
      message.success('删除成功')
      fetchCases()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleSubmit = async (values: { 
    module_id?: number; 
    case_data: string;
    status?: string;
  }) => {
    try {
      let caseData
      try {
        caseData = JSON.parse(values.case_data)
      } catch {
        message.error('用例数据必须是有效的 JSON 格式')
        return
      }

      if (editingCase) {
        await caseApi.updateCase(editingCase.id, {
          module_id: values.module_id,
          case_data: caseData,
          status: values.status,
        })
        message.success('更新成功')
      } else {
        if (!filters.system_id) {
          message.error('请先选择测试系统')
          return
        }
        await caseApi.createCase({
          system_id: filters.system_id,
          module_id: values.module_id,
          case_data: caseData,
        })
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchCases()
    } catch (error) {
      message.error(editingCase ? '更新失败' : '创建失败')
    }
  }

  const handleViewVersions = async (record: TestCase) => {
    try {
      const res = await caseApi.getCaseVersions(record.id)
      setVersions(res.data)
      setSelectedCase(record)
      setVersionDrawer(true)
    } catch (error) {
      message.error('获取版本历史失败')
    }
  }

  const handleExport = async () => {
    try {
      const res = await caseApi.exportCases({
        system_id: filters.system_id,
        module_id: filters.module_id,
        status: filters.status,
      })
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `测试用例_${dayjs().format('YYYYMMDD')}.xlsx`
      link.click()
      window.URL.revokeObjectURL(url)
      message.success('导出成功')
    } catch (error) {
      message.error('导出失败')
    }
  }

  const handleReview = async (record: TestCase, status: 'approved' | 'rejected') => {
    try {
      await caseApi.updateCase(record.id, { review_status: status })
      message.success(status === 'approved' ? '已审核通过' : '已拒绝')
      fetchCases()
    } catch (error) {
      message.error('更新审核状态失败')
    }
  }

  const handleGenerateScript = async (record: TestCase) => {
    setSelectedCase(record)
    setGeneratedScript('')
    setScriptModalVisible(true)
    setGeneratingScript(true)
    try {
      const res = await caseApi.generateScript(record.id, { framework: scriptFramework })
      setGeneratedScript(res.data.script)
    } catch (error: any) {
      message.error(error?.response?.data?.detail || '生成脚本失败')
      setScriptModalVisible(false)
    } finally {
      setGeneratingScript(false)
    }
  }

  const handleFrameworkChange = async (val: string) => {
    setScriptFramework(val)
    if (selectedCase) {
      setGeneratingScript(true)
      setGeneratedScript('')
      try {
        const res = await caseApi.generateScript(selectedCase.id, { framework: val })
        setGeneratedScript(res.data.script)
      } catch (error: any) {
        message.error(error?.response?.data?.detail || '重新生成失败')
      } finally {
        setGeneratingScript(false)
      }
    }
  }

  const columns = [
    {
      title: '用例标题',
      dataIndex: ['case_data', 'title'],
      key: 'title',
      width: 250,
      ellipsis: true,
      render: (_: unknown, record: TestCase) => record.case_data?.title || '-',
    },
    {
      title: '所属系统',
      dataIndex: 'system_id',
      key: 'system',
      width: 120,
      render: (id: number) => systems.find(s => s.id === id)?.name || '-',
    },
    {
      title: '所属模块',
      dataIndex: 'module_id',
      key: 'module',
      width: 120,
      render: (id: number) => modules.find(m => m.id === id)?.name || '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 90,
      render: (status: string) => {
        const map: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          pending: { color: 'processing', text: '待审核' },
          approved: { color: 'success', text: '已通过' },
          rejected: { color: 'error', text: '已拒绝' },
        }
        const config = map[status] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '审核',
      dataIndex: 'review_status',
      key: 'review_status',
      width: 90,
      render: (status: string) => {
        const map: Record<string, { color: string; text: string }> = {
          pending: { color: 'orange', text: '待审核' },
          approved: { color: 'green', text: '已通过' },
          rejected: { color: 'red', text: '已拒绝' },
        }
        const config = map[status] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 60,
      render: (v: number) => <Tag>v{v}</Tag>,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 160,
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      width: 180,
      render: (_: unknown, record: TestCase) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleView(record)}>
            查看
          </Button>
          <Button type="link" size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Dropdown
            menu={{
              items: [
                { key: 'script', icon: <CodeOutlined />, label: '生成自动化脚本', onClick: () => handleGenerateScript(record) },
                { type: 'divider' },
                { key: 'approve', icon: <CheckCircleOutlined style={{color: 'green'}} />, label: '审核通过', onClick: () => handleReview(record, 'approved'), disabled: record.review_status === 'approved' },
                { key: 'reject', icon: <CloseCircleOutlined style={{color: 'red'}} />, label: '审核拒绝', onClick: () => handleReview(record, 'rejected'), disabled: record.review_status === 'rejected' },
                { type: 'divider' },
                { key: 'versions', icon: <HistoryOutlined />, label: '版本历史', onClick: () => handleViewVersions(record) },
                { key: 'delete', icon: <DeleteOutlined />, label: '删除', danger: true, onClick: () => handleDelete(record.id) },
              ]
            }}
          >
            <Button type="link" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      ),
    },
  ]

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>用例管理</Title>
        <Space>
          <Button icon={<FilterOutlined />} onClick={() => setFilterVisible(!filterVisible)}>
            筛选
          </Button>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出
          </Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建用例
          </Button>
        </Space>
      </div>

      {filterVisible && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={4}>
              <Select
                placeholder="选择系统"
                style={{ width: '100%' }}
                allowClear
                value={filters.system_id}
                onChange={(v) => setFilters({ ...filters, system_id: v, module_id: undefined })}
                options={systems.map(s => ({ label: s.name, value: s.id }))}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="选择模块"
                style={{ width: '100%' }}
                allowClear
                value={filters.module_id}
                onChange={(v) => setFilters({ ...filters, module_id: v })}
                options={modules.map(m => ({ label: m.name, value: m.id }))}
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="用例状态"
                style={{ width: '100%' }}
                allowClear
                value={filters.status}
                onChange={(v) => setFilters({ ...filters, status: v })}
                options={[
                  { label: '草稿', value: 'draft' },
                  { label: '待审核', value: 'pending' },
                  { label: '已通过', value: 'approved' },
                  { label: '已拒绝', value: 'rejected' },
                ]}
              />
            </Col>
            <Col span={6}>
              <Input
                placeholder="搜索标题"
                value={filters.keyword}
                onChange={(e) => setFilters({ ...filters, keyword: e.target.value })}
                onPressEnter={() => fetchCases()}
              />
            </Col>
            <Col span={6}>
              <Space>
                <Button type="primary" onClick={() => fetchCases()}>查询</Button>
                <Button onClick={() => setFilters({ system_id: undefined, module_id: undefined, status: undefined, keyword: '' })}>重置</Button>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={cases}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            onChange: (page, pageSize) => setPagination({ ...pagination, current: page, pageSize }),
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      {/* 新建/编辑弹窗 */}
      <Modal
        title={editingCase ? '编辑用例' : '新建用例'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="module_id"
            label="所属模块"
          >
            <Select
              placeholder="选择模块"
              allowClear
              options={modules.map(m => ({ label: m.name, value: m.id }))}
            />
          </Form.Item>
          <Form.Item
            name="case_data"
            label="用例数据 (JSON)"
            rules={[{ required: true, message: '请输入用例数据' }]}
          >
            <TextArea rows={12} placeholder='{"title": "用例标题", "precondition": "...", "steps": [], "expected": "..."}' />
          </Form.Item>
          {editingCase && (
            <Form.Item name="status" label="状态">
              <Select
                options={[
                  { label: '草稿', value: 'draft' },
                  { label: '待审核', value: 'pending' },
                  { label: '已通过', value: 'approved' },
                  { label: '已拒绝', value: 'rejected' },
                ]}
              />
            </Form.Item>
          )}
        </Form>
      </Modal>

      {/* 查看详情抽屉 */}
      <Drawer
        title="用例详情"
        width={600}
        open={viewDrawer}
        onClose={() => setViewDrawer(false)}
      >
        {selectedCase && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="用例标题">{selectedCase.case_data?.title || '-'}</Descriptions.Item>
            <Descriptions.Item label="前置条件">{selectedCase.case_data?.precondition || '-'}</Descriptions.Item>
            <Descriptions.Item label="测试步骤">{selectedCase.case_data?.steps?.join('\n') || '-'}</Descriptions.Item>
            <Descriptions.Item label="预期结果">{selectedCase.case_data?.expected || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={selectedCase.status === 'approved' ? 'green' : 'orange'}>
                {selectedCase.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="版本">v{selectedCase.version}</Descriptions.Item>
            <Descriptions.Item label="创建时间">{dayjs(selectedCase.created_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
            <Descriptions.Item label="更新时间">{dayjs(selectedCase.updated_at).format('YYYY-MM-DD HH:mm:ss')}</Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>

      {/* 版本历史抽屉 */}
      <Drawer
        title={`版本历史 - ${selectedCase?.case_data?.title}`}
        width={600}
        open={versionDrawer}
        onClose={() => setVersionDrawer(false)}
      >
        {versions.map((v: VersionData) => (
          <Card key={v.id} size="small" style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Text strong>v{v.version}</Text>
              <Text type="secondary">{dayjs(v.created_at).format('YYYY-MM-DD HH:mm')}</Text>
            </div>
            <Divider style={{ margin: '8px 0' }} />
            <Text>{v.change_summary || '无变更说明'}</Text>
          </Card>
        ))}
      </Drawer>
      {/* 生成脚本弹窗 */}
      <Modal
        title={`生成自动化脚本 - ${selectedCase?.case_data?.title || ''}`}
        open={scriptModalVisible}
        onCancel={() => {
          setScriptModalVisible(false)
          setSelectedCase(null)
        }}
        footer={null}
        width={800}
      >
        <div style={{ marginBottom: 16 }}>
          <Space>
            <Text>目标框架:</Text>
            <Select
              value={scriptFramework}
              onChange={handleFrameworkChange}
              style={{ width: 150 }}
              options={[
                { label: 'Pytest (Python)', value: 'pytest' },
                { label: 'Playwright (TS)', value: 'playwright-ts' },
                { label: 'Playwright (Python)', value: 'playwright-python' },
                { label: 'Cypress (JS/TS)', value: 'cypress' },
                { label: 'Jest (JS)', value: 'jest' },
              ]}
              disabled={generatingScript}
            />
          </Space>
        </div>
        
        <Card
          size="small"
          loading={generatingScript}
          style={{
            backgroundColor: '#1e1e1e',
            borderColor: '#333',
            height: '400px',
            overflowY: 'auto'
          }}
        >
          {!generatingScript && (
            <pre style={{ margin: 0, color: '#d4d4d4', fontFamily: 'Menlo, Monaco, "Courier New", monospace', whiteSpace: 'pre-wrap' }}>
              {generatedScript || '暂无脚本内容...'}
            </pre>
          )}
        </Card>
        
        <div style={{ marginTop: 16, textAlign: 'right' }}>
          <Space>
            <Button
              icon={<CodeOutlined />}
              onClick={() => {
                if (generatedScript) {
                  navigator.clipboard.writeText(generatedScript)
                  message.success('代码已复制到剪贴板')
                }
              }}
              disabled={!generatedScript || generatingScript}
            >
              复制脚本
            </Button>
            <Button
              type="primary"
              onClick={() => {
                setScriptModalVisible(false)
                setSelectedCase(null)
              }}
            >
              关闭
            </Button>
          </Space>
        </div>
      </Modal>
    </div>
  )
}

export default Cases
