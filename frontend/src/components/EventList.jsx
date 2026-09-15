export default function EventList({ events }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Time</th>
          <th>Type</th>
          <th>Identity</th>
          <th>IP</th>
          <th>User-Agent</th>
        </tr>
      </thead>
      <tbody>
        {events.length === 0 && (
        <tr><td colSpan="5" style={{ color: '#7b8794' }}>No events yet.</td></tr>
        )}
        {events.map((e) => (
          <tr key={e.id}>
            <td>{new Date(e.created_at).toLocaleString()}</td>
            <td>{e.event_type}</td>
            <td>{e.identity || '-'}</td>
            <td>{e.ip_address || '-'}</td>
            <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {e.user_agent || '-'}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
