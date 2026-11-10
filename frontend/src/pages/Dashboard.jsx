import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import apiClient from '../api/client'

function Dashboard() {
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchProfile = async () => {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        navigate('/login', { replace: true })
        return
      }

      try {
        const response = await apiClient.get('auth/profile/')
        setProfile(response.data)

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem('access_token')
          sessionStorage.removeItem('refresh_token')

          navigate('/login', { replace: true })
          return
        }

        setError('Unable to load your profile. Please try again.')

      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [navigate])

  const handleLogout = () => {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')

    navigate('/login', { replace: true })
  }

  if (loading) {
    return (
      <div className="min-vh-100 d-flex justify-content-center align-items-center">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status"></div>
          <p className="mt-3 text-muted">Loading your dashboard...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">{error}</div>
        <button className="btn btn-primary" onClick={handleLogout}>
          Return to Login
        </button>
      </div>
    )
  }

  return (
    <div className="min-vh-100 bg-light">

      <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div className="container-fluid px-4">

          <a className="navbar-brand fw-bold" href="/dashboard">
            <i className="bi bi-lightning-charge-fill me-2"></i>
            Smart Utility
          </a>

          <div className="d-flex align-items-center gap-3">
            <span className="text-white">
              <i className="bi bi-person-circle me-2"></i>
              {profile?.username}
            </span>

            <button
              className="btn btn-outline-light btn-sm"
              onClick={handleLogout}
            >
              <i className="bi bi-box-arrow-right me-1"></i>
              Logout
            </button>
          </div>

        </div>
      </nav>

      <div className="container-fluid px-4 py-4">

        <div className="mb-4">
          <h2 className="fw-bold">
            Welcome, {profile?.username}!
          </h2>

          <p className="text-muted">
            Manage your utilities from one place.
          </p>

          <span className="badge bg-primary">
            {profile?.role}
          </span>
        </div>

        {/*
          Summary cards will be connected to the actual
          meters, billing, payments and support APIs next.
        */}

        <div className="row g-4">

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">My Meters</p>
                <h3 className="fw-bold">--</h3>
                <i className="bi bi-speedometer2 fs-1 text-primary"></i>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Outstanding Bills</p>
                <h3 className="fw-bold">--</h3>
                <i className="bi bi-receipt fs-1 text-warning"></i>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Total Payments</p>
                <h3 className="fw-bold">--</h3>
                <i className="bi bi-credit-card fs-1 text-success"></i>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Support Tickets</p>
                <h3 className="fw-bold">--</h3>
                <i className="bi bi-headset fs-1 text-info"></i>
              </div>
            </div>
          </div>

        </div>

        <div className="card border-0 shadow-sm mt-4">
          <div className="card-body p-4">
            <h5 className="fw-bold mb-3">Quick Actions</h5>

            <div className="row g-3">

              <div className="col-md-4">
                <button className="btn btn-outline-primary w-100 py-3">
                  <i className="bi bi-speedometer2 me-2"></i>
                  View My Meters
                </button>
              </div>

              <div className="col-md-4">
                <button className="btn btn-outline-primary w-100 py-3">
                  <i className="bi bi-receipt me-2"></i>
                  View My Bills
                </button>
              </div>

              <div className="col-md-4">
                <button className="btn btn-outline-primary w-100 py-3">
                  <i className="bi bi-headset me-2"></i>
                  Contact Support
                </button>
              </div>

            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

export default Dashboard