import { Ranking } from './components/Ranking'

const ENTRIES = [
  { id: 1, label: "Hector", score: 9840 },
  { id: 2, label: "Alex Poatan", score: 7200 },
  { id: 3, label: "Jon Jones", score: 6800 },
]

function App() {
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
      <Ranking entries={ENTRIES} title="Ranking" scoreType={1}/>
    </div>
  )
}

export default App