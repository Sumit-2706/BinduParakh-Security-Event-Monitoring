// A circular "hub wheel" for the 15 MITRE ATT&CK tactics -- center shows
// the currently selected tactic, spokes connect out to the other 14.
// Positions are computed with trigonometry rather than hardcoded, so it
// correctly handles all 15 tactics (not just a fixed subset).
const TACTIC_SYMBOLS = {
  'reconnaissance': '◎',
  'resource-development': '⚒',
  'initial-access': '⚿',
  'execution': '▶',
  'persistence': '⚓',
  'privilege-escalation': '▲',
  'defense-impairment': '⊘',
  'stealth': '◐',
  'credential-access': '⚷',
  'discovery': '⚲',
  'lateral-movement': '⇄',
  'collection': '▣',
  'command-and-control': '📡'.length ? '◈' : '◈',
  'exfiltration': '↥',
  'impact': '⚡',
}

// Splits a tactic name into up to two lines (breaking on a space closest
// to the middle) so long names like "Privilege Escalation" or "Lateral
// Movement" wrap instead of running past the edge of the SVG and getting
// clipped by the viewport.
function wrapLabel(name) {
  if (name.length <= 11 || !name.includes(' ')) return [name]
  const words = name.split(' ')
  if (words.length === 1) return [name]
  let bestSplit = 1
  let bestDiff = Infinity
  for (let i = 1; i < words.length; i++) {
    const a = words.slice(0, i).join(' ').length
    const b = words.slice(i).join(' ').length
    const diff = Math.abs(a - b)
    if (diff < bestDiff) { bestDiff = diff; bestSplit = i }
  }
  return [words.slice(0, bestSplit).join(' '), words.slice(bestSplit).join(' ')]
}

export default function AttackHubWheel({ tactics, selected, onSelect, techniqueCount }) {
  // Extra padding baked into the SVG canvas (beyond the wheel itself) so
  // two-line labels on the left/right edges have room to render fully
  // instead of being cut off by the viewBox boundary.
  const pad = 46
  const wheelSize = 440
  const size = wheelSize + pad * 2
  const center = size / 2
  const outerRadius = wheelSize / 2 - 55
  const nodeRadius = 24

  const selectedTactic = tactics.find((t) => t.shortname === selected)

  return (
    <svg width="100%" viewBox={`0 0 ${size} ${size}`} style={{ maxWidth: size, display: 'block', margin: '0 auto' }}>
      {/* Decorative rings only -- rotates slowly for a "radar sweep" feel.
          Kept in its own group, separate from the tactic nodes/labels
          below, so the text never spins and stays readable. */}
      <g className="hub-wheel-decor-ring">
        <circle cx={center} cy={center} r={outerRadius + 45} fill="none" stroke="#1c2530" />
        <circle cx={center} cy={center} r={outerRadius - 15} fill="none" stroke="#1c2530" />
        {Array.from({ length: 24 }).map((_, i) => {
          const a = (i / 24) * 2 * Math.PI
          const r1 = outerRadius + 45
          const r2 = r1 + 6
          return (
            <line
              key={i}
              x1={center + r1 * Math.cos(a)} y1={center + r1 * Math.sin(a)}
              x2={center + r2 * Math.cos(a)} y2={center + r2 * Math.sin(a)}
              stroke="#2a3441" strokeWidth={1}
            />
          )
        })}
      </g>

      {tactics.map((t, i) => {
        const angle = (i / tactics.length) * 2 * Math.PI - Math.PI / 2
        const x = center + outerRadius * Math.cos(angle)
        const y = center + outerRadius * Math.sin(angle)
        const isSelected = t.shortname === selected
        const lines = wrapLabel(t.name)
        const labelAnchor = x > center + 10 ? 'start' : x < center - 10 ? 'end' : 'middle'
        const labelX = x > center + 10 ? x + 30 : x < center - 10 ? x - 30 : x
        // Base vertical offset for the (possibly 2-line) label block,
        // then stack additional lines downward from there.
        const baseDy = y > center ? 40 : y < center - 5 ? -32 - (lines.length - 1) * 12 : 4

        return (
          <g key={t.shortname}>
            <line
              x1={center} y1={center} x2={x} y2={y}
              stroke="#e8a33d" strokeOpacity={isSelected ? 0.4 : 0.15}
            />
            <circle
              className="hub-tactic-node"
              cx={x} cy={y} r={nodeRadius}
              fill={isSelected ? '#1a1610' : '#141a24'}
              stroke={isSelected ? '#e8a33d' : '#3a4452'}
              strokeWidth={isSelected ? 2 : 1.5}
              onClick={() => onSelect(t.shortname)}
            />
            <text
              x={x} y={y + 5} textAnchor="middle" fontSize="14"
              fill={isSelected ? '#e8a33d' : '#8a94a3'}
              style={{ pointerEvents: 'none' }}
            >
              {TACTIC_SYMBOLS[t.shortname] || '•'}
            </text>
            <text
              x={labelX} textAnchor={labelAnchor} fontSize="10"
              fill={isSelected ? '#e8a33d' : '#8a94a3'}
              style={{ pointerEvents: 'none' }}
            >
              {lines.map((line, li) => (
                <tspan key={li} x={labelX} y={y + baseDy + li * 12}>{line}</tspan>
              ))}
            </text>
          </g>
        )
      })}

      <circle cx={center} cy={center} r={70} fill="#141410" stroke="#e8a33d" strokeWidth="1.5" />
      <text x={center} y={center - 12} textAnchor="middle" fontSize="9" fill="#7b8794" letterSpacing="1">
        CURRENTLY VIEWING
      </text>
      <text x={center} y={center + 8} textAnchor="middle" fontSize="14" fill="#e8a33d">
        {selectedTactic ? selectedTactic.name : 'All tactics'}
      </text>
      <text x={center} y={center + 26} textAnchor="middle" fontSize="10" fill="#6b7684">
        {techniqueCount} technique{techniqueCount === 1 ? '' : 's'}
      </text>
    </svg>
  )
}
