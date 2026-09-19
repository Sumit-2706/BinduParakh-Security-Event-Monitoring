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

// Client-side guard: checks the token exists AND hasn't expired, by
// decoding the JWT payload's exp claim. A token that's present but stale
// (expired, or tampered-with) is treated as logged-out so the app routes
// back to /login instead of showing a dashboard that 401s on every poll.
export function isAuthenticated() {
  const token = localStorage.getItem('bp_token')
  if (!token) return false
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (!payload.exp) return true
    return payload.exp * 1000 > Date.now()
  } catch {
    return false
  }
}

// Reads the role claim the backend embeds in the JWT ("admin" | "analyst"),
// so admin-only UI (Resolve buttons, site registration) can be hidden from
// analysts instead of showing actions that always 403. A missing/unknown
// role defaults to non-admin (safe: the backend enforces the real check).
export function getUserRole() {
  const token = localStorage.getItem('bp_token')
  if (!token) return null
  try {
    const payload = JSON.parse(atob(token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    return payload.role === 'admin' ? 'admin' : (payload.role || 'analyst')
  } catch {
    return null
  }
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

export async function fetchSites() {
  const res = await client.get('/sites')
  return res.data
}

export async function createSite(name, contact_email) {
  const res = await client.post('/sites', { name, contact_email })
  return res.data
}

export default client
