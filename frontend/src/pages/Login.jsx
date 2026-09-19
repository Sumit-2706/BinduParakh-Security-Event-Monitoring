import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api/client'
import RadarBadge from '../components/RadarBadge'

export default function Login() {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setNotice('')
    try {
      if (mode === 'login') {
        await login(email, password)
        navigate('/dashboard')
      } else {
        await register(email, password)
        setNotice('Analyst account created -- log in with those credentials.')
        setMode('login')
        setPassword('')
      }
    } catch (err) {
      setError(err.response?.data?.detail || (mode === 'login' ? 'Login failed' : 'Registration failed'))
    }
  }

  function toggleMode() {
    setMode(mode === 'login' ? 'register' : 'login')
    setError('')
    setNotice('')
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand-row">
          <RadarBadge size={44} />
          <span className="brand-name"><span className="bindu">बिंदु</span>Parakh</span>
        </div>
        <div className="login-subtitle">Security event monitoring console</div>
        {error && <div className="error-text">{error}</div>}
        {notice && <div className="notice-text">{notice}</div>}
        <form onSubmit={handleSubmit}>
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            type="password"
            placeholder={mode === 'register' ? 'Password (min 8 characters)' : 'Password'}
            value={password}
            minLength={mode === 'register' ? 8 : undefined}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">
            {mode === 'login' ? 'Log in' : 'Create analyst account'}
          </button>
        </form>
        <button type="button" className="link-button" onClick={toggleMode}>
          {mode === 'login' ? 'New here? Request an analyst account' : 'Have an account? Log in instead'}
        </button>
        {mode === 'register' && (
          <div className="login-hint">
            Analyst accounts are read-only: you can watch alerts, events, the
            ATT&amp;CK matrix and threat news, but not manage sites or resolve alerts.
          </div>
        )}
      </div>
    </div>
  )
}