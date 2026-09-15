import { useEffect, useState } from 'react'
import client from '../api/client'

export default function ThreatNews() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    client.get('/news')
      .then((res) => setItems(res.data.items))
      .catch(() => setError(true))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div style={{ color: '#7b8794', fontSize: 13 }}>Loading live threat news...</div>
  }

  if (error || items.length === 0) {
    return (
      <div style={{ color: '#7b8794', fontSize: 13 }}>
        Couldn't reach the live news feed right now. This can happen if the
        backend container has no internet access -- check your network and
        refresh.
      </div>
    )
  }

  return (
    <div>
      {items.map((item, i) => (
        <a key={i} href={item.link} target="_blank" rel="noreferrer" className="news-item">
          <div className="news-title">{item.title}</div>
          <div className="news-meta">{item.source} · {item.published}</div>
        </a>
      ))}
    </div>
  )
}
