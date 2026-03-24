// src/components/Layout/Layout.jsx
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'

export default function Layout() {
  return (
    <div
      className="h-screen grid"
      style={{
        gridTemplateColumns: '260px 1fr',
        gridTemplateRows: '70px 1fr',
        gridTemplateAreas: '"sidebar header" "sidebar main"',
      }}
    >
      <div style={{ gridArea: 'sidebar' }}>
        <Sidebar />
      </div>
      <div style={{ gridArea: 'header' }}>
        <Header />
      </div>
      <main style={{ gridArea: 'main' }} className="overflow-y-auto bg-slate-50 p-8">
        <Outlet />
      </main>
    </div>
  )
}
