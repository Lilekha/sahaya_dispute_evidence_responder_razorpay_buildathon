import { Routes, Route } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Topbar from './components/Topbar'
import Overview from './pages/Overview'
import Disputes from './pages/Disputes'
import DisputeDetail from './pages/DisputeDetail'
import Evidence from './pages/Evidence'
import Methodology from './pages/Methodology'

export default function App() {
  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <div className="ml-60 flex min-h-screen flex-col">
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
      </div>
    </div>
  )
}
