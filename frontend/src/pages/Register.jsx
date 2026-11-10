
import { useState } from 'react'
import { Link } from 'react-router-dom'

import InputField from '../components/InputField'
import Button from '../components/Button'

function Register() {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    phone_number: '',
    password: '',
    confirmPassword: '',
  })

  const [message, setMessage] = useState('')

  const handleChange = (event) => {
    const { name, value } = event.target

    setFormData((previousData) => ({
      ...previousData,
      [name]: value,
    }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()

    if (formData.password !== formData.confirmPassword) {
      setMessage('Passwords do not match.')
      return
    }

    setMessage('Registration form completed. Backend connection comes next.')
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
              >
                Create Account
              </Button>

              {message && (
                <div className="alert alert-info mt-3 mb-0" role="status">
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
