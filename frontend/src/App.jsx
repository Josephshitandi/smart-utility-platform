
import { Routes, Route, Navigate } from 'react-router-dom'

import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import BillGeneration from './pages/BillGeneration'
import BillDetails from './pages/BillDetails'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<Login />} />

      <Route path="/register" element={<Register />} />

      <Route path="/dashboard" element={<Dashboard />} />

      <Route path="/bills/generate" element={<BillGeneration />} />

      <Route path="/bills/:id" element={<BillDetails />} />

      <Route
        path="*"
        element={<h1 className="text-center mt-5">404 - Page Not Found</h1>}
      />
    </Routes>
  )
}

export default App
