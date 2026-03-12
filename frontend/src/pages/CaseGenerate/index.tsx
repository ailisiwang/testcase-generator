import React, { useEffect, useState, useRef } from 'react'
import { 
  Card, 
  Row, 
  Col, 
  Select, 
  Button, 
  Space, 
  Input, 
  Upload, 
  message, 
  Typography,
  Divider,
  Spin,
  Tabs,
  Alert,
  Tag
} from 'antd'
import { 
  SendOutlined, 
  UploadOutlined, 
  FileTextOutlined,
  DeleteOutlined,
  SaveOutlined,
  CopyOutlined,
  ClearOutlined
} from '@ant-design/icons'
import { useParams, useNavigate } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { systemApi, moduleApi, modelApi, generateApi, caseApi } from '../../api/services'

const { Title, Text, Paragraph } = Typography
const { TextArea } = Input

interface System {
  id: number
  name: string
}

interface Module {
  id: number
  name: string
}

interface ModelConfig {
  id: number
  provider: string
  model_name: string
  is_active: boolean
}

const CaseGenerate: React.FC = () => {
  const { systemId } = useParams<{ systemId: string }>()
  const navigate = useNavigate()
  
  const [systems, setSystems] = useState<System[]>([])
  const [modules, setModules] = useState<Module[]>([])
  const [models, setModels] = useState<ModelConfig[]>([])
  const [selectedSystem, setSelectedSystem] = useState<number | undefined>(Number(systemId))
  const [selectedModule, setSelectedModule] = useState<number | undefined>()
  const [selectedModel, setSelectedModel] = useState<number | undefined>()
  const [requirement, setRequirement] = useState('')
  const [generatedContent, setGeneratedContent] = useState('')
  const [isGenerating, setIsGenerating] = useState(false)
  const [activeTab, setActiveTab] = useState('text')
  const [fileList, setFileList] = useState<any[]>([])
  const [generatedCases, setGeneratedCases] = useState<any[]>([])
  
  const outputRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetchSystems()
    fetchModels()
  }, [])

  useEffect(() => {
    if (selectedSystem) {
      fetchModules(selectedSystem)
    }
  }, [selectedSystem])

  const fetchSystems = async () => {
    try {
      const res = await systemApi.getSystems({ page_size: 100 })
      setSystems(res.data.items || [])
      if (!selectedSystem && res.data.items?.length > 0) {
        setSelectedSystem(res.data.items[0].id)
      }
    } catch (error) {
      message.error('获取系统列表失败')
    }
  }

  const fetchModules = async (systemId: number) => {
    try {
      const res = await moduleApi.getModules(systemId)
      const flatModules = flattenModules(res.data.items || [])
      setModules(flatModules)
    } catch (error) {
      console.error(error)
    }
  }

  const flattenModules = (items: any[], prefix = ''): Module[] => {
    let result: Module[] = []
    items.forEach(item => {
      result.push({
        id: item.id,
        name: prefix + item.name,
      })
      if (item.children) {
        result = result.concat(flattenModules(item.children, prefix + '  '))
      }
    })
    return result
  }

  const fetchModels = async () => {
    try {
      const res = await modelApi.getModels({ page_size: 100 })
      setModels(res.data.items || [])
      if (res.data.items?.length > 0) {
        const activeModel = res.data.items.find((m: ModelConfig) => m.is_active)
        if (activeModel) {
          setSelectedModel(activeModel.id)
        }
      }
    } catch (error) {
      console.error(error)
    }
  }

  // 文本生成
  const handleGenerate = async () => {
    if (!selectedSystem) {
      message.warning('请选择测试系统')
      return
    }
    if (!requirement.trim()) {
      message.warning('请输入需求描述')
      return
    }

    setIsGenerating(true)
    setGeneratedContent('')
    setGeneratedCases([])

    try {
      const res = await generateApi.generateFromText({
        system_id: selectedSystem,
        module_id: selectedModule,
        requirement: requirement,
        model_config_id: selectedModel,
      })

      const taskId = res.data.task_id
      
      // 使用 SSE 流式读取
      const eventSource = new EventSource(`/api/cases/generate/stream/${taskId}`)
      
      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.content) {
            setGeneratedContent(prev => prev + data.content)
          }
          if (data.done) {
            eventSource.close()
            setIsGenerating(false)
            
            // 尝试解析生成的用例
            try {
              const parsed = parseGeneratedContent(data.full_content || generatedContent)
              setGeneratedCases(parsed)
            } catch (e) {
              console.error('解析用例失败', e)
            }
          }
        } catch (e) {
          console.error('解析流式数据失败', e)
        }
      }

      eventSource.onerror = () => {
        eventSource.close()
        setIsGenerating(false)
        message.error('生成中断')
      }

    } catch (error: any) {
      setIsGenerating(false)
      message.error(error.response?.data?.detail || '生成失败')
    }
  }

  // 文件上传生成
  const handleFileGenerate = async () => {
    if (!selectedSystem) {
      message.warning('请选择测试系统')
      return
    }
    if (fileList.length === 0) {
      message.warning('请上传文件')
      return
    }

    setIsGenerating(true)
    setGeneratedContent('')

    try {
      const formData = new FormData()
      formData.append('system_id', String(selectedSystem))
      if (selectedModule) {
        formData.append('module_id', String(selectedModule))
      }
      if (selectedModel) {
        formData.append('model_config_id', String(selectedModel))
      }
      formData.append('file', fileList[0].originFileObj)

      const res = await generateApi.generateFromFile(formData)
      
      // 文件上传后可能返回完整内容或 task_id
      if (res.data.task_id) {
        const taskId = res.data.task_id
        const eventSource = new EventSource(`/api/cases/generate/stream/${taskId}`)
        
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.content) {
              setGeneratedContent(prev => prev + data.content)
            }
            if (data.done) {
              eventSource.close()
              setIsGenerating(false)
            }
          } catch (e) {
            console.error(e)
          }
        }
      } else if (res.data.content) {
        setGeneratedContent(res.data.content)
        setIsGenerating(false)
      }
    } catch (error: any) {
      setIsGenerating(false)
      message.error(error.response?.data?.detail || '文件处理失败')
    }
  }

  // 解析生成的内容为用例
  const parseGeneratedContent = (content: string): any[] => {
    try {
      // 尝试找到 JSON 数组
      const jsonMatch = content.match(/\[[\s\S]*\]/g)
      if (jsonMatch) {
        return JSON.parse(jsonMatch[0])
      }
      return []
    } catch {
      return []
    }
  }

  // 保存生成的用例
  const handleSaveCases = async () => {
    if (!selectedSystem) {
      message.warning('请选择测试系统')
      return
    }

    if (generatedCases.length === 0 && !generatedContent) {
      message.warning('没有可保存的用例')
      return
    }

    try {
      // 如果有解析出的用例
      if (generatedCases.length > 0) {
        for (const caseData of generatedCases) {
          await caseApi.createCase({
            system_id: selectedSystem,
            module_id: selectedModule,
            case_data: caseData,
          })
        }
        message.success(`成功保存 ${generatedCases.length} 条用例`)
      } else {
        // 保存原始内容
        await caseApi.createCase({
          system_id: selectedSystem,
          module_id: selectedModule,
          case_data: {
            title: 'AI 生成用例',
            content: generatedContent,
            generated_at: new Date().toISOString(),
          },
        })
        message.success('用例保存成功')
      }
      
      navigate('/cases')
    } catch (error) {
      message.error('保存失败')
    }
  }

  const handleCopy = () => {
    if (generatedContent) {
      navigator.clipboard.writeText(generatedContent)
      message.success('已复制到剪贴板')
    }
  }

  const handleClear = () => {
    setGeneratedContent('')
    setGeneratedCases([])
    setRequirement('')
  }

  return (
    <div>
      <Title level={2} style={{ marginBottom: 24 }}>用例生成</Title>

      <Row gutter={24}>
        <Col xs={24} lg={10}>
          <Card title="生成配置" size="small">
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <div>
                <Text strong>测试系统 *</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="选择测试系统"
                  value={selectedSystem}
                  onChange={(v) => {
                    setSelectedSystem(v)
                    setSelectedModule(undefined)
                  }}
                  options={systems.map(s => ({ label: s.name, value: s.id }))}
                />
              </div>

              <div>
                <Text>所属模块</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="选择模块（可选）"
                  allowClear
                  value={selectedModule}
                  onChange={setSelectedModule}
                  options={modules.map(m => ({ label: m.name, value: m.id }))}
                />
              </div>

              <div>
                <Text>大模型</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="选择模型（可选）"
                  allowClear
                  value={selectedModel}
                  onChange={setSelectedModel}
                  options={models.map(m => ({ 
                    label: `${m.provider}/${m.model_name}`, 
                    value: m.id 
                  }))}
                />
                {models.length === 0 && (
                  <Alert 
                    message="未配置模型，请先到模型配置页面添加" 
                    type="warning" 
                    style={{ marginTop: 8 }}
                    showIcon
                  />
                )}
              </div>

              <Divider />

              <Tabs 
                activeKey={activeTab} 
                onChange={setActiveTab}
                items={[
                  {
                    key: 'text',
                    label: '文本输入',
                    children: (
                      <div>
                        <TextArea
                          rows={8}
                          placeholder="请输入需求描述，例如：用户登录功能，需要验证用户名密码正确、错误、空值等情况"
                          value={requirement}
                          onChange={(e) => setRequirement(e.target.value)}
                          disabled={isGenerating}
                        />
                        <Button
                          type="primary"
                          icon={<SendOutlined />}
                          onClick={handleGenerate}
                          loading={isGenerating}
                          disabled={!requirement.trim() || !selectedSystem}
                          style={{ marginTop: 16 }}
                          block
                        >
                          {isGenerating ? '生成中...' : '生成用例'}
                        </Button>
                      </div>
                    )
                  },
                  {
                    key: 'file',
                    label: '文件上传',
                    children: (
                      <div>
                        <Upload
                          accept=".txt,.doc,.docx,.pdf,.md"
                          fileList={fileList}
                          onChange={({ fileList }) => setFileList(fileList)}
                          beforeUpload={() => false}
                          maxCount={1}
                        >
                          <Button icon={<UploadOutlined />}>点击上传需求文档</Button>
                        </Upload>
                        <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
                          支持 .txt, .doc, .docx, .pdf, .md 格式
                        </Text>
                        <Button
                          type="primary"
                          icon={<SendOutlined />}
                          onClick={handleFileGenerate}
                          loading={isGenerating}
                          disabled={fileList.length === 0 || !selectedSystem}
                          style={{ marginTop: 16 }}
                          block
                        >
                          {isGenerating ? '处理中...' : '从文件生成'}
                        </Button>
                      </div>
                    )
                  }
                ]}
              />
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={14}>
          <Card 
            title={
              <Space>
                <FileTextOutlined />
                <span>生成结果</span>
                {generatedCases.length > 0 && (
                  <Tag color="blue">{generatedCases.length} 条用例</Tag>
                )}
              </Space>
            }
            extra={
              <Space>
                <Button 
                  icon={<CopyOutlined />} 
                  onClick={handleCopy}
                  disabled={!generatedContent}
                  size="small"
                >
                  复制
                </Button>
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={handleClear}
                  disabled={!generatedContent && generatedCases.length === 0}
                  size="small"
                >
                  清空
                </Button>
                <Button 
                  type="primary"
                  icon={<SaveOutlined />} 
                  onClick={handleSaveCases}
                  disabled={(!generatedContent && generatedCases.length === 0) || !selectedSystem}
                >
                  保存用例
                </Button>
              </Space>
            }
            style={{ minHeight: 400 }}
          >
            {isGenerating && (
              <div style={{ textAlign: 'center', padding: 40 }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text>AI 正在生成测试用例，请稍候...</Text>
                </div>
              </div>
            )}

            {!isGenerating && !generatedContent && (
              <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
                <FileTextOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <div>输入需求描述或上传文件，点击生成按钮</div>
              </div>
            )}

            {generatedContent && (
              <div 
                ref={outputRef}
                className="stream-output"
                style={{ whiteSpace: 'pre-wrap' }}
              >
                <ReactMarkdown>{generatedContent}</ReactMarkdown>
              </div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default CaseGenerate
