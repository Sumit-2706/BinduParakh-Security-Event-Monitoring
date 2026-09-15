// A circular "radar console" badge -- the sweep line rotates slowly,
// like an old SOC radar/sonar display. Ties directly into the product's
// subject (threat monitoring) rather than being decoration for its own
// sake. Respects prefers-reduced-motion.
export default function RadarBadge({ size = 40 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className="radar-badge"
      role="img"
      aria-label="BinduParakh"
    >
      <defs>
        <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="sweepGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.9" />
        </linearGradient>
      </defs>

      <circle cx="50" cy="50" r="48" fill="var(--panel-raised)" stroke="var(--border)" strokeWidth="1.5" />
      <circle cx="50" cy="50" r="48" fill="url(#radarGlow)" />

      {/* Concentric range rings */}
      <circle cx="50" cy="50" r="36" fill="none" stroke="var(--accent)" strokeOpacity="0.25" strokeWidth="1" />
      <circle cx="50" cy="50" r="24" fill="none" stroke="var(--accent)" strokeOpacity="0.25" strokeWidth="1" />
      <circle cx="50" cy="50" r="12" fill="none" stroke="var(--accent)" strokeOpacity="0.3" strokeWidth="1" />

      {/* Crosshair */}
      <line x1="50" y1="4" x2="50" y2="96" stroke="var(--accent)" strokeOpacity="0.12" strokeWidth="1" />
      <line x1="4" y1="50" x2="96" y2="50" stroke="var(--accent)" strokeOpacity="0.12" strokeWidth="1" />

      {/* Rotating sweep */}
      <g className="radar-sweep">
        <path d="M 50 50 L 50 4 A 46 46 0 0 1 88 28 Z" fill="url(#sweepGradient)" />
      </g>

      {/* Center blip -- represents the "detected" alert */}
      <circle cx="68" cy="30" r="2.5" fill="var(--accent)" className="radar-blip" />
      <circle cx="50" cy="50" r="3" fill="var(--accent)" />
    </svg>
  )
}
