/**
 * API client — typed wrapper around axios for the Privacy Eye backend.
 */
import axios, { AxiosError } from 'axios'
import Cookies from 'js-cookie'

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120_000, // 2 min for video uploads
  withCredentials: true, // Support HttpOnly SameSite authentication cookies
})

/**
 * Reads the Double-Submit CSRF token from document cookies.
 * Supports js-cookie with fallback to document.cookie regex parsing.
 */
export function getCsrfToken(): string | undefined {
  if (typeof document === 'undefined') return undefined
  const cookieVal = Cookies.get('csrf_token')
  if (cookieVal) return cookieVal

  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/)
  return match ? decodeURIComponent(match[1]) : undefined
}

// Attach JWT and Double-Submit CSRF token on state-changing requests
api.interceptors.request.use((config) => {
  let token = Cookies.get('access_token')
  if (!token && typeof window !== 'undefined') {
    token = localStorage.getItem('access_token') || undefined
  }
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }

  // Central Double-Submit CSRF: set X-CSRF-Token on all state-changing requests
  const method = (config.method || 'get').toUpperCase()
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE']
  if (unsafeMethods.includes(method)) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      config.headers['X-CSRF-Token'] = csrfToken
    }
  }
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    if (err.response?.status === 401 && !err.config?.url?.includes('/auth/login') && !err.config?.url?.includes('/auth/refresh')) {
      const refresh = Cookies.get('refresh_token') || (typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null)
      try {
        const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh }, { withCredentials: true })
        const { access_token, refresh_token: new_refresh } = res.data
        Cookies.set('access_token', access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 7 })
        Cookies.set('logged_in', 'true', { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 7 })
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('logged_in', 'true')
        }
        if (new_refresh) {
          Cookies.set('refresh_token', new_refresh, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
          if (typeof window !== 'undefined') {
            localStorage.setItem('refresh_token', new_refresh)
          }
        }
        if (err.config) {
          err.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(err.config)
        }
      } catch {
        Cookies.remove('access_token')
        Cookies.remove('refresh_token')
        Cookies.remove('logged_in')
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('logged_in')
        }
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/auth/')) {
          window.location.href = `/auth/login?next=${encodeURIComponent(window.location.pathname)}`
        }
      }
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const authApi = {
  register: async (email: string, password: string, confirm_password?: string, full_name?: string) => {
    let finalConfirm = confirm_password
    let finalName = full_name

    // Handle 3-argument call: register(email, password, full_name)
    if (confirm_password !== undefined && full_name === undefined && confirm_password !== password) {
      finalName = confirm_password
      finalConfirm = password
    } else if (!finalConfirm) {
      finalConfirm = password
    }

    const res = await api.post('/auth/register', {
      email,
      password,
      confirm_password: finalConfirm,
      full_name: finalName,
    })
    const tokens = res.data.tokens || res.data
    if (tokens?.access_token) {
      Cookies.set('access_token', tokens.access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access_token)
      }
    }
    if (tokens?.refresh_token) {
      Cookies.set('refresh_token', tokens.refresh_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
      if (typeof window !== 'undefined') {
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }
    }
    Cookies.set('logged_in', 'true', { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
    if (typeof window !== 'undefined') {
      localStorage.setItem('logged_in', 'true')
    }
    return res.data
  },

  login: async (email: string, password: string, remember_me: boolean = false) => {
    const res = await api.post('/auth/login', { email, password, remember_me })
    const tokens = res.data.tokens || res.data
    const expiresDays = remember_me ? 30 : 1
    if (tokens?.access_token) {
      Cookies.set('access_token', tokens.access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: expiresDays })
      if (typeof window !== 'undefined') {
        localStorage.setItem('access_token', tokens.access_token)
      }
    }
    if (tokens?.refresh_token) {
      Cookies.set('refresh_token', tokens.refresh_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: expiresDays })
      if (typeof window !== 'undefined') {
        localStorage.setItem('refresh_token', tokens.refresh_token)
      }
    }
    Cookies.set('logged_in', 'true', { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: expiresDays })
    if (typeof window !== 'undefined') {
      localStorage.setItem('logged_in', 'true')
    }
    return res.data
  },

  me: () => api.get('/auth/me'),

  logout: async () => {
    try {
      return await api.post('/auth/logout')
    } catch {
      // ignore
    } finally {
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      Cookies.remove('logged_in')
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('logged_in')
      }
    }
  },

  logoutAll: async () => {
    try {
      return await api.post('/auth/logout-all')
    } finally {
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
      Cookies.remove('logged_in')
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('logged_in')
      }
    }
  },

  changePassword: (current_password: string, new_password: string, confirm_password?: string) =>
    api.post('/auth/change-password', { current_password, new_password, confirm_password }),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),

  resetPassword: (token: string, new_password: string, confirm_password?: string) =>
    api.post('/auth/reset-password', { token, new_password, confirm_password }),

  getSessions: () => api.get('/auth/sessions'),

  deleteSession: (session_id: string) => api.delete(`/auth/sessions/${session_id}`),

  deleteAccount: (password_confirmation: string) =>
    api.delete('/users/me', { data: { password_confirmation } }),

  requestVerification: (email?: string) =>
    api.post('/auth/request-verification', email ? { email } : {}),

  verifyEmail: (token: string) =>
    api.post('/auth/verify-email', { token }),
}

