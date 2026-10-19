/** Shared TypeScript types for the Privacy Eye frontend. */

export type RiskLevel = 'LOW' | 'SUSPICIOUS' | 'HIGH' | 'CRITICAL' | 'UNDETERMINED'
export type MediaType  = 'IMAGE' | 'VIDEO' | 'AUDIO'
export type AnalysisStatus = 'PENDING' | 'PROCESSING' | 'COMPLETE' | 'FAILED' | 'UNSUPPORTED'

export interface Signal {
  signal_key:   string
  signal_label: string
  severity:     'low' | 'medium' | 'high'
  score:        number | null
  description:  string | null
}

export interface Analysis {
  id:                   string
  original_filename:    string
  media_type:           MediaType
  file_size_bytes:      number
  file_sha256:          string | null
  mime_type:            string | null
  duration_seconds:     number | null
  status:               AnalysisStatus
  risk_level:           RiskLevel | null
  synthetic_probability: number | null
  confidence:           number | null
  model_id?:            string | null
  model_version?:       string | null
  prediction?:          string | null
  limitations?:         string | null
  error_code?:          string | null
  explanation:          string | null
  signals:              Signal[]
  raw_scores:           Record<string, unknown> | null
  provenance_info:      Record<string, unknown> | null
  media_deleted:        boolean
  processing_ms:        number | null
  created_at:           string
  updated_at:           string
}

export type ConsentPurpose =
  | 'MEDIA_PROCESSING'
  | 'SAVE_HISTORY'
  | 'RETAIN_MEDIA'
  | 'EXTERNAL_AI_SHARING'
  | 'MODEL_TRAINING'
  | 'ANALYTICS'

export interface ConsentItem {
  purpose: ConsentPurpose
  granted: boolean
  policy_version: string
  granted_at?: string | null
  withdrawn_at?: string | null
}

export interface UserConsentListResponse {
  consents: ConsentItem[]
  policy_version: string
}

export interface AnalysisListResponse {
  items:    Analysis[]
  total:    number
  page:     number
  per_page: number
}

export interface DashboardStats {
  total_scanned:     number
  suspicious:        number
  low_risk:          number
  high_risk:         number
  critical:          number
  undetermined:      number
  scans_this_month:  number
  scans_limit:       number
}

export interface User {
  id:                    string
  email:                 string
  full_name:             string | null
  role:                  string
  is_verified:           boolean
  is_active?:            boolean
  scans_used_this_month: number
  scans_limit:           number
  created_at:            string
}

export interface Report {
  id:              string
  analysis_id:     string
  title:           string
  summary:         string | null
  recommendations: string | null
  report_json:     Record<string, unknown> | null
  created_at:      string
}

export const RISK_CONFIG: Record<RiskLevel, { label: string; emoji: string; className: string; color: string }> = {
  LOW:          { label: 'Low Risk',          emoji: '🟢', className: 'risk-low',          color: '#10b981' },
  SUSPICIOUS:   { label: 'Suspicious',        emoji: '🟡', className: 'risk-suspicious',   color: '#f59e0b' },
  HIGH:         { label: 'High Risk',         emoji: '🟠', className: 'risk-high',         color: '#f97316' },
  CRITICAL:     { label: 'Critical',          emoji: '🔴', className: 'risk-critical',     color: '#ef4444' },
  UNDETERMINED: { label: 'Unable to Determine', emoji: '⚪', className: 'risk-undetermined', color: '#6b7280' },
}

export const MEDIA_TYPE_CONFIG: Record<MediaType, { label: string; accept: Record<string, string[]>; maxMB: number }> = {
  IMAGE: { label: 'Image', accept: { 'image/jpeg': ['.jpg','.jpeg'], 'image/png': ['.png'], 'image/webp': ['.webp'] }, maxMB: 20  },
  VIDEO: { label: 'Video', accept: { 'video/mp4': ['.mp4'], 'video/quicktime': ['.mov'], 'video/webm': ['.webm'] },       maxMB: 500 },
  AUDIO: { label: 'Audio', accept: { 'audio/mpeg': ['.mp3'], 'audio/wav': ['.wav'], 'audio/ogg': ['.ogg'], 'audio/flac': ['.flac'] }, maxMB: 50 },
}
