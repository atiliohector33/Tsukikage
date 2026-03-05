import { useState } from 'react'
import { Ranking } from './Ranking'

const ENTRIES = [
  { id: 1, label: "Ana Lima", score: 9840 },
  { id: 2, label: "Carlos Mota", score: 7200 },
  { id: 3, label: "Beatriz Faro", score: 6800 },
]


function App() {

  return (
    <>
      <Ranking entries={ENTRIES} title="Ranking" scoreLabel="pts" />
    </>
  )
}

export default App