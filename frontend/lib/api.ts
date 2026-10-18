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

// Attach JWT and CSRF token on every request
api.interceptors.request.use((config) => {
  const token = Cookies.get('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  // Double-submit CSRF protection: send csrf_token cookie value as header
  const csrfToken = Cookies.get('csrf_token')
  if (csrfToken) config.headers['X-CSRF-Token'] = csrfToken
  return config
})

// Auto-refresh on 401
api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    if (err.response?.status === 401 && !err.config?.url?.includes('/auth/login') && !err.config?.url?.includes('/auth/refresh')) {
      const refresh = Cookies.get('refresh_token')
      try {
        const res = await axios.post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh }, { withCredentials: true })
        const { access_token, refresh_token: new_refresh } = res.data
        Cookies.set('access_token', access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 7 })
        if (new_refresh) {
          Cookies.set('refresh_token', new_refresh, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
        }
        if (err.config) {
          err.config.headers.Authorization = `Bearer ${access_token}`
          return api.request(err.config)
        }
      } catch {
        Cookies.remove('access_token')
        Cookies.remove('refresh_token')
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
    const res = await api.post('/auth/register', { email, password, confirm_password, full_name })
    const tokens = res.data.tokens || res.data
    if (tokens?.access_token) {
      Cookies.set('access_token', tokens.access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
    }
    if (tokens?.refresh_token) {
      Cookies.set('refresh_token', tokens.refresh_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: 30 })
    }
    return res.data
  },

  login: async (email: string, password: string, remember_me: boolean = false) => {
    const res = await api.post('/auth/login', { email, password, remember_me })
    const tokens = res.data.tokens || res.data
    const expiresDays = remember_me ? 30 : 1
    if (tokens?.access_token) {
      Cookies.set('access_token', tokens.access_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: expiresDays })
    }
    if (tokens?.refresh_token) {
      Cookies.set('refresh_token', tokens.refresh_token, { secure: window.location.protocol === 'https:', sameSite: 'lax', expires: expiresDays })
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
    }
  },

  logoutAll: async () => {
    try {
      return await api.post('/auth/logout-all')
    } finally {
      Cookies.remove('access_token')
      Cookies.remove('refresh_token')
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
  analyzeImage: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/image', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => e, // can be used for progress bar
    })
  },

  analyzeVideo: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/video', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  analyzeAudio: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return api.post('/analyze/audio', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },

  getHistory: (page = 1, perPage = 10, mediaType?: string) =>
    api.get('/analyze/history', { params: { page, per_page: perPage, media_type: mediaType } }),

  getAnalysis: (id: string) => api.get(`/analyze/${id}`),

  deleteAnalysis: (id: string) => api.delete(`/analyze/${id}`),

  getStats: () => api.get('/analyze/stats'),
}

// ── Reports ───────────────────────────────────────────────────────────────────
export const reportsApi = {
  generate: (analysisId: string) => api.post(`/reports/${analysisId}/generate`),
  get:      (analysisId: string) => api.get(`/reports/${analysisId}`),
  downloadJson: (analysisId: string) =>
    api.get(`/reports/${analysisId}/download/json`, { responseType: 'blob' }),
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
