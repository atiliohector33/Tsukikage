import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import Tsukikage from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Tsukikage />
  </StrictMode>,
)
