import axios from 'axios'

// Reads the backend URL from an env var so the same build works
// against local, staging, or production APIs without code changes.
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: API_BASE })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('bp_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export async function login(email, password) {
  const form = new URLSearchParams()
  form.append('username', email)
  form.append('password', password)
  const res = await client.post('/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  localStorage.setItem('bp_token', res.data.access_token)
  return res.data
}

export async function register(email, password) {
  const res = await client.post('/auth/register', { email, password })
  return res.data
}

export function logout() {
  localStorage.removeItem('bp_token')
}

export function isAuthenticated() {
  return !!localStorage.getItem('bp_token')
}

export async function fetchEvents(limit = 50) {
  const res = await client.get('/events', { params: { limit } })
  return res.data
}

export async function fetchAlerts(limit = 50) {
  const res = await client.get('/alerts', { params: { limit } })
  return res.data
}

export async function resolveAlert(alertId) {
  const res = await client.post(`/alerts/${alertId}/resolve`)
  return res.data
}

export async function logEvent(payload) {
  const res = await client.post('/events/log', payload)
  return res.data
}

export async function fetchSites() {
  const res = await client.get('/sites')
  return res.data
}

export async function createSite(name, contact_email) {
  const res = await client.post('/sites', { name, contact_email })
  return res.data
}

export default client
