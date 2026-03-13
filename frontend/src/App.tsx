import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { ConfigProvider, App as AntdApp } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { useAuthStore } from './stores/authStore'
import ErrorBoundary from './components/ErrorBoundary'
import MainLayout from './components/Layout/MainLayout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Systems from './pages/Systems'
import Modules from './pages/Modules'
import Cases from './pages/Cases'
import CaseGenerate from './pages/CaseGenerate'
import ModelConfig from './pages/ModelConfig'

// 路由守卫组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

// 公开路由组件
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }
  
  return <>{children}</>
}

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ConfigProvider locale={zhCN}>
        <AntdApp>
          <BrowserRouter>
            <Routes>
        {/* 公开路由 */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />
        
        {/* 受保护路由 */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="systems" element={<Systems />} />
          <Route path="systems/:systemId/modules" element={<Modules />} />
          <Route path="cases" element={<Cases />} />
          <Route path="cases/generate" element={<CaseGenerate />} />
          <Route path="cases/generate/:systemId" element={<CaseGenerate />} />
          <Route path="models" element={<ModelConfig />} />
        </Route>
        
        {/* 404 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
    </AntdApp>
  </ConfigProvider>
</ErrorBoundary>
  )
}

export default App
