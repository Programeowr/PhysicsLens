export const scenarios = [
  {
    title: "Inclined Plane",
    tag: "angles + normal",
    blurb: "Resolve gravity into parallel and perpendicular components on a ramp.",
    art: (
      <svg viewBox="0 0 160 90" aria-hidden="true">
        <polygon points="18,74 130,74 130,28" className="ink-fill" />
        <rect x="78" y="50" width="20" height="16" className="paper-fill" />
        <line x1="88" y1="50" x2="88" y2="27" className="ink-stroke" />
        <line x1="88" y1="50" x2="68" y2="60" className="accent-stroke" />
      </svg>
    ),
  },
  {
    title: "Horizontal Friction",
    tag: "drag + push",
    blurb: "Compute friction and net force for bodies moving over flat surfaces.",
    art: (
      <svg viewBox="0 0 160 90" aria-hidden="true">
        <line x1="12" y1="66" x2="146" y2="66" className="ink-stroke" />
        <rect x="58" y="48" width="30" height="18" className="ink-fill" />
        <line x1="88" y1="57" x2="120" y2="57" className="accent-stroke" />
        <line x1="58" y1="57" x2="34" y2="57" className="ink-stroke" />
      </svg>
    ),
  },
  {
    title: "Atwood Pulley",
    tag: "tension solve",
    blurb: "Symbolically solve pulley acceleration and tension for two hanging masses.",
    art: (
      <svg viewBox="0 0 160 90" aria-hidden="true">
        <circle cx="80" cy="22" r="10" className="paper-fill" />
        <line x1="66" y1="22" x2="94" y2="22" className="ink-stroke" />
        <line x1="88" y1="22" x2="88" y2="56" className="ink-stroke" />
        <rect x="64" y="56" width="16" height="14" className="ink-fill" />
      </svg>
    ),
  },
  {
    title: "Projectile Motion",
    tag: "trajectory",
    blurb: "Derive range, max height, and flight time from launch conditions.",
    art: (
      <svg viewBox="0 0 160 90" aria-hidden="true">
        <line x1="14" y1="70" x2="146" y2="70" className="ink-stroke" />
        <path d="M20 66 Q74 10 136 62" className="accent-stroke" fill="none" />
        <circle cx="20" cy="66" r="3" className="ink-fill" />
      </svg>
    ),
  },
];

export default function ScenarioGrid() {
  return (
    <section className="scenario-wrap" id="scenarios" aria-label="Supported physics scenarios">
      <div className="section-title">
        <h2>Diagram Atlas</h2>
        <p>Every card maps to one solver and one force-story.</p>
      </div>
      <div className="scenario-grid">
        {scenarios.map((scenario, index) => (
          <article
            className="scenario-card"
            key={scenario.title}
            data-magnetic
            style={{ animationDelay: `${0.2 + index * 0.08}s` }}
          >
            <div className="scenario-art">{scenario.art}</div>
            <h3>{scenario.title}</h3>
            <span className="tag">{scenario.tag}</span>
            <p>{scenario.blurb}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
