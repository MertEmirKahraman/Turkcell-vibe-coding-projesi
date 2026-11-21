import { createContext } from 'react'

export interface AuthContextValue {
  isAuthenticated: boolean
  role: string | null
  signIn: (accessToken: string, refreshToken: string, role: string) => void
  signOut: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)
