// Shared access to the /news endpoint so the NewsTicker and the Threat News
// tab don't each fire their own identical request on every dashboard load.
// The fetch result is cached at module level for the life of the page; the
// backend already caches the feed itself for 30 minutes.
import { useEffect, useState } from 'react'
import client from '../api/client'

const newsState = { items: null, error: false, started: false }
let inflight = null

function load() {
  if (newsState.started) return Promise.resolve()
  if (!inflight) {
    newsState.started = true
    inflight = client
      .get('/news')
      .then((res) => { newsState.items = res.data.items || [] })
      .catch(() => { newsState.error = true; newsState.items = newsState.items || [] })
      .finally(() => { inflight = null })
  }
  return inflight
}

export default function useThreatNews() {
  const [state, setState] = useState({
    items: newsState.items || [],
    loading: !newsState.started,
    error: newsState.error,
  })

  useEffect(() => {
    let cancelled = false
    load().then(() => {
      if (!cancelled) {
        setState({ items: newsState.items || [], loading: false, error: newsState.error })
      }
    })
    return () => { cancelled = true }
  }, [])

  return state
}