
import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'

function PaymentHistory() {
  const navigate = useNavigate()

  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const fetchPayments = async () => {
    try {
      setLoading(true)
      setError('')

      const response = await api.get('payments/')
      const data = response.data

      setPayments(Array.isArray(data) ? data : data.results || [])
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        'Unable to load payment history. Please try again.'
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPayments()
  }, [])

  const filteredPayments = useMemo(() => {
    return payments.filter((payment) => {
      const searchValue = search.toLowerCase()

      const matchesSearch =
        String(payment.id || '').includes(searchValue) ||
        String(payment.bill || payment.bill_id || '').includes(searchValue) ||
        String(payment.provider_reference || '')
          .toLowerCase()
          .includes(searchValue)

      const matchesStatus =
        statusFilter === 'all' || payment.status === statusFilter

      const paymentDate = payment.initiated_at
        ? new Date(payment.initiated_at).toISOString().slice(0, 10)
        : ''

      const matchesFrom = !dateFrom || paymentDate >= dateFrom
      const matchesTo = !dateTo || paymentDate <= dateTo

      return (
        matchesSearch &&
        matchesStatus &&
        matchesFrom &&
        matchesTo
      )
    })
  }, [payments, search, statusFilter, dateFrom, dateTo])

  const formatDate = (value) => {
    if (!value) return '—'

    return new Date(value).toLocaleString()
  }

  const formatAmount = (value) => {
    return Number(value || 0).toLocaleString('en-KE', {
      style: 'currency',
      currency: 'KES',
    })
  }

  const getStatusClass = (status) => {
    switch (status) {
      case 'successful':
        return 'bg-success'
      case 'pending':
        return 'bg-warning text-dark'
      case 'failed':
        return 'bg-danger'
      default:
        return 'bg-secondary'
    }
  }

  return (
    <div className="container-fluid py-4">
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-4 gap-3">
        <div>
          <h2 className="fw-bold mb-1">Payment History</h2>
          <p className="text-muted mb-0">
            View and track your payment transactions.
          </p>
        </div>

        <div className="d-flex gap-2">
          <button
            className="btn btn-outline-secondary"
            onClick={() => navigate('/dashboard')}
          >
            Back to Dashboard
          </button>

          <button
            className="btn btn-primary"
            onClick={fetchPayments}
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          {error}
        </div>
      )}

      <div className="card shadow-sm mb-4">
        <div className="card-body">
          <h5 className="fw-semibold mb-3">Filter Transactions</h5>

          <div className="row g-3">
            <div className="col-md-4">
              <label className="form-label">Search</label>
              <input
                type="text"
                className="form-control"
                placeholder="Payment ID, bill ID or provider reference"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>

            <div className="col-md-2">
              <label className="form-label">Payment Status</label>
              <select
                className="form-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="pending">Pending</option>
                <option value="successful">Successful</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div className="col-md-3">
              <label className="form-label">From Date</label>
              <input
                type="date"
                className="form-control"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
              />
            </div>

            <div className="col-md-3">
              <label className="form-label">To Date</label>
              <input
                type="date"
                className="form-control"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
              />
            </div>
          </div>

          <div className="mt-3">
            <button
              className="btn btn-sm btn-outline-secondary"
              onClick={() => {
                setSearch('')
                setStatusFilter('all')
                setDateFrom('')
                setDateTo('')
              }}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="card shadow-sm">
        <div className="card-header bg-white py-3">
          <div className="d-flex justify-content-between align-items-center">
            <h5 className="mb-0 fw-semibold">Transactions</h5>
            <span className="badge bg-primary">
              {filteredPayments.length} Records
            </span>
          </div>
        </div>

        <div className="card-body">
          {loading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status" />
              <p className="mt-2 text-muted">Loading payments...</p>
            </div>
          ) : filteredPayments.length === 0 ? (
            <div className="text-center py-5">
              <h5>No payments found</h5>
              <p className="text-muted mb-0">
                Try changing your search or filters.
              </p>
            </div>
          ) : (
            <div className="table-responsive">
              <table className="table table-hover align-middle">
                <thead className="table-light">
                  <tr>
                    <th>Payment ID</th>
                    <th>Bill ID</th>
                    <th>Amount</th>
                    <th>Method</th>
                    <th>Provider</th>
                    <th>Provider Reference</th>
                    <th>Status</th>
                    <th>Initiated</th>
                    <th>Processed</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredPayments.map((payment) => (
                    <tr key={payment.id}>
                      <td>#{payment.id}</td>

                      <td>
                        #{payment.bill || payment.bill_id || '—'}
                      </td>

                      <td className="fw-semibold">
                        {formatAmount(payment.amount)}
                      </td>

                      <td>
                        {payment.payment_method || '—'}
                      </td>

                      <td>
                        {payment.provider || '—'}
                      </td>

                      <td>
                        {payment.provider_reference || '—'}
                      </td>

                      <td>
                        <span
                          className={`badge ${getStatusClass(payment.status)}`}
                        >
                          {payment.status || 'Unknown'}
                        </span>
                      </td>

                      <td>{formatDate(payment.initiated_at)}</td>

                      <td>{formatDate(payment.processed_at)}</td>

                      <td>
                        <div className="d-flex gap-2">
                          <button
                            className="btn btn-sm btn-outline-primary"
                            onClick={() =>
                              navigate(
                                `/bills/${payment.bill || payment.bill_id}`
                              )
                            }
                          >
                            View Bill
                          </button>

                          <button
                            className="btn btn-sm btn-outline-success"
                            onClick={() =>
                              navigate(`/payments/${payment.id}`)
                            }
                          >
                            View Receipt
                          </button>
                        </div>
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
  )
}

export default PaymentHistory
