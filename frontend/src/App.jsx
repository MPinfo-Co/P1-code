// src/App.jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './stores/authStore'
import { IssuesProvider } from './contexts/IssuesContext'
import Layout from './components/Layout/Layout'
import Login from './pages/Login/Login'
import Home from './pages/Home/Home'
import AiPartner from './pages/AiPartner/AiPartner'
import IssueList from './pages/AiPartner/IssueList'
import IssueDetail from './pages/AiPartner/IssueDetail'
import KnowledgeBase from './pages/KnowledgeBase/KnowledgeBase'
import Account from './pages/Settings/Account'
import Role from './pages/Settings/Role'
import AiConfig from './pages/Settings/AiConfig'
import NotFound from './pages/NotFound'

function ProtectedRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

function AppRoutes() {
  const { user } = useAuth()

  return (
    <Routes>
      <Route
        path="/login"
        element={user ? <Navigate to="/" replace /> : <Login />}
      />
      <Route
        path="/"
        element={<ProtectedRoute><Layout /></ProtectedRoute>}
      >
        <Route index element={<Home />} />
        <Route path="ai-partner" element={<AiPartner />} />
        <Route path="ai-partner/:partnerId/issues" element={<IssueList />} />
        <Route path="ai-partner/:partnerId/issues/:issueId" element={<IssueDetail />} />
        <Route path="kb" element={<KnowledgeBase />} />
        <Route path="settings" element={<Navigate to="/settings/account" replace />} />
        <Route path="settings/account" element={<Account />} />
        <Route path="settings/role" element={<Role />} />
        <Route path="settings/ai-config" element={<AiConfig />} />
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
