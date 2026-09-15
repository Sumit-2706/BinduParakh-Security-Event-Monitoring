import { useEffect, useState } from 'react'
import { fetchSites, createSite } from '../api/client'

export default function Sites() {
  const [sites, setSites] = useState([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [revealedKey, setRevealedKey] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  function refresh() {
    fetchSites().then(setSites).catch(() => {})
  }

  useEffect(() => { refresh() }, [])

  async function handleCreate(e) {
    e.preventDefault()
    setError('')
    setSuccess('')

    const trimmedName = name.trim()
    const trimmedEmail = email.trim()
    const emailLooksValid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)

    if (trimmedName.length < 2) {
      setError('Enter the real website/site name (at least 2 characters).')
      return
    }
    if (!emailLooksValid) {
      setError('Enter a valid contact email address for alerts.')
      return
    }

    try {
      const site = await createSite(trimmedName, trimmedEmail)
      setRevealedKey(site)
      setSuccess(`"${site.name}" was registered successfully -- alerts for it will go to ${site.contact_email}.`)
      setName('')
      setEmail('')
      refresh()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not create site')
    }
  }

  return (
    <div>
      <div className="card">
        <h3 style={{ margin: '0 0 4px 0', fontSize: 14 }}>Register a website to monitor</h3>
        <p style={{ color: '#7b8794', fontSize: 11.5, margin: '0 0 10px 0' }}>
          Each site gets its own API key and its own contact email --
          alerts for that site go straight to the team that owns it.
        </p>
        {error && <div className="error-text" style={{ fontSize: 12, marginBottom: 6 }}>{error}</div>}
        {success && <div style={{ color: '#5fd68f', fontSize: 12, marginBottom: 6 }}>{success}</div>}
        <form onSubmit={handleCreate} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, alignItems: 'start' }}>
          <input placeholder="Real website name (e.g. Demo Shop)" value={name} onChange={(e) => setName(e.target.value)} required />
          <input type="email" placeholder="Contact email for alerts" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <button type="submit" style={{ width: 110 }}>Add site</button>
        </form>
      </div>

      {revealedKey && (
        <div className="card" style={{ border: '1px solid #e8a33d' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h4 style={{ margin: 0, color: '#e8a33d', fontSize: 13 }}>"{revealedKey.name}" registered — how to connect it</h4>
            <button
              onClick={() => setRevealedKey(null)}
              style={{ width: 'auto', padding: '2px 10px', fontSize: 11, background: 'transparent', border: '1px solid #3a4452', color: '#8a94a3' }}
            >
              Dismiss
            </button>
          </div>
          <p style={{ fontSize: 12, color: '#d5dae1', margin: '10px 0 4px 0' }}>API key (copy this into the site's config):</p>
          <div className="mono" style={{ background: '#0a0e14', padding: 8, borderRadius: 6, fontSize: 11.5, color: '#e8a33d', marginBottom: 8, wordBreak: 'break-all' }}>
            {revealedKey.api_key}
          </div>
          <details>
            <summary style={{ cursor: 'pointer', fontSize: 12, color: '#8a94a3' }}>Show integration code snippet</summary>
            <pre className="mono" style={{ background: '#0a0e14', padding: 10, borderRadius: 6, fontSize: 10.5, color: '#a8b2c0', overflowX: 'auto', marginTop: 8 }}>
{`requests.post(
    "http://localhost:8000/ingest/log",
    headers={"X-API-Key": "${revealedKey.api_key}"},
    json={
        "event_type": "login_failure",
        "identity": username,
        "ip_address": request.remote_addr,
    },
)`}
            </pre>
          </details>
        </div>
      )}

      <div className="card">
        <h3 style={{ margin: '0 0 8px 0', fontSize: 14 }}>Monitored sites</h3>
        <table>
          <thead><tr><th>Name</th><th>Contact email</th><th>Registered</th></tr></thead>
          <tbody>
            {sites.length === 0 && <tr><td colSpan="3" style={{ color: '#7b8794' }}>No sites registered yet.</td></tr>}
            {sites.map((s) => (
              <tr key={s.id}>
                <td>{s.name}</td>
                <td>{s.contact_email}</td>
                <td>{new Date(s.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
