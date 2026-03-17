import { Ranking } from './components/Ranking'

const ENTRIES = [
  { id: 1, label: "Hector", score: 9840 },
  { id: 2, label: "Alex Poatan", score: 7200 },
  { id: 3, label: "Jon Jones", score: 6800 },
]


function App() {

  return (
    <>
      <Ranking entries={ENTRIES} title="Ranking" scoreLabel="pts" />
    </>
  )
}

export default App