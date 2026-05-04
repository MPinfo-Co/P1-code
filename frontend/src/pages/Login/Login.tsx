import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/stores/authStore'
import { Box, Paper, Typography, TextField, Button, Alert } from '@mui/material'
import './Login.css'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : '登入失敗')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box className="login-root">
      <Paper elevation={24} className="login-paper">
        <Typography variant="h3" fontWeight={900} color="text.primary" mb={4}>
          MP-Box
        </Typography>
        <Box component="form" onSubmit={handleSubmit} className="login-form">
          <TextField
            label="Email"
            type="email"
            placeholder="輸入 Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            fullWidth
            required
          />
          <TextField
            label="密碼"
            type="password"
            placeholder="密碼"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            fullWidth
            required
          />
          {error && <Alert severity="error">{error}</Alert>}
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            size="large"
            disabled={loading}
          >
            {loading ? '登入中...' : '登入系統'}
          </Button>
        </Box>
      </Paper>
    </Box>
  )
}
