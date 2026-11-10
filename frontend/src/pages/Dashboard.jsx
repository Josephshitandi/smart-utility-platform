
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import apiClient from '../api/client'

function Dashboard() {
  const navigate = useNavigate()

  const [profile, setProfile] = useState(null)
  const [meters, setMeters] = useState([])
  const [readings, setReadings] = useState([])
  const [bills, setBills] = useState([])

  const [meterCount, setMeterCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchDashboardData = async () => {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        navigate('/login', { replace: true })
        return
      }

      try {
        const [
          profileResponse,
          metersResponse,
          readingsResponse,
          billsResponse,
        ] = await Promise.all([
          apiClient.get('auth/profile/'),
          apiClient.get('meters/'),
          apiClient.get('meters/readings/'),
          apiClient.get('billing/bills/'),
        ])

        setProfile(profileResponse.data)

        const meterData = metersResponse.data
        const meterList = Array.isArray(meterData)
          ? meterData
          : meterData.results || []

        const readingData = readingsResponse.data
        const readingList = Array.isArray(readingData)
          ? readingData
          : readingData.results || []

        const billData = billsResponse.data
        const billList = Array.isArray(billData)
          ? billData
          : billData.results || []

        setMeters(meterList)
        setMeterCount(meterData.count ?? meterList.length)
        setReadings(readingList)
        setBills(billList)

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem('access_token')
          sessionStorage.removeItem('refresh_token')

          navigate('/login', { replace: true })
          return
        }

        console.error('Dashboard error:', err.response?.data || err)

        setError('Unable to load dashboard information.')

      } finally {
        setLoading(false)
      }
    }

    fetchDashboardData()
  }, [navigate])

  const handleLogout = () => {
    sessionStorage.removeItem('access_token')
    sessionStorage.removeItem('refresh_token')

    navigate('/login', { replace: true })
  }

  const formatDate = (date) => {
    if (!date) return '--'

    return new Date(date).toLocaleString()
  }

  const formatCurrency = (amount) => {
    return `KSh ${Number(amount).toLocaleString('en-KE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  // Calculate outstanding bills.
  const outstandingBills = bills.filter(
    (bill) => bill.status === 'pending'
  )

  const outstandingAmount = outstandingBills.reduce(
    (total, bill) => total + Number(bill.amount),
    0
  )

  const totalBills = bills.length

  // Calculate the latest consumption for each meter.
  const latestConsumption = meters.map((meter) => {
    const meterReadings = readings
      .filter((reading) => Number(reading.meter) === Number(meter.id))
      .sort(
        (a, b) =>
          new Date(b.reading_date) - new Date(a.reading_date)
      )

    const latest = meterReadings[0]
    const previous = meterReadings[1]

    const consumption =
      latest && previous
        ? Number(latest.reading_value) -
          Number(previous.reading_value)
        : null

    return {
      ...meter,
      latestReading: latest,
      previousReading: previous,
      consumption,
    }
  })

  if (loading) {
    return (
      <div className="min-vh-100 d-flex justify-content-center align-items-center">
        <div className="text-center">
          <div className="spinner-border text-primary" role="status"></div>
          <p className="mt-3 text-muted">
            Loading your dashboard...
          </p>
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

      {/* Navigation */}
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary shadow-sm">
        <div className="container-fluid px-4">

          <span className="navbar-brand fw-bold">
            <i className="bi bi-lightning-charge-fill me-2"></i>
            Smart Utility
          </span>

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

        {/* Welcome */}
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

        {/* Dashboard Summary Cards */}
        <div className="row g-4">

          {/* Meters */}
          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">My Meters</p>
                <h3 className="fw-bold">{meterCount}</h3>
                <i className="bi bi-speedometer2 fs-1 text-primary"></i>
              </div>
            </div>
          </div>

          {/* Readings */}
          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Meter Readings</p>
                <h3 className="fw-bold">{readings.length}</h3>
                <i className="bi bi-activity fs-1 text-info"></i>
              </div>
            </div>
          </div>

          {/* Outstanding Bills */}
          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Outstanding Bills</p>
                <h3 className="fw-bold">
                  {outstandingBills.length}
                </h3>

                <p className="text-muted mb-2">
                  {formatCurrency(outstandingAmount)}
                </p>

                <i className="bi bi-receipt fs-1 text-warning"></i>
              </div>
            </div>
          </div>

          {/* Total Bills */}
          <div className="col-md-6 col-xl-3">
            <div className="card border-0 shadow-sm h-100">
              <div className="card-body">
                <p className="text-muted mb-1">Total Bills</p>
                <h3 className="fw-bold">{totalBills}</h3>
                <i className="bi bi-file-earmark-text fs-1 text-success"></i>
              </div>
            </div>
          </div>

        </div>

        {/* Registered Meters */}
        <div className="card border-0 shadow-sm mt-4">
          <div className="card-body p-4">

            <h5 className="fw-bold mb-3">
              My Registered Meters
            </h5>

            {meters.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-speedometer2 fs-1 text-muted"></i>
                <p className="text-muted mt-3">
                  You don't have any registered meters yet.
                </p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">

                  <thead className="table-light">
                    <tr>
                      <th>Meter Number</th>
                      <th>Meter Type</th>
                      <th>Status</th>
                      <th>Installation Date</th>
                    </tr>
                  </thead>

                  <tbody>
                    {meters.map((meter) => (
                      <tr key={meter.id}>
                        <td className="fw-semibold">
                          {meter.meter_number}
                        </td>

                        <td>{meter.meter_type}</td>

                        <td>
                          <span className={`badge ${
                            meter.status === 'active'
                              ? 'bg-success'
                              : 'bg-secondary'
                          }`}>
                            {meter.status}
                          </span>
                        </td>

                        <td>{meter.installation_date}</td>
                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </div>
        </div>

        {/* Meter Consumption */}
        <div className="card border-0 shadow-sm mt-4">
          <div className="card-body p-4">

            <h5 className="fw-bold mb-3">
              Meter Consumption
            </h5>

            {latestConsumption.length === 0 ? (
              <p className="text-muted">
                No meter information available.
              </p>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">

                  <thead className="table-light">
                    <tr>
                      <th>Meter Number</th>
                      <th>Latest Reading</th>
                      <th>Previous Reading</th>
                      <th>Consumption</th>
                      <th>Reading Date</th>
                    </tr>
                  </thead>

                  <tbody>
                    {latestConsumption.map((meter) => (
                      <tr key={meter.id}>
                        <td className="fw-semibold">
                          {meter.meter_number}
                        </td>

                        <td>
                          {meter.latestReading?.reading_value ?? '--'}
                        </td>

                        <td>
                          {meter.previousReading?.reading_value ?? '--'}
                        </td>

                        <td className="fw-bold text-success">
                          {meter.consumption !== null
                            ? `${meter.consumption.toFixed(3)} units`
                            : '--'}
                        </td>

                        <td>
                          {meter.latestReading
                            ? formatDate(meter.latestReading.reading_date)
                            : '--'}
                        </td>
                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </div>
        </div>

        {/* Recent Meter Readings */}
        <div className="card border-0 shadow-sm mt-4">
          <div className="card-body p-4">

            <h5 className="fw-bold mb-3">
              Recent Meter Readings
            </h5>

            {readings.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-activity fs-1 text-muted"></i>
                <p className="text-muted mt-3">
                  No readings recorded yet.
                </p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">

                  <thead className="table-light">
                    <tr>
                      <th>Meter Number</th>
                      <th>Reading Value</th>
                      <th>Source</th>
                      <th>Status</th>
                      <th>Reading Date</th>
                    </tr>
                  </thead>

                  <tbody>
                    {readings.slice(0, 10).map((reading) => (
                      <tr key={reading.id}>
                        <td className="fw-semibold">
                          {reading.meter_number}
                        </td>

                        <td>{reading.reading_value}</td>

                        <td>{reading.source}</td>

                        <td>
                          <span className="badge bg-success">
                            {reading.status}
                          </span>
                        </td>

                        <td>{formatDate(reading.reading_date)}</td>
                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </div>
        </div>

        {/* Bill History */}
        <div className="card border-0 shadow-sm mt-4">
          <div className="card-body p-4">

            <div className="d-flex justify-content-between align-items-center mb-3">
              <h5 className="fw-bold mb-0">
                My Bill History
              </h5>

              <span className="badge bg-primary">
                {totalBills} Bills
              </span>
            </div>

            {bills.length === 0 ? (
              <div className="text-center py-4">
                <i className="bi bi-receipt fs-1 text-muted"></i>
                <p className="text-muted mt-3">
                  You don't have any bills yet.
                </p>
              </div>
            ) : (
              <div className="table-responsive">
                <table className="table table-hover align-middle">

                  <thead className="table-light">
                    <tr>
                      <th>Bill ID</th>
                      <th>Meter Number</th>
                      <th>Units Consumed</th>
                      <th>Amount</th>
                      <th>Due Date</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {bills.map((bill) => (
                      <tr key={bill.id}>
                        <td>#{bill.id}</td>

                        <td className="fw-semibold">
                          {bill.meter_number}
                        </td>

                        <td>{bill.units_consumed}</td>

                        <td className="fw-semibold">
                          {formatCurrency(bill.amount)}
                        </td>

                        <td>{bill.due_date}</td>

                        <td>
                          <span className={`badge ${
                            bill.status === 'paid'
                              ? 'bg-success'
                              : bill.status === 'pending'
                                ? 'bg-warning text-dark'
                                : 'bg-danger'
                          }`}>
                            {bill.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>

                </table>
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  )
}

export default Dashboard
