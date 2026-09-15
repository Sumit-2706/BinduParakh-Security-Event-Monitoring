import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login } from '../api/client'
import RadarBadge from '../components/RadarBadge'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand-row">
          <RadarBadge size={44} />
          <span className="brand-name"><span className="bindu">बिंदु</span>Parakh</span>
        </div>
        {error && <div className="error-text">{error}</div>}
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
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit">Log in</button>
        </form>
      </div>
    </div>
  )
}
