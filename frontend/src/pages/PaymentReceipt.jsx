import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import apiClient from '../api/client'

function PaymentReceipt() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [payment, setPayment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchPayment = async () => {
      try {
        const response = await apiClient.get(`payments/${id}/`)
        setPayment(response.data)
      } catch (err) {
        console.error('Payment receipt error:', err.response?.data || err)
        setError('Unable to load payment receipt.')
      } finally {
        setLoading(false)
      }
    }

    fetchPayment()
  }, [id])

  const formatCurrency = (amount) => {
    return `KSh ${Number(amount).toLocaleString('en-KE', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`
  }

  const formatDate = (date) => {
    if (!date) return '--'
    return new Date(date).toLocaleString()
  }

  if (loading) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status"></div>
        <p className="mt-3">Loading payment receipt...</p>
      </div>
    )
  }

  if (error || !payment) {
    return (
      <div className="container py-5">
        <div className="alert alert-danger">
          {error || 'Payment not found.'}
        </div>

        <button
          className="btn btn-primary"
          onClick={() => navigate('/payments')}
        >
          Back to Payment History
        </button>
      </div>
    )
  }

  const billId = payment.bill_id ?? payment.bill

  return (
    <div className="container py-5">
      <div className="d-flex justify-content-between align-items-center mb-4 no-print">
        <button
          className="btn btn-outline-secondary"
          onClick={() => navigate('/payments')}
        >
          <i className="bi bi-arrow-left me-2"></i>
          Back to Payments
        </button>

        <button
          className="btn btn-primary"
          onClick={() => window.print()}
          disabled={payment.status !== 'successful'}
        >
          <i className="bi bi-printer me-2"></i>
          Print Receipt
        </button>
      </div>

      <div className="card border-0 shadow-sm mx-auto" style={{ maxWidth: '750px' }}>
        <div className="card-body p-4 p-md-5">

          <div className="text-center mb-4">
            <i className="bi bi-lightning-charge-fill text-primary fs-1"></i>

            <h3 className="fw-bold mt-2">
              Smart Utility Platform
            </h3>

            <p className="text-muted mb-0">
              Payment Receipt
            </p>
          </div>

          <hr />

          <div className="text-center my-4">
            <h2 className="fw-bold text-success">
              {formatCurrency(payment.amount)}
            </h2>

            <span className={`badge ${
              payment.status === 'successful'
                ? 'bg-success'
                : payment.status === 'pending'
                  ? 'bg-warning text-dark'
                  : 'bg-danger'
            }`}>
              {payment.status?.toUpperCase()}
            </span>
          </div>

          <hr />

          <h5 className="fw-bold mb-3">Transaction Details</h5>

          <div className="row mb-3">
            <div className="col-6 text-muted">Payment ID</div>
            <div className="col-6 text-end fw-semibold">
              #{payment.id}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Bill ID</div>
            <div className="col-6 text-end fw-semibold">
              #{billId ?? '--'}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Payment Method</div>
            <div className="col-6 text-end">
              {payment.payment_method || '--'}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Provider</div>
            <div className="col-6 text-end">
              {payment.provider || '--'}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Provider Reference</div>
            <div className="col-6 text-end fw-semibold text-break">
              {payment.provider_reference || '--'}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Initiated</div>
            <div className="col-6 text-end">
              {formatDate(payment.initiated_at)}
            </div>
          </div>

          <div className="row mb-3">
            <div className="col-6 text-muted">Processed</div>
            <div className="col-6 text-end">
              {formatDate(payment.processed_at)}
            </div>
          </div>

          <hr />

          <div className="text-center text-muted small mt-4">
            <p className="mb-1">
              Thank you for your payment.
            </p>
            <p className="mb-0">
              Please retain this receipt for your records.
            </p>
          </div>

        </div>
      </div>

      <style>{`
        @media print {
          body {
            background: white !important;
          }

          .no-print {
            display: none !important;
          }

          .card {
            box-shadow: none !important;
            border: 1px solid #ddd !important;
          }

          .container {
            padding: 0 !important;
          }
        }
      `}</style>
    </div>
  )
}

export default PaymentReceipt