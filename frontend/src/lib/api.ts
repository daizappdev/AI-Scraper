import axios from 'axios'
import toast from 'react-hot-toast'

const API_BASE_URL = (window as any).VITE_API_URL || 'http://localhost:8000/api'

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth-storage')
    if (token) {
      try {
        const authData = JSON.parse(token)
        if (authData.state?.token) {
          config.headers.Authorization = `Bearer ${authData.state.token}`
        }
      } catch (error) {
        console.error('Failed to parse auth data:', error)
      }
    }
    
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`[API] Success: ${response.config.method?.toUpperCase()} ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('[API] Response error:', error)
    
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Unauthorized - clear auth and redirect to login
          localStorage.removeItem('auth-storage')
          window.location.href = '/login'
          toast.error('Session expired. Please login again.')
          break
          
        case 403:
          toast.error('Access denied. You do not have permission to perform this action.')
          break
          
        case 404:
          toast.error('Resource not found.')
          break
          
        case 429:
          toast.error('Too many requests. Please wait a moment and try again.')
          break
          
        case 500:
          toast.error('Server error. Please try again later.')
          break
          
        default:
          const message = data?.detail || `Request failed with status ${status}`
          toast.error(message)
      }
    } else if (error.request) {
      // Network error
      toast.error('Network error. Please check your internet connection.')
    } else {
      // Something else happened
      toast.error('An unexpected error occurred.')
    }
    
    return Promise.reject(error)
  }
)

// API helpers
export const authAPI = {
  login: (username: string, password: string) => 
    api.post('/auth/login', { username, password }),
    
  register: (userData: {
    email: string
    username: string
    password: string
    full_name?: string
  }) => api.post('/auth/register', userData),
  
  getProfile: () => api.get('/auth/me'),
  
  updateProfile: (data: any) => api.put('/auth/me', data),
  
  refreshToken: () => api.post('/auth/refresh'),
}

export const scrapersAPI = {
  getScrapers: (skip = 0, limit = 20) => 
    api.get(`/scrapers?skip=${skip}&limit=${limit}`),
    
  getScraper: (id: number) => api.get(`/scrapers/${id}`),
  
  createScraper: (data: any) => api.post('/scrapers', data),
  
  updateScraper: (id: number, data: any) => api.put(`/scrapers/${id}`, data),
  
  deleteScraper: (id: number) => api.delete(`/scrapers/${id}`),
  
  generateScript: (id: number, description?: string) => 
    api.post(`/scrapers/${id}/generate`, { description }),
    
  downloadScript: (id: number) => 
    api.get(`/scrapers/${id}/script`, { responseType: 'blob' }),
    
  executeScraper: (id: number, options: {
    output_format?: string
    custom_url?: string
  } = {}) => api.post(`/scrapers/${id}/execute`, options),
  
  getExecutions: (id: number, skip = 0, limit = 20) => 
    api.get(`/scrapers/${id}/executions?skip=${skip}&limit=${limit}`),
}

export const usersAPI = {
  getProfile: () => api.get('/users/profile'),
  
  updateProfile: (data: any) => api.put('/users/profile', data),
  
  getCredits: () => api.get('/users/credits'),
  
  getScrapers: () => api.get('/users/scrapers'),
  
  getExecutions: () => api.get('/users/executions'),
}

export const adminAPI = {
  getStats: () => api.get('/admin/stats'),
  
  getUsers: (params: {
    skip?: number
    limit?: number
    search?: string
    active_only?: boolean
    premium_only?: boolean
  } = {}) => {
    const queryParams = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        queryParams.append(key, String(value))
      }
    })
    return api.get(`/admin/users?${queryParams}`)
  },
  
  getUser: (id: number) => api.get(`/admin/users/${id}`),
  
  updateUserStatus: (id: number, is_active: boolean) => 
    api.put(`/admin/users/${id}/status`, { is_active }),
    
  updateUserPremium: (id: number, is_premium: boolean) => 
    api.put(`/admin/users/${id}/premium`, { is_premium }),
    
  updateUserCredits: (id: number, credits: number) => 
    api.put(`/admin/users/${id}/credits`, { credits }),
    
  getRecentExecutions: () => api.get('/admin/executions/recent'),
  
  getRecentAILogs: () => api.get('/admin/ai-logs/recent'),
  
  getSettings: () => api.get('/admin/settings'),
  
  updateSetting: (key: string, value: string, description?: string) => 
    api.put('/admin/settings', { key, value, description }),
    
  systemHealth: () => api.get('/admin/system/health'),
}