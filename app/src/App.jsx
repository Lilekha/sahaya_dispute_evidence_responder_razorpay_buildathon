import { Routes, Route } from 'react-router-dom'
import { Loader2, AlertTriangle } from 'lucide-react'
import { DataProvider, useData } from './context/DataContext'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Overview from './pages/Overview'
import Disputes from './pages/Disputes'
import DisputeDetail from './pages/DisputeDetail'
import Evidence from './pages/Evidence'
import Methodology from './pages/Methodology'

export default function App() {
  return (
    <DataProvider>
      <AppShell />
    </DataProvider>
  )
}

function AppShell() {
  const { loading, error } = useData()

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas">
        <div className="flex items-center gap-2 text-sm text-slate">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Loading dashboard data…
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-canvas p-6">
        <div className="flex max-w-md items-start gap-3 border border-gap bg-surface p-4 text-sm">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-gap" aria-hidden="true" />
          <div>
            <p className="font-medium text-ink">Couldn&rsquo;t load dashboard_data.json</p>
            <p className="mt-1 text-slate">{error.message}</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <div className="ml-16 flex min-h-screen flex-col md:ml-60">
        <Topbar />
        <main className="mx-auto w-full max-w-[1280px] flex-1 p-6">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/disputes" element={<Disputes />} />
            <Route path="/disputes/:id" element={<DisputeDetail />} />
            <Route path="/evidence" element={<Evidence />} />
            <Route path="/methodology" element={<Methodology />} />
          </Routes>
        </main>
        <footer className="border-t border-line px-6 py-4 text-[11px] text-slate">
          SaHaYa — Saboot Hai Yahan · Built on Razorpay&rsquo;s dispute schema · Prototype, not
          affiliated with Razorpay
        </footer>
      </div>
    </div>
  )
}
