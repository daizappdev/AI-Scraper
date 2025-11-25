import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './stores/authStore'

import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import CreateScraperPage from './pages/CreateScraperPage'
import ScraperDetailPage from './pages/ScraperDetailPage'
import ProfilePage from './pages/ProfilePage'
import AdminPage from './pages/AdminPage'
import LoadingSpinner from './components/LoadingSpinner'

function App() {
  const { user, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <Layout>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={!user ? <LoginPage /> : <Navigate to="/dashboard" />} />
        <Route path="/register" element={!user ? <RegisterPage /> : <Navigate to="/dashboard" />} />

        {/* Protected routes */}
        <Route path="/dashboard" element={user ? <DashboardPage /> : <Navigate to="/login" />} />
        <Route path="/create" element={user ? <CreateScraperPage /> : <Navigate to="/login" />} />
        <Route path="/scraper/:id" element={user ? <ScraperDetailPage /> : <Navigate to="/login" />} />
        <Route path="/profile" element={user ? <ProfilePage /> : <Navigate to="/login" />} />
        
        {/* Admin routes */}
        <Route path="/admin" element={user?.is_admin ? <AdminPage /> : <Navigate to="/dashboard" />} />

        {/* Catch all route */}
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </Layout>
  )
}

export default App