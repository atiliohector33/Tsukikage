import { Ranking } from './components/Ranking'

const ENTRIES = [
  { id: 1, label: "Hector", score: 9840 },
  { id: 2, label: "Alex Poatan", score: 7200 },
  { id: 3, label: "Jon Jones", score: 6800 },
]

function Tsukikage() {
  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      gap: "20px",
      flexWrap: "wrap",
      background: "linear-gradient(135deg, #f5f3ff, #ede9fe)",
      padding: "20px"
    }}>
      <Ranking
        entries={ENTRIES}
        title="Ranking"
        highlightFn={(entry) => entry.score > 9000}
      />
    </div>
  )
}

export default Tsukikage