import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import apiClient from '../api/client'

function BillGeneration() {
  const navigate = useNavigate()

  const [meters, setMeters] = useState([])
  const [readings, setReadings] = useState([])

  const [meterId, setMeterId] = useState('')
  const [previousReadingId, setPreviousReadingId] = useState('')
  const [currentReadingId, setCurrentReadingId] = useState('')
  const [dueDate, setDueDate] = useState('')

  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(null)

  // Load administrator profile, meters and readings.
  useEffect(() => {
    const loadData = async () => {
      const token = sessionStorage.getItem('access_token')

      if (!token) {
        navigate('/login')
        return
      }

      try {
        const profileResponse = await apiClient.get('auth/profile/')

        if (!profileResponse.data.is_superuser) {
          navigate('/dashboard')
          return
        }

        const [metersResponse, readingsResponse] = await Promise.all([
          apiClient.get('meters/'),
          apiClient.get('meters/readings/'),
        ])

        const meterData = metersResponse.data.results ?? metersResponse.data
        const readingData = readingsResponse.data.results ?? readingsResponse.data

        setMeters(
          meterData.filter((meter) => meter.status === 'active')
        )

        setReadings(readingData)

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem('access_token')
          navigate('/login')
        } else {
          setError(
            err.response?.data?.detail ||
            'Unable to load meters and readings.'
          )
        }
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [navigate])

  // Get readings belonging to the selected meter.
  const meterReadings = readings
    .filter((reading) => Number(reading.meter) === Number(meterId))
    .sort(
      (a, b) =>
        new Date(a.reading_date) - new Date(b.reading_date)
    )

  const previousReading = meterReadings.find(
    (reading) => Number(reading.id) === Number(previousReadingId)
  )

  // Only allow readings recorded after the previous reading.
  const availableCurrentReadings = previousReading
    ? meterReadings.filter(
        (reading) =>
          new Date(reading.reading_date) >
          new Date(previousReading.reading_date)
      )
    : []

  const formatDate = (date) => {
    return new Date(date).toLocaleString()
  }

  const formatError = (data) => {
    if (typeof data === 'string') return data

    if (data?.detail) return data.detail

    if (data && typeof data === 'object') {
      return Object.entries(data)
        .map(([field, messages]) => {
          const message = Array.isArray(messages)
            ? messages.join(', ')
            : String(messages)

          return `${field}: ${message}`
        })
        .join(' | ')
    }

    return 'Unable to generate bill.'
  }

  // Submit bill creation request.
  const handleSubmit = async (e) => {
    e.preventDefault()

    setError('')
    setSuccess(null)

    if (!meterId || !previousReadingId || !currentReadingId || !dueDate) {
      setError('Please complete all fields.')
      return
    }

    try {
      setSubmitting(true)

      const response = await apiClient.post('billing/bills/', {
        meter_id: Number(meterId),
        previous_reading_id: Number(previousReadingId),
        current_reading_id: Number(currentReadingId),
        due_date: dueDate,
      })

      setSuccess(response.data)

      setPreviousReadingId('')
      setCurrentReadingId('')
      setDueDate('')

    } catch (err) {
      if (err.response?.status === 401) {
        sessionStorage.removeItem('access_token')
        navigate('/login')
      } else {
        setError(formatError(err.response?.data))
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="container mt-5 text-center">
        <div className="spinner-border text-primary"></div>
        <p className="mt-2">Loading billing information...</p>
      </div>
    )
  }

  return (
    <div className="container py-4">

      {/* Page heading */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>
            <i className="bi bi-receipt me-2"></i>
            Generate Bill
          </h2>
          <p className="text-muted mb-0">
            Create a customer bill using recorded meter readings.
          </p>
        </div>

        <button
          className="btn btn-outline-secondary"
          onClick={() => navigate('/dashboard')}
        >
          <i className="bi bi-arrow-left me-1"></i>
          Dashboard
        </button>
      </div>

      {/* Error message */}
      {error && (
        <div className="alert alert-danger">
          <i className="bi bi-exclamation-triangle me-2"></i>
          {error}
        </div>
      )}

      {/* Successful bill generation */}
      {success && (
        <div className="alert alert-success">
          <h5>
            <i className="bi bi-check-circle me-2"></i>
            Bill generated successfully!
          </h5>

          <p className="mb-1">
            Bill number: <strong>#{success.id}</strong>
          </p>

          <p className="mb-1">
            Meter: <strong>{success.meter_number}</strong>
          </p>

          <p className="mb-1">
            Units consumed: <strong>{success.units_consumed}</strong>
          </p>

          <p className="mb-1">
            Amount: <strong>KES {success.amount}</strong>
          </p>

          <p className="mb-0">
            Due date: <strong>{success.due_date}</strong>
          </p>

          <button
            className="btn btn-success btn-sm mt-3"
            onClick={() => navigate('/dashboard')}
          >
            View Dashboard
          </button>
        </div>
      )}

      {/* Bill generation form */}
      <div className="card shadow-sm">
        <div className="card-header bg-primary text-white">
          <h5 className="mb-0">Bill Information</h5>
        </div>

        <div className="card-body">

          <form onSubmit={handleSubmit}>

            {/* Meter selection */}
            <div className="mb-3">
              <label className="form-label">
                Select Meter
              </label>

              <select
                className="form-select"
                value={meterId}
                onChange={(e) => {
                  setMeterId(e.target.value)
                  setPreviousReadingId('')
                  setCurrentReadingId('')
                  setSuccess(null)
                }}
                required
              >
                <option value="">Choose an active meter</option>

                {meters.map((meter) => (
                  <option key={meter.id} value={meter.id}>
                    {meter.meter_number} - {meter.meter_type} - {meter.customer_email}
                  </option>
                ))}
              </select>

              {meters.length === 0 && (
                <small className="text-danger">
                  No active meters are available.
                </small>
              )}
            </div>

            {/* Previous reading */}
            <div className="mb-3">
              <label className="form-label">
                Previous Reading
              </label>

              <select
                className="form-select"
                value={previousReadingId}
                onChange={(e) => {
                  setPreviousReadingId(e.target.value)
                  setCurrentReadingId('')
                  setSuccess(null)
                }}
                disabled={!meterId}
                required
              >
                <option value="">Select previous reading</option>

                {meterReadings.map((reading) => (
                  <option key={reading.id} value={reading.id}>
                    {reading.reading_value} units -
                    {' '}{formatDate(reading.reading_date)}
                  </option>
                ))}
              </select>
            </div>

            {/* Current reading */}
            <div className="mb-3">
              <label className="form-label">
                Current Reading
              </label>

              <select
                className="form-select"
                value={currentReadingId}
                onChange={(e) => {
                  setCurrentReadingId(e.target.value)
                  setSuccess(null)
                }}
                disabled={!previousReadingId}
                required
              >
                <option value="">Select current reading</option>

                {availableCurrentReadings.map((reading) => (
                  <option key={reading.id} value={reading.id}>
                    {reading.reading_value} units -
                    {' '}{formatDate(reading.reading_date)}
                  </option>
                ))}
              </select>
            </div>

            {/* Due date */}
            <div className="mb-4">
              <label className="form-label">
                Payment Due Date
              </label>

              <input
                type="date"
                className="form-control"
                value={dueDate}
                onChange={(e) => {
                  setDueDate(e.target.value)
                  setSuccess(null)
                }}
                required
              />
            </div>

            {/* Submit */}
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting || meters.length === 0}
            >
              {submitting ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2"></span>
                  Generating Bill...
                </>
              ) : (
                <>
                  <i className="bi bi-receipt me-2"></i>
                  Generate Bill
                </>
              )}
            </button>

          </form>
        </div>
      </div>
    </div>
  )
}

export default BillGeneration