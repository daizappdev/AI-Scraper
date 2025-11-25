import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '../lib/api'
import toast from 'react-hot-toast'

interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_active: boolean
  is_admin: boolean
  is_premium: boolean
  credits: number
  created_at: string
}

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  isLoading: boolean
  isAuthenticated: boolean
  
  // Actions
  login: (username: string, password: string) => Promise<void>
  register: (userData: RegisterData) => Promise<void>
  logout: () => void
  refreshAuthToken: () => Promise<void>
  updateUser: (userData: Partial<User>) => void
  setLoading: (loading: boolean) => void
}

interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isLoading: true,
      isAuthenticated: false,

      login: async (username: string, password: string) => {
        try {
          set({ isLoading: true })
          
          const response = await api.post('/auth/login', {
            username,
            password
          })
          
          const { access_token, refresh_token } = response.data
          
          // Set token in API client
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          // Get user data
          const userResponse = await api.get('/auth/me')
          
          set({
            user: userResponse.data,
            token: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false
          })
          
          toast.success('Welcome back!')
        } catch (error: any) {
          set({ isLoading: false })
          
          const message = error.response?.data?.detail || 'Login failed'
          toast.error(message)
          throw error
        }
      },

      register: async (userData: RegisterData) => {
        try {
          set({ isLoading: true })
          
          const response = await api.post('/auth/register', userData)
          
          // Auto-login after registration
          await get().login(userData.username, userData.password)
          
          toast.success('Account created successfully!')
        } catch (error: any) {
          set({ isLoading: false })
          
          const message = error.response?.data?.detail || 'Registration failed'
          toast.error(message)
          throw error
        }
      },

      logout: () => {
        // Clear headers
        delete api.defaults.headers.common['Authorization']
        
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false
        })
        
        toast.success('Logged out successfully')
      },

      refreshAuthToken: async () => {
        try {
          const { refreshToken } = get()
          
          if (!refreshToken) {
            throw new Error('No refresh token available')
          }
          
          const response = await api.post('/auth/refresh', null, {
            headers: {
              Authorization: `Bearer ${refreshToken}`
            }
          })
          
          const { access_token, refresh_token } = response.data
          
          // Update tokens
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          set({
            token: access_token,
            refreshToken: refresh_token
          })
        } catch (error) {
          // If refresh fails, logout user
          get().logout()
          throw error
        }
      },

      updateUser: (userData: Partial<User>) => {
        const { user } = get()
        if (user) {
          set({
            user: { ...user, ...userData }
          })
        }
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading })
      }
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated
      })
    }
  )
)

// Initialize auth state on app start
const initializeAuth = async () => {
  const { token } = useAuthStore.getState()
  
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
    
    try {
      const response = await api.get('/auth/me')
      useAuthStore.setState({
        user: response.data,
        isAuthenticated: true,
        isLoading: false
      })
    } catch (error) {
      // Token might be expired, try to refresh
      try {
        await useAuthStore.getState().refreshAuthToken()
        
        // Retry getting user data
        const response = await api.get('/auth/me')
        useAuthStore.setState({
          user: response.data,
          isAuthenticated: true,
          isLoading: false
        })
      } catch (refreshError) {
        // Refresh failed, clear auth state
        useAuthStore.getState().logout()
      }
    }
  } else {
    useAuthStore.setState({ isLoading: false })
  }
}

// Initialize on module load
initializeAuth()