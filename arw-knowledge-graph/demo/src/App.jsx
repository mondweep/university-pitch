import { Routes, Route } from 'react-router-dom'
import Layout from './components/shared/Layout'
import HomePage from './pages/HomePage'
import CostCalculatorPage from './pages/CostCalculatorPage'
import SpeedDemonPage from './pages/SpeedDemonPage'
import GraphNavigatorPage from './pages/GraphNavigatorPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/cost-calculator" element={<CostCalculatorPage />} />
        <Route path="/speed-demon" element={<SpeedDemonPage />} />
        <Route path="/graph-navigator" element={<GraphNavigatorPage />} />
      </Routes>
    </Layout>
  )
}

export default App
