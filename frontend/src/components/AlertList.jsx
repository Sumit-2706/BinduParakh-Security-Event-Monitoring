export default function AlertList({ alerts, onResolve, onViewTechnique }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Rule</th>
          <th>MITRE ATT&CK</th>
          <th>Severity</th>
          <th>Description</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        {alerts.length === 0 && (
          <tr><td colSpan="7" style={{ color: '#7b8794' }}>No alerts yet.</td></tr>
        )}
        {alerts.map((a) => (
          <tr key={a.id}>
            <td>{new Date(a.created_at).toLocaleString()}</td>
            <td>{a.rule_name}</td>
            <td>
              {a.technique ? (
                <button
                  onClick={() => onViewTechnique(a.technique.technique_id)}
                  title="Open this technique in the ATT&CK matrix tab"
                  className="mono mitre-link"
                >
                  {a.technique.technique_id} — {a.technique.name}
                </button>
              ) : (
                <span style={{ color: '#6b7684' }}>—</span>
              )}
            </td>
            <td><span className={`severity-badge severity-${a.severity}`}>{a.severity}</span></td>
            <td>{a.description}</td>
            <td>{a.resolved ? 'Resolved' : 'Open'}</td>
            <td>
              {!a.resolved && (
                <button style={{ width: 'auto', padding: '4px 10px', fontSize: 12 }} onClick={() => onResolve(a.id)}>
                  Resolve
                </button>
              )}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
