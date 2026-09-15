import { useEffect, useState } from 'react'
import client from '../api/client'

// A horizontally-scrolling ticker of live threat headlines, shown across
// the top of every dashboard tab. Each headline is a real hyperlink to
// the source article (opens in a new tab) so it's independently
// clickable even while the strip is animating.
export default function NewsTicker() {
  const [items, setItems] = useState([])

  useEffect(() => {
    let cancelled = false
    client.get('/news')
      .then((res) => { if (!cancelled) setItems(res.data.items || []) })
      .catch(() => { if (!cancelled) setItems([]) })
    return () => { cancelled = true }
  }, [])

  if (items.length === 0) return null

  // Duplicate the list so the CSS animation can loop seamlessly from
  // -50% back to 0% without a visible jump/gap.
  const looped = [...items, ...items]

  return (
    <div className="news-ticker">
      <span className="news-ticker-label">LIVE THREAT NEWS</span>
      <div className="news-ticker-track-wrap">
        <div className="news-ticker-track">
          {looped.map((item, i) => (
            <a
              key={i}
              href={item.link}
              target="_blank"
              rel="noreferrer"
              className="news-ticker-item"
              title={item.title}
            >
              {item.title}
            </a>
          ))}
        </div>
      </div>
    </div>
  )
}
