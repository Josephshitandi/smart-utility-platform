import axios from 'axios'

const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1/',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Automatically attach the JWT access token.
apiClient.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

export default apiClient