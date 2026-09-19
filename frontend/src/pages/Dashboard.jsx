import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchEvents, fetchAlerts, resolveAlert, logout, getUserRole } from '../api/client'
import EventList from '../components/EventList'
import AlertList from '../components/AlertList'
import AttackMatrix from './AttackMatrix'
import ThreatNews from '../components/ThreatNews'
import NewsTicker from '../components/NewsTicker'
import RadarBadge from '../components/RadarBadge'
import Sites from './Sites'

const POLL_INTERVAL_MS = 5000

export default function Dashboard() {
  const [events, setEvents] = useState([])
  const [alerts, setAlerts] = useState([])
  const [tab, setTab] = useState('alerts')
  const [focusTechniqueId, setFocusTechniqueId] = useState(null)
  const [actionError, setActionError] = useState('')
  const [online, setOnline] = useState(true)
  const navigate = useNavigate()

  // Admins can resolve alerts and register sites; analysts are read-only.
  // The role comes from the JWT claim, so no extra /auth/me request.
  const isAdmin = getUserRole() === 'admin'

  // Called when the person clicks a technique inside an alert row -- jumps
  // to the ATT&CK matrix tab and asks it to auto-search/select that exact
  // technique, rather than linking straight out to the external MITRE site.
  function viewTechniqueInMatrix(techniqueId) {
    setFocusTechniqueId(techniqueId)
    setTab('attack')
  }

  async function refresh() {
    try {
      const [ev, al] = await Promise.all([fetchEvents(50), fetchAlerts(50)])
      setEvents(ev)
      setAlerts(al)
      setOnline(true)
    } catch (err) {
      if (err.response?.status === 401) {
        logout()
        navigate('/login')
      } else {
        // Network / server hiccup -- keep showing the last data we have so
        // the dashboard doesn't flash empty on a transient disconnect. The
        // status pill flips to OFFLINE until the next poll succeeds.
        setOnline(false)
      }
    }
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [])

  async function handleResolve(alertId) {
    try {
      setActionError('')
      await resolveAlert(alertId)
    } catch (err) {
      setActionError(err.response?.data?.detail || 'Could not resolve alert')
    }
    refresh()
  }

  const openAlerts = alerts.filter((a) => !a.resolved)
  const critical = openAlerts.filter((a) => a.severity === 'critical').length
  const high = openAlerts.filter((a) => a.severity === 'high').length

  return (
    <div className="app-shell">
      <div className="sidebar">
        <div className="brand-row">
          <RadarBadge size={34} />
          <span className="brand-name"><span className="bindu">बिंदु</span>Parakh</span>
        </div>
        <div className={`nav-link ${tab === 'alerts' ? 'active' : ''}`} onClick={() => setTab('alerts')}>Alerts</div>
        <div className={`nav-link ${tab === 'events' ? 'active' : ''}`} onClick={() => setTab('events')}>Events</div>
        <div className={`nav-link ${tab === 'attack' ? 'active' : ''}`} onClick={() => setTab('attack')}>ATT&amp;CK matrix</div>
        <div className={`nav-link ${tab === 'sites' ? 'active' : ''}`} onClick={() => setTab('sites')}>Monitored sites</div>
        <div className={`nav-link ${tab === 'news' ? 'active' : ''}`} onClick={() => setTab('news')}>Threat news</div>
        <div className="nav-link" onClick={() => { logout(); navigate('/login') }}>Log out</div>
      </div>
      <div className="main-content">
        <NewsTicker />
        <div className={`conn-pill ${online ? 'conn-live' : 'conn-down'}`} role="status">
          <span className="conn-dot"></span>
          {online ? 'LIVE' : 'OFFLINE'}
        </div>
        {(tab === 'alerts' || tab === 'events') && (
          <div className="stat-grid">
            <div className="stat-card accent-neutral">
              <div className="label">Open alerts (recent 50)</div>
              <div className="value">{openAlerts.length}</div>
            </div>
            <div className="stat-card accent-critical">
              <div className="label">Critical</div>
              <div className="value">{critical}</div>
            </div>
            <div className="stat-card accent-high">
              <div className="label">High</div>
              <div className="value">{high}</div>
            </div>
            <div className="stat-card accent-neutral">
              <div className="label">Events shown (recent 50)</div>
              <div className="value">{events.length}</div>
            </div>
          </div>
        )}

        {tab === 'attack' ? (
          <AttackMatrix focusTechniqueId={focusTechniqueId} onFocusHandled={() => setFocusTechniqueId(null)} />
        ) : tab === 'sites' ? (
          <Sites />
        ) : tab === 'news' ? (
          <div className="card">
            <h3 style={{ marginTop: 0, fontSize: 15 }}>Live threat news</h3>
            <p style={{ color: '#7b8794', fontSize: 12, marginTop: -8, marginBottom: 16 }}>
              Real headlines from The Hacker News, fetched live -- click through to read the full article on their site.
            </p>
            <ThreatNews />
          </div>
        ) : (
          <div className="card">
            {actionError && <div className="error-text" style={{ fontSize: 12, marginBottom: 6 }}>{actionError}</div>}
            {tab === 'alerts' ? (
              <AlertList alerts={alerts} canResolve={isAdmin} onResolve={handleResolve} onViewTechnique={viewTechniqueInMatrix} />
            ) : (
              <EventList events={events} />
            )}
          </div>
        )}
      </div>
    </div>
  )
}
