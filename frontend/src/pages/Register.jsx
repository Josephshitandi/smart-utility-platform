
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import InputField from '../components/InputField'
import Button from '../components/Button'
import apiClient from '../api/client'

function Register() {
  const navigate = useNavigate()

  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone_number: '',
    password: '',
    confirmPassword: '',
  })

  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (event) => {
    const { name, value } = event.target

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()

    setMessage('')
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    if (formData.password.length < 8) {
      setError('Password must contain at least 8 characters.')
      return
    }

    setLoading(true)

    try {
      const response = await apiClient.post('auth/register/', {
        username: formData.username,
        email: formData.email,
        phone_number: formData.phone_number,
        password: formData.password,
      })

      setMessage('Account created successfully! Redirecting to login...')

      setFormData({
        username: '',
        email: '',
        phone_number: '',
        password: '',
        confirmPassword: '',
      })

      setTimeout(() => {
        navigate('/login')
      }, 1500)

    } catch (err) {
      const data = err.response?.data

      if (data && typeof data === 'object') {
        const errorMessages = Object.entries(data)
          .map(([field, errors]) => {
            const details = Array.isArray(errors)
              ? errors.join(', ')
              : String(errors)

            return `${field}: ${details}`
          })

        setError(errorMessages.join(' | '))
      } else {
        setError('Unable to connect to the server. Please try again.')
      }

    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container py-5">
      <div className="row justify-content-center">
        <div className="col-md-7 col-lg-6">
          <div className="card shadow-sm border-0 p-4">

            <div className="text-center mb-4">
              <h2 className="fw-bold">Create an Account</h2>
              <p className="text-muted">
                Join the Smart Utility Platform
              </p>
            </div>

            <form onSubmit={handleSubmit}>

              <InputField
                label="Username"
                id="username"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleChange}
                required
              />

              <InputField
                label="Email Address"
                id="email"
                type="email"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange}
                required
              />

              <InputField
                label="Phone Number"
                id="phone_number"
                type="tel"
                placeholder="Enter your phone number"
                value={formData.phone_number}
                onChange={handleChange}
                required
              />

              <InputField
                label="Password"
                id="password"
                type="password"
                placeholder="Create a password"
                value={formData.password}
                onChange={handleChange}
                required
              />

              <InputField
                label="Confirm Password"
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                value={formData.confirmPassword}
                onChange={handleChange}
                required
              />

              <Button
                type="submit"
                className="login-button w-100"
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Create Account'}
              </Button>

              {error && (
                <div className="alert alert-danger mt-3" role="alert">
                  {error}
                </div>
              )}

              {message && (
                <div className="alert alert-success mt-3" role="status">
                  {message}
                </div>
              )}

            </form>

            <div className="text-center mt-4">
              <p className="text-muted">
                Already have an account?{' '}
                <Link to="/login">Sign in</Link>
              </p>
            </div>

          </div>
        </div>
      </div>
    </div>
  )
}

export default Register
