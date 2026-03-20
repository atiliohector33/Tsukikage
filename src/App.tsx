import { Ranking } from './components/Ranking'

const ENTRIES = [
  { id: 1, label: "Hector", score: 9840 },
  { id: 2, label: "Alex Poatan", score: 7200 },
  { id: 3, label: "Jon Jones", score: 6800 },
  { id: 4, label: "Amanda Nunes", score: 6500 },
  { id: 5, label: "Israel Adesanya", score: 6200 },
  { id: 6, label: "Valentina Shevchenko", score: 6000 },
  { id: 7, label: "Kamaru Usman", score: 5800 },
  { id: 8, label: "Stipe Miocic", score: 5500 },
  { id: 9, label: "Rose Namajunas", score: 5300 },
  { id: 10, label: "Francis Ngannou", score: 5000 },
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
        limit={10}
      />
    </div>
  )
}

export default Tsukikage