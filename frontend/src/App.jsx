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
import FnToolList from './pages/fn_ai_partner_tool/FnToolList'
import FnExpertSetting from './pages/fn_expert_setting/FnExpertSetting'
import FnAiPartnerConfigList from './pages/fn_ai_partner_config/FnAiPartnerConfigList'
import FnAiPartnerChatPage from './pages/fn_ai_partner_chat/FnAiPartnerChatPage'
import FnFeedbackSubmit from './pages/fn_feedback/FnFeedbackSubmit'
import FnFeedbackList from './pages/fn_feedback/FnFeedbackList'
import FnCustomTableList from './pages/fn_custom_table/FnCustomTableList'
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
          path="expert"
          element={
            <PermissionGuard fnKey="fn_expert">
              <IssueList />
            </PermissionGuard>
          }
        />
        <Route
          path="expert/issues/:issueId"
          element={
            <PermissionGuard fnKey="fn_expert">
              <IssueDetail />
            </PermissionGuard>
          }
        />
        <Route
          path="user"
          element={
            <PermissionGuard fnKey="fn_user">
              <FnUserList />
            </PermissionGuard>
          }
        />
        <Route
          path="role"
          element={
            <PermissionGuard fnKey="fn_role">
              <FnRoleList />
            </PermissionGuard>
          }
        />
        <Route
          path="company_data"
          element={
            <PermissionGuard fnKey="fn_company_data">
              <FnCompanyDataList />
            </PermissionGuard>
          }
        />
        <Route
          path="ai_partner_tool"
          element={
            <PermissionGuard fnKey="fn_ai_partner_tool">
              <FnToolList />
            </PermissionGuard>
          }
        />
        <Route
          path="expert_setting"
          element={
            <PermissionGuard fnKey="fn_expert_setting">
              <FnExpertSetting />
            </PermissionGuard>
          }
        />
        <Route
          path="ai_partner_config"
          element={
            <PermissionGuard fnKey="fn_ai_partner_config">
              <FnAiPartnerConfigList />
            </PermissionGuard>
          }
        />
        <Route
          path="ai_partner_chat"
          element={
            <PermissionGuard fnKey="fn_ai_partner_chat">
              <FnAiPartnerChatPage />
            </PermissionGuard>
          }
        />
        <Route
          path="feedback"
          element={
            <PermissionGuard fnKey="fn_feedback">
              <FnFeedbackSubmit />
            </PermissionGuard>
          }
        />
        <Route
          path="feedback/list"
          element={
            <PermissionGuard fnKey="fn_feedback">
              <FnFeedbackList />
            </PermissionGuard>
          }
        />
        <Route
          path="custom_table"
          element={
            <PermissionGuard fnKey="fn_custom_table">
              <FnCustomTableList />
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
