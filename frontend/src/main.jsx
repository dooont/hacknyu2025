import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Chart from './parts/chart'


createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Chart />
  </StrictMode>,
)
