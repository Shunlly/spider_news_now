/**
 * Axios instance configuration.
 */

import axios from 'axios'

const apiBaseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const axiosInstance = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
axiosInstance.interceptors.request.use(
  (config) => {
    // Add any auth headers here if needed in future
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
axiosInstance.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // Handle errors globally
    const message = error.response?.data?.detail || error.message || 'Unknown error'
    console.error('API Error:', message)
    return Promise.reject(error)
  }
)

export default axiosInstance
