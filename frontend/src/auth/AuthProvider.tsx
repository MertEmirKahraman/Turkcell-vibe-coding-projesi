import { useMemo, useState, type ReactNode } from 'react'

import { saveAccessToken } from '../api/client'
import { AuthContext } from './auth-context'

const refreshTokenKey = 'kahvecell.refreshToken'
const roleKey = 'kahvecell.role'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => localStorage.getItem('kahvecell.accessToken') !== null,
  )
  const [role, setRole] = useState<string | null>(
    () => localStorage.getItem(roleKey),
  )

  const value = useMemo(
    () => ({
      isAuthenticated,
      role,
      signIn(accessToken: string, refreshToken: string, userRole: string) {
        saveAccessToken(accessToken)
        localStorage.setItem(refreshTokenKey, refreshToken)
        localStorage.setItem(roleKey, userRole)
        setIsAuthenticated(true)
        setRole(userRole)
      },
      signOut() {
        saveAccessToken(null)
        localStorage.removeItem(refreshTokenKey)
        localStorage.removeItem(roleKey)
        setIsAuthenticated(false)
        setRole(null)
      },
    }),
    [isAuthenticated, role],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
