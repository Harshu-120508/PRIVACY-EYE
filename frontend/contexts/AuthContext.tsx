'use client'
import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Cookies from 'js-cookie'
import { authApi } from '@/lib/api'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string, remember_me?: boolean) => Promise<void>
  register: (email: string, password: string, confirm_password?: string, full_name?: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState<boolean>(true)

  const refreshUser = useCallback(async () => {
    try {
      const res = await authApi.me()
      setUser(res.data)
    } catch {
      setUser(null)
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      Cookies.remove('logged_in')
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('logged_in')
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  useEffect(() => {
    // Initial session hydration on application startup
    const hasToken =
      Cookies.get('logged_in') ||
      Cookies.get('access_token') ||
      Cookies.get('refresh_token') ||
      (typeof window !== 'undefined' && (localStorage.getItem('access_token') || localStorage.getItem('logged_in')))
    if (hasToken) {
      refreshUser()
    } else {
      setIsLoading(false)
    }
  }, [refreshUser])

  const login = async (email: string, password: string, remember_me: boolean = false) => {
    setIsLoading(true)
    try {
      const res = await authApi.login(email, password, remember_me)
      const userData = res.user || res.data?.user
      if (userData) {
        setUser(userData)
      } else {
        await refreshUser()
      }
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (email: string, password: string, confirm_password?: string, full_name?: string) => {
    setIsLoading(true)
    try {
      const res = await authApi.register(email, password, confirm_password, full_name)
      const userData = res.user || res.data?.user
      if (userData) {
        setUser(userData)
      } else {
        await refreshUser()
      }
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    setIsLoading(true)
    try {
      await authApi.logout()
    } finally {
      setUser(null)
      setIsLoading(false)
      router.push('/auth/login')
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
