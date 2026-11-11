
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import apiClient from '../api/client'

function BillDetails() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [bill, setBill] = useState(null)
  const [readings, setReadings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadBill = async () => {
      if (!sessionStorage.getItem('access_token')) {
        navigate('/login')
        return
      }

      try {
        const [billResponse, readingsResponse] = await Promise.all([
          apiClient.get(`billing/bills/${id}/`),
          apiClient.get('meters/readings/'),
        ])

        setBill(billResponse.data)

        const readingData =
          readingsResponse.data.results ?? readingsResponse.data

        setReadings(readingData)

      } catch (err) {
        if (err.response?.status === 401) {
          sessionStorage.removeItem('access_token')
          navigate('/login')
        } else {
          setError(
            err.response?.data?.detail ||
            'Unable to load bill details.'
          )
        }
      } finally {
        setLoading(false)
      }
    }

    loadBill()
  }, [id, navigate])

  const formatMoney = (value) => {
    return Number(value || 0).toLocaleString('en-KE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  }

  const formatDate = (value) => {
    if (!value) return '—'

    return new Date(value).toLocaleDateString('en-KE', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  }

  const getReading = (readingId) => {
    return readings.find(
      (reading) => Number(reading.id) === Number(readingId)
    )
  }

  const previousReading = bill
    ? getReading(bill.previous_reading)
    : null

  const currentReading = bill
    ? getReading(bill.current_reading)
    : null

  if (loading) {
    return (
      <div className="container text-center mt-5">
        <div className="spinner-border text-primary" />
        <p className="mt-2">Loading bill...</p>
      </div>
    )
  }

  if (error || !bill) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger">
          {error || 'Bill not found.'}
        </div>

        <button
          className="btn btn-secondary"
          onClick={() => navigate('/dashboard')}
        >
          Back to Dashboard
        </button>
      </div>
    )
  }

  return (
    <div className="container py-4">

      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>
            <i className="bi bi-receipt me-2" />
            Bill #{bill.id}
          </h2>
          <p className="text-muted mb-0">
            Utility billing statement
          </p>
        </div>

        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-secondary"
            onClick={() => navigate('/dashboard')}
          >
            <i className="bi bi-arrow-left me-1" />
            Back
          </button>

          <button
            className="btn btn-primary"
            onClick={() => window.print()}
          >
            <i className="bi bi-printer me-1" />
            Print / Save PDF
          </button>
        </div>
      </div>

      <div className="card shadow-sm" id="invoice">

        <div className="card-body p-4 p-md-5">

          <div className="row mb-4">
            <div className="col-md-7">
              <h3 className="fw-bold text-primary">
                SMART UTILITY PLATFORM
              </h3>
              <p className="text-muted mb-0">
                Utility Billing Statement
              </p>
            </div>

            <div className="col-md-5 text-md-end mt-3 mt-md-0">
              <h4>INVOICE</h4>
              <p className="mb-1">
                <strong>Bill Number:</strong> #{bill.id}
              </p>
              <p className="mb-1">
                <strong>Issued:</strong> {formatDate(bill.created_at)}
              </p>
              <p className="mb-0">
                <strong>Due Date:</strong> {formatDate(bill.due_date)}
              </p>
            </div>
          </div>

          <hr />

          <div className="row my-4">
            <div className="col-md-6 mb-3">
              <h6 className="text-muted">CUSTOMER INFORMATION</h6>
              <p className="mb-1">
                <strong>Email:</strong> {bill.customer_email || '—'}
              </p>
              <p className="mb-1">
                <strong>Meter Number:</strong> {bill.meter_number}
              </p>
              <p className="mb-0">
                <strong>Meter ID:</strong> {bill.meter}
              </p>
            </div>

            <div className="col-md-6 mb-3">
              <h6 className="text-muted">BILLING INFORMATION</h6>
              <p className="mb-1">
                <strong>Tariff:</strong> {bill.tariff_name || '—'}
              </p>
              <p className="mb-1">
                <strong>Period From:</strong>{' '}
                {formatDate(bill.billing_period_start)}
              </p>
              <p className="mb-0">
                <strong>Period To:</strong>{' '}
                {formatDate(bill.billing_period_end)}
              </p>
            </div>
          </div>

          <h5 className="mt-4 mb-3">Meter Reading Details</h5>

          <div className="table-responsive">
            <table className="table table-bordered">
              <thead className="table-light">
                <tr>
                  <th>Description</th>
                  <th>Reading</th>
                  <th>Reading Date</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>Previous Reading</td>
                  <td>
                    {previousReading?.reading_value ?? '—'}
                  </td>
                  <td>
                    {formatDate(previousReading?.reading_date)}
                  </td>
                </tr>

                <tr>
                  <td>Current Reading</td>
                  <td>
                    {currentReading?.reading_value ?? '—'}
                  </td>
                  <td>
                    {formatDate(currentReading?.reading_date)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="row justify-content-end mt-4">
            <div className="col-md-6">

              <h5 className="mb-3">Charges Summary</h5>

              <table className="table">
                <tbody>
                  <tr>
                    <td>Units Consumed</td>
                    <td className="text-end">
                      {bill.units_consumed}
                    </td>
                  </tr>

                  <tr>
                    <td>Rate per Unit</td>
                    <td className="text-end">
                      KES {formatMoney(bill.rate_per_unit)}
                    </td>
                  </tr>

                  <tr>
                    <td>Subtotal</td>
                    <td className="text-end">
                      KES {formatMoney(bill.subtotal)}
                    </td>
                  </tr>

                  <tr>
                    <td>Fixed Charge</td>
                    <td className="text-end">
                      KES {formatMoney(bill.fixed_charge)}
                    </td>
                  </tr>

                  <tr className="table-primary fw-bold">
                    <td>Total Amount Due</td>
                    <td className="text-end">
                      KES {formatMoney(bill.amount)}
                    </td>
                  </tr>
                </tbody>
              </table>

              <div className="text-end mt-3">
                <span className={`badge ${
                  bill.status === 'paid'
                    ? 'bg-success'
                    : bill.status === 'overdue'
                      ? 'bg-danger'
                      : 'bg-warning text-dark'
                }`}>
                  {String(bill.status).toUpperCase()}
                </span>
              </div>

            </div>
          </div>

          <hr className="my-4" />

          <div className="text-center text-muted">
            <p className="mb-1">
              Thank you for using our utility services.
            </p>
            <small>
              This is a system-generated billing statement.
            </small>
          </div>

        </div>
      </div>

      <style>{`
        @media print {
          body {
            background: white !important;
          }

          body * {
            visibility: hidden;
          }

          #invoice,
          #invoice * {
            visibility: visible;
          }

          #invoice {
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            border: none !important;
            box-shadow: none !important;
          }

          button {
            display: none !important;
          }
        }
      `}</style>

    </div>
  )
}

export default BillDetails
