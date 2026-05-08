// src/App.jsx
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './stores/authStore'
import useAuthStore from './stores/authStore'
import { IssuesProvider } from './contexts/IssuesContext'
import Layout from './components/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import IssueList from './pages/fn_expert/IssueList'
import IssueDetail from './pages/fn_expert/IssueDetail'
import FnUserList from './pages/fn_user/FnUserList'
import FnRoleList from './pages/fn_role/FnRoleList'
import FnCompanyDataList from './pages/fn_company_data/FnCompanyDataList'
import FnToolList from './pages/fn_tool/FnToolList'
import FnExpertSetting from './pages/fn_expert_setting/FnExpertSetting'
import FnAiPartnerConfigList from './pages/fn_ai_partner_config/FnAiPartnerConfigList'
import NotFound from './pages/NotFound'
import PermissionGuard from './components/Layout/PermissionGuard'

function ProtectedRoute({ children }) {
  const { token } = useAuth()
  return token ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { token } = useAuth()

  // On page refresh, restore user profile (including functions) if token exists
  useEffect(() => {
    if (token) {
      useAuthStore.getState().fetchMe()
    }
  }, [token])

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Home />} />
        <Route
          path="fn_expert"
          element={
            <PermissionGuard fnKey="fn_expert">
              <IssueList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_expert/issues/:issueId"
          element={
            <PermissionGuard fnKey="fn_expert">
              <IssueDetail />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_user"
          element={
            <PermissionGuard fnKey="fn_user">
              <FnUserList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_role"
          element={
            <PermissionGuard fnKey="fn_role">
              <FnRoleList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_company_data"
          element={
            <PermissionGuard fnKey="fn_company_data">
              <FnCompanyDataList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_tool"
          element={
            <PermissionGuard fnKey="fn_tool">
              <FnToolList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_expert_setting"
          element={
            <PermissionGuard fnKey="fn_expert_setting">
              <FnExpertSetting />
            </PermissionGuard>
          }
        />
        <Route
          path="ai-partner-config"
          element={
            <PermissionGuard fnKey="fn_ai_partner_config">
              <FnAiPartnerConfigList />
            </PermissionGuard>
          }
        />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <IssuesProvider>
        <AppRoutes />
      </IssuesProvider>
    </BrowserRouter>
  )
}
