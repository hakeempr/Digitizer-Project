import { createContext, useContext, useState, useCallback } from 'react'
import { auth as authApi } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    // Rehydrate from localStorage on page refresh
    if (!authApi.isLoggedIn()) return null
    return authApi.getUser()
  })

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password)
    setUser({ name: data.full_name, email: data.email, role: data.role, id: data.user_id })
    return data
  }, [])

  const logout = useCallback(async () => {
    await authApi.logout()
    setUser(null)
  }, [])

  const updateUser = useCallback((patch) => {
    setUser(prev => ({ ...prev, ...patch }))
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
