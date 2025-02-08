import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Chart from './parts/Chart'
import { DataTableDemo } from './parts/Table'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <div className="flex space-x-4 w-11/12 mx-auto mt-8">
      <div className="w-[65%] p-4">
        <Chart />
      </div>
      <div className="w-[35%] p-4">
        <DataTableDemo />
      </div>
    </div>
  </StrictMode>,
);
