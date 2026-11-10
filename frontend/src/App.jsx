import { useState } from 'react'
import './App.css'

function App() {
  const [showPassword, setShowPassword] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()

    setMessage('Login interface is ready. Authentication will be connected next.')
  }

  return (
    <div className="login-page">
      <div className="login-container">
        <div className="login-brand">
          <div className="brand-icon">
            <i className="bi bi-lightning-charge-fill"></i>
          </div>

          <h1>Smart Utility</h1>
          <p>Utility management made simple.</p>
        </div>

        <div className="login-card">
          <div className="login-heading">
            <h2>Welcome back</h2>
            <p>Sign in to access your account.</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="email" className="form-label">
                Email address
              </label>

              <input
                type="email"
                className="form-control"
                id="email"
                placeholder="Enter your email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>

            <div className="mb-3">
              <label htmlFor="password" className="form-label">
                Password
              </label>

              <div className="password-wrapper">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="form-control"
                  id="password"
                  placeholder="Enter your password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                </button>
              </div>
            </div>

            <div className="text-end mb-4">
              <a href="#forgot-password" className="forgot-link">
                Forgot password?
              </a>
            </div>

            <button type="submit" className="btn login-button w-100">
              Sign In
            </button>

            {message && (
              <div className="alert alert-info mt-3 mb-0" role="status">
                {message}
              </div>
            )}
          </form>

          <div className="login-footer">
            <p>
              Don't have an account? <a href="#register">Contact support</a>
            </p>
          </div>
        </div>

        <p className="copyright">
          © 2026 Smart Utility Platform. All rights reserved.
        </p>
      </div>
    </div>
  )
}

export default App