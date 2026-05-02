// src/App.jsx
import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './stores/authStore'
import useAuthStore from './stores/authStore'
import { IssuesProvider } from './contexts/IssuesContext'
import Layout from './components/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import AiPartner from './pages/AiPartner/AiPartner'
import IssueList from './pages/AiPartner/IssueList'
import IssueDetail from './pages/AiPartner/IssueDetail'
import KnowledgeBase from './pages/KnowledgeBase/KnowledgeBase'
import FnUserList from './pages/fn_user/FnUserList'
import FnRoleList from './pages/fn_role/FnRoleList'
import AiConfig from './pages/Settings/AiConfig'
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
          path="fn_partner"
          element={
            <PermissionGuard fnKey="fn_partner">
              <AiPartner />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_partner/:partnerId/issues"
          element={
            <PermissionGuard fnKey="fn_partner">
              <IssueList />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_partner/:partnerId/issues/:issueId"
          element={
            <PermissionGuard fnKey="fn_partner">
              <IssueDetail />
            </PermissionGuard>
          }
        />
        <Route
          path="fn_km"
          element={
            <PermissionGuard fnKey="fn_km">
              <KnowledgeBase />
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
          path="fn_ai_config"
          element={
            <PermissionGuard fnKey="fn_ai_config">
              <AiConfig />
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
