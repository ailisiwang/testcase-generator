import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Tag, Space, Typography } from 'antd'
import {
  AppstoreOutlined,
  FileTextOutlined,
  RocketOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { systemApi, caseApi } from '../../api/services'

const { Title, Text } = Typography

interface DashboardStats {
  systemCount: number
  caseCount: number
  pendingReview: number
  approved: number
}

const Dashboard: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState<DashboardStats>({
    systemCount: 0,
    caseCount: 0,
    pendingReview: 0,
    approved: 0,
  })
  const [recentCases, setRecentCases] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [systemsRes, casesRes] = await Promise.all([
        systemApi.getSystems({ page_size: 100 }),
        caseApi.getCases({ page_size: 10 }),
      ])

      const cases = casesRes.data.items || []
      const pendingReview = cases.filter((c: any) => c.review_status === 'pending').length
      const approved = cases.filter((c: any) => c.review_status === 'approved').length

      setStats({
        systemCount: systemsRes.data.total || 0,
        caseCount: casesRes.data.total || 0,
        pendingReview,
        approved,
      })
      setRecentCases(cases)
    } catch (error) {
      console.error('获取数据失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const columns = [
    {
      title: '用例名称',
      dataIndex: ['case_data', 'title'],
      key: 'title',
      ellipsis: true,
      render: (_: any, record: any) => record.case_data?.title || `-`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          draft: { color: 'default', text: '草稿' },
          pending: { color: 'processing', text: '待审核' },
          approved: { color: 'success', text: '已通过' },
          rejected: { color: 'error', text: '已拒绝' },
        }
        const config = statusMap[status] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '审核状态',
      dataIndex: 'review_status',
      key: 'review_status',
      render: (status: string) => {
        const statusMap: Record<string, { color: string; text: string }> = {
          pending: { color: 'orange', text: '待审核' },
          approved: { color: 'green', text: '已通过' },
          rejected: { color: 'red', text: '已拒绝' },
        }
        const config = statusMap[status] || { color: 'default', text: status }
        return <Tag color={config.color}>{config.text}</Tag>
      },
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      render: (v: number) => <Tag>v{v}</Tag>,
    },
    {
      title: '更新时间',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => new Date(date).toLocaleString('zh-CN'),
    },
  ]

  const statCards = [
    {
      title: '测试系统',
      value: stats.systemCount,
      icon: <AppstoreOutlined style={{ fontSize: 40, color: '#1890ff' }} />,
      color: '#e6f7ff',
      onClick: () => navigate('/systems'),
    },
    {
      title: '测试用例',
      value: stats.caseCount,
      icon: <FileTextOutlined style={{ fontSize: 40, color: '#52c41a' }} />,
      color: '#f6ffed',
      onClick: () => navigate('/cases'),
    },
    {
      title: '待审核',
      value: stats.pendingReview,
      icon: <ClockCircleOutlined style={{ fontSize: 40, color: '#faad14' }} />,
      color: '#fffbe6',
      onClick: () => navigate('/cases?status=pending'),
    },
    {
      title: '已通过',
      value: stats.approved,
      icon: <CheckCircleOutlined style={{ fontSize: 40, color: '#13c2c2' }} />,
      color: '#e6fffb',
      onClick: () => navigate('/cases?status=approved'),
    },
  ]

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>仪表盘</Title>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statCards.map((card, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card
              hoverable
              onClick={card.onClick}
              style={{ borderRadius: 12, cursor: 'pointer' }}
              bodyStyle={{ padding: 20 }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <Text type="secondary">{card.title}</Text>
                  <Statistic
                    value={card.value}
                    valueStyle={{ fontSize: 32, fontWeight: 600 }}
                  />
                </div>
                <div style={{
                  width: 64,
                  height: 64,
                  borderRadius: '50%',
                  background: card.color,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {card.icon}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      <Card
        title="最近用例"
        extra={
          <Space>
            <RocketOutlined />
            <a onClick={() => navigate('/cases/generate')}>生成用例</a>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={recentCases}
          rowKey="id"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="快速操作" size="small">
            <Space direction="vertical" style={{ width: '100%' }}>
              <a onClick={() => navigate('/cases/generate')}>
                <RocketOutlined /> 生成新用例
              </a>
              <a onClick={() => navigate('/systems')}>
                <AppstoreOutlined /> 管理测试系统
              </a>
              <a onClick={() => navigate('/models')}>
                <FileTextOutlined /> 配置模型参数
              </a>
            </Space>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="使用帮助" size="small">
            <Text type="secondary">
              1. 先创建测试系统和模块<br />
              2. 配置大模型 API<br />
              3. 输入需求或上传文件生成用例<br />
              4. 管理、审核和导出用例
            </Text>
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