// ── Analysis ──────────────────────────────────────────────────────────────────
export const analysisApi = {
  analyzeImage: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    })
  },

  analyzeVideo: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/video', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    })
  },

  analyzeAudio: (file: File, onProgress?: (percent: number) => void) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/audio', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total && onProgress) {
          onProgress(Math.round((e.loaded * 100) / e.total))
        }
      },
    })
  },

  getHistory: (page = 1, perPage = 10, mediaType?: string) =>
    api.get('/analyze/history', { params: { page, per_page: perPage, media_type: mediaType } }),

  getAnalysis: (id: string) => api.get(`/analyze/${id}`),

  deleteAnalysis: (id: string) => api.delete(`/analyze/${id}`),

  purgeAllHistory: () => api.delete('/analyze/history/purge'),

  getStats: () => api.get('/analyze/stats'),
}

// ── Users & Sovereignty ───────────────────────────────────────────────────────
export const usersApi = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (fullName: string) => api.patch('/users/me', null, { params: { full_name: fullName } }),
  exportUserData: () => api.get('/users/me/export'),
  getAuditLogs: (page = 1, limit = 20, action?: string) =>
    api.get('/users/me/audit-logs', { params: { page, limit, action } }),
}

// ── Consents ──────────────────────────────────────────────────────────────────
export const consentsApi = {
  getConsents: () => api.get('/users/me/consents'),
  updateConsent: (purpose: string, granted: boolean, policy_version: string = '1.0.0') =>
    api.put('/users/me/consents', { purpose, granted, policy_version }),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  generate: (analysisId: string) => api.post(`/reports/${analysisId}/generate`),
  get:      (analysisId: string) => api.get(`/reports/${analysisId}`),
  downloadJson: (analysisId: string) =>
    api.get(`/reports/${analysisId}/download/json`, { responseType: 'blob' }),
  downloadHtml: (analysisId: string) =>
    api.get(`/reports/${analysisId}/download/html`, { responseType: 'blob' }),
}


// ── Live Camera Scan ─────────────────────────────────────────────────────────
export const liveScanApi = {
  analyzeFrame: (payload: { session_id: string; image_base64: string; run_challenge?: boolean }) =>
    api.post('/live/frame', payload),

  requestChallenge: (sessionId: string) =>
    api.post('/live/challenge', null, { params: { session_id: sessionId } }),

  saveAudit: (payload: {
    session_id: string
    assessment: string
    category_label?: string
    confidence: number
    quality_index: number
    signals: any[]
    explanation: string
    snapshot_base64?: string
    consent_given?: boolean
    landmarks?: any
    eye_status?: string
    blink_count?: number
    phone_detected?: boolean
    presentation_attack?: boolean
    reason_codes?: string[]
  }) => api.post('/live/save-audit', payload),

  submitConsent: (payload: {
    session_id: string
    consent_given: boolean
    category_label: string
    confidence: number
    quality_score?: number
    face_snapshot_base64?: string
    landmarks?: any
  }) => api.post('/live/consent-response', payload),

  getTrainingStats: () => api.get('/live/training-stats'),
}

// ── Admin ────────────────────────────────────────────────────────────────────
export const adminApi = {
  getStats: () => api.get('/admin/stats'),
  getUsers: (params?: { q?: string; role?: string; status?: string; limit?: number; offset?: number }) =>
    api.get('/admin/users', { params }),
  updateUserStatus: (userId: string, is_active: boolean) =>
    api.patch(`/admin/users/${userId}/status`, { is_active }),
  updateUserRole: (userId: string, role: string) =>
    api.patch(`/admin/users/${userId}/role`, { role }),
  getScans: (params?: { risk_level?: string; media_type?: string; limit?: number; offset?: number }) =>
    api.get('/admin/scans', { params }),
  getAuditLogs: (params?: { action?: string; limit?: number; offset?: number }) =>
    api.get('/admin/audit-logs', { params }),
  getModels: () => api.get('/admin/models'),
  getCurrentModel: () => api.get('/admin/model/current'),
}

// ── Helpers ───────────────────────────────────────────────────────────────────
export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data
    if (typeof data?.detail === 'string') return data.detail
    if (Array.isArray(data?.detail)) return data.detail.map((d: { msg: string }) => d.msg).join(', ')
    return err.message
  }
  return 'An unexpected error occurred.'
}
