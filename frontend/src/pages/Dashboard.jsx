import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

function Dashboard() {
  const navigate = useNavigate()

  useEffect(() => {
    const token = sessionStorage.getItem('access_token')

    if (!token) {
      navigate('/login', { replace: true })
    }
  }, [navigate])

  const handleLogout = () => {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')

    navigate('/login', { replace: true })
  }

  return (
    <div className="min-vh-100 bg-light">

      {/* Navigation */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div className="container-fluid px-4">

          <a className="navbar-brand fw-bold" href="/dashboard">
            <i className="bi bi-lightning-charge-fill me-2"></i>
            Smart Utility
          </a>

          <div className="d-flex align-items-center gap-3">
            <span className="text-white">
              <i className="bi bi-person-circle me-2"></i>
              Customer
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

      {/* Dashboard Content */}
      <div className="container-fluid px-4 py-4">

        <div className="mb-4">
          <h2 className="fw-bold">Customer Dashboard</h2>
          <p className="text-muted">
            Welcome to your Smart Utility account.
            Manage your utilities from one place.
          </p>
        </div>

        {/* Summary Cards */}
        <div className="row g-4">

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <p className="text-muted mb-1">My Meters</p>
                    <h3 className="fw-bold">--</h3>
                  </div>
                  <i className="bi bi-speedometer2 fs-1 text-primary"></i>
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <p className="text-muted mb-1">Outstanding Bills</p>
                    <h3 className="fw-bold">--</h3>
                  </div>
                  <i className="bi bi-receipt fs-1 text-warning"></i>
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <p className="text-muted mb-1">Total Payments</p>
                    <h3 className="fw-bold">--</h3>
                  </div>
                  <i className="bi bi-credit-card fs-1 text-success"></i>
                </div>
              </div>
            </div>
          </div>

          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <div className="d-flex justify-content-between">
                  <div>
                    <p className="text-muted mb-1">Support Tickets</p>
                    <h3 className="fw-bold">--</h3>
                  </div>
                  <i className="bi bi-headset fs-1 text-info"></i>
                </div>
              </div>
            </div>
          </div>

        </div>

        {/* Quick Actions */}
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