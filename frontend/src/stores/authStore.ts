import { create } from 'zustand'
import Cookies from 'js-cookie'

interface User {
  id: number
  username: string
  email: string
  employee_id?: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  setUser: (user: User | null) => void
  login: (user: User) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!Cookies.get('access_token'),
  setUser: (user) => set({ user, isAuthenticated: !!user }),
  login: (user) => set({ user, isAuthenticated: true }),
  logout: () => {
    Cookies.remove('access_token', { path: '/' })
    Cookies.remove('refresh_token', { path: '/' })
    set({ user: null, isAuthenticated: false })
  },
}))
