import { useEffect, useState } from 'react'
import client from '../api/client'
import AttackHubWheel from '../components/AttackHubWheel'

export default function AttackMatrix({ focusTechniqueId, onFocusHandled }) {
  const [tactics, setTactics] = useState([])
  const [selectedTactic, setSelectedTactic] = useState(null)
  const [techniques, setTechniques] = useState([])
  const [search, setSearch] = useState('')
  const [selectedTechnique, setSelectedTechnique] = useState(null)
  const [stats, setStats] = useState(null)

  useEffect(() => {
    client.get('/attack/tactics').then((res) => setTactics(res.data))
    client.get('/attack/stats').then((res) => setStats(res.data))
  }, [])

  // When an alert row asks us to focus a specific technique (e.g. clicking
  // "T1110 -- Brute Force" in the Alerts tab), search for its exact ID and
  // clear any tactic-wheel filter so it's guaranteed to show up in results.
  useEffect(() => {
    if (focusTechniqueId) {
      setSelectedTactic(null)
      setSearch(focusTechniqueId)
    }
  }, [focusTechniqueId])

  useEffect(() => {
    const params = {}
    if (selectedTactic) params.tactic = selectedTactic
    if (search) params.search = search
    params.limit = 200
    client.get('/attack/techniques', { params }).then((res) => {
      setTechniques(res.data)
      // Once the focused technique's exact ID search returns a result,
      // auto-select it so the detail panel (with the official MITRE link)
      // opens immediately without an extra click.
      if (focusTechniqueId) {
        const match = res.data.find((t) => t.technique_id === focusTechniqueId)
        if (match) {
          setSelectedTechnique(match)
          onFocusHandled?.()
        }
      }
    })
  }, [selectedTactic, search])

  return (
    <div>
      {stats && (
        <div className="stat-grid">
          <div className="stat-card accent-neutral">
            <div className="label">Tactics</div>
            <div className="value">{stats.total_tactics}</div>
          </div>
          <div className="stat-card accent-neutral">
            <div className="label">Techniques</div>
            <div className="value">{stats.total_techniques}</div>
          </div>
          <div className="stat-card accent-neutral">
            <div className="label">Sub-techniques</div>
            <div className="value">{stats.total_subtechniques}</div>
          </div>
          <div className="stat-card accent-teal">
            <div className="label">Actively detected</div>
            <div className="value">{stats.techniques_actively_detected}</div>
          </div>
        </div>
      )}

      <div className="card">
        <input
          placeholder="Search techniques (e.g. 'phishing', 'brute force')..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ marginBottom: 16 }}
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, alignItems: 'start' }}>
          <div>
            {tactics.length > 0 && (
              <AttackHubWheel
                tactics={tactics}
                selected={selectedTactic}
                onSelect={(shortname) => setSelectedTactic(selectedTactic === shortname ? null : shortname)}
                techniqueCount={techniques.length}
              />
            )}
            {selectedTactic && (
              <div style={{ textAlign: 'center', marginTop: 8 }}>
                <button style={{ width: 'auto', padding: '4px 14px', fontSize: 12 }} onClick={() => setSelectedTactic(null)}>
                  Clear selection
                </button>
              </div>
            )}
          </div>

          <div>
            <div style={{ maxHeight: 300, overflowY: 'auto', marginBottom: 16 }}>
              <table>
                <thead>
                  <tr><th>ID</th><th>Technique</th></tr>
                </thead>
                <tbody>
                  {techniques.map((t) => (
                    <tr
                      key={t.technique_id}
                      style={{ cursor: 'pointer', background: selectedTechnique?.technique_id === t.technique_id ? 'rgba(232,163,61,0.08)' : 'transparent' }}
                      onClick={() => setSelectedTechnique(t)}
                    >
                      <td className="mono" style={{ color: '#e8a33d', fontSize: 11 }}>
                        {t.is_subtechnique ? '\u00A0\u00A0↳ ' : ''}{t.technique_id}
                      </td>
                      <td>{t.name}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {selectedTechnique ? (
              <div>
                <h3 style={{ color: '#e8a33d', marginBottom: 4 }}>
                  {selectedTechnique.technique_id} — {selectedTechnique.name}
                </h3>
                <div style={{ marginBottom: 12 }}>
                  {selectedTechnique.tactics.map((tac) => (
                    <span key={tac} className="severity-badge severity-medium" style={{ marginRight: 6 }}>{tac}</span>
                  ))}
                </div>
                <p style={{ color: '#7b8794', fontSize: 13, lineHeight: 1.6 }}>{selectedTechnique.description}</p>
                {selectedTechnique.detection && (
                  <>
                    <h4 style={{ marginBottom: 4, fontSize: 13 }}>Detection guidance</h4>
                    <p style={{ color: '#7b8794', fontSize: 13, lineHeight: 1.6 }}>{selectedTechnique.detection}</p>
                  </>
                )}
                {selectedTechnique.mitigations?.length > 0 && (
                  <>
                    <h4 style={{ marginBottom: 4, fontSize: 13 }}>Mitigations</h4>
                    <ul style={{ color: '#7b8794', fontSize: 13 }}>
                      {selectedTechnique.mitigations.map((m) => <li key={m}>{m}</li>)}
                    </ul>
                  </>
                )}
                <a
                  href={`https://attack.mitre.org/techniques/${selectedTechnique.technique_id.replace('.', '/')}/`}
                  target="_blank" rel="noreferrer"
                  style={{ color: '#e8a33d', fontSize: 12 }}
                >
                  View on attack.mitre.org →
                </a>
              </div>
            ) : (
              <div style={{ color: '#7b8794', fontSize: 13 }}>Click a tactic on the wheel, or a technique in the list, to see details.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
