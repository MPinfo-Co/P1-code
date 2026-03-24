// src/contexts/AuthContext.jsx
import { createContext, useContext, useState } from 'react'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const stored = localStorage.getItem('mp-box-user')
    return stored ? JSON.parse(stored) : null
  })

  const navigate = useNavigate()

  function login(username, role) {
    const userData = { username, role }
    localStorage.setItem('mp-box-user', JSON.stringify(userData))
    setUser(userData)
    navigate('/')
  }

  function logout() {
    localStorage.removeItem('mp-box-user')
    setUser(null)
    navigate('/login')
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
