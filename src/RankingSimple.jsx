const sortByScore = (entries) => [...entries].sort((a, b) => b.score - a.score);
const getMedal = (pos) => ({ 1: "🥇", 2: "🥈", 3: "🥉" }[pos] ?? null);

function Ranking({ entries, title, scoreLabel = "pts" }) {
  const sorted = sortByScore(entries);

  return (
    <div style={{ width: "100%", maxWidth: 400, fontFamily: "system-ui, sans-serif" }}>
      {title && <h2 style={{ fontSize: "1rem", fontWeight: 700, margin: "0 0 12px" }}>{title}</h2>}

      <ol style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 4 }}>
        {sorted.map((entry, index) => {
          const position = index + 1;
          const medal = getMedal(position);
          const initials = entry.label.slice(0, 2).toUpperCase();

          return (
            <li key={entry.id} style={{ display: "flex", alignItems: "center", gap: 12, padding: "10px 12px", borderRadius: 8, transition: "background 0.15s" }}
              onMouseEnter={e => e.currentTarget.style.background = "rgba(0,0,0,0.04)"}
              onMouseLeave={e => e.currentTarget.style.background = "transparent"}
            >
              <span style={{ minWidth: 28, fontSize: "0.85rem", fontWeight: 600, color: "#9ca3af", textAlign: "center" }}>
                {medal ?? `#${position}`}
              </span>

              <span style={{ width: 34, height: 34, borderRadius: "50%", background: "#e5e7eb", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "0.75rem", fontWeight: 700, flexShrink: 0, overflow: "hidden" }}>
                {entry.avatar ? <img src={entry.avatar} alt={entry.label} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : initials}
              </span>

              <span style={{ flex: 1, fontSize: "0.9rem", fontWeight: 500 }}>{entry.label}</span>

              <span style={{ fontSize: "0.85rem", fontWeight: 700, color: "#4f46e5" }}>
                {entry.score.toLocaleString("pt-BR")}
                <span style={{ fontSize: "0.7rem", fontWeight: 400, opacity: 0.6, marginLeft: 2 }}>{scoreLabel}</span>
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

const ENTRIES = [
  { id: 1, label: "Ana Lima", score: 9840 },
  { id: 2, label: "Carlos Mota", score: 7200 },
  { id: 3, label: "Beatriz Faro", score: 6800 },
  { id: 4, label: "Diego Ramos", score: 5100 },
  { id: 5, label: "Elisa Cruz", score: 3900 },
];

export default function App() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", padding: 24 }}>
      <Ranking entries={ENTRIES} title="Ranking" scoreLabel="pts" />
    </div>
  );
}
