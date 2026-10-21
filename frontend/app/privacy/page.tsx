import React from 'react'
import Link from 'next/link'
import {
  ShieldCheck,
  Lock,
  Cpu,
  Database,
  Trash2,
  FileText,
  AlertTriangle,
  CheckCircle2,
  ArrowLeft,
  Mail,
  Building,
  Calendar,
  Layers,
  FileKey,
} from 'lucide-react'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

export const metadata = {
  title: 'Privacy Policy — Privacy Eye',
  description: 'Transparent disclosure of data handling, in-memory processing, zero-retention defaults, and user rights.',
}

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-canvas text-white selection:bg-white/25 selection:text-white">
      {/* Background ambient lighting */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-white/[0.025] rounded-full blur-3xl" />
        <div className="absolute top-1/3 -right-40 w-96 h-96 bg-white/[0.02] rounded-full blur-3xl" />
      </div>

      <div className="relative max-w-4xl mx-auto px-4 py-12 sm:px-6 lg:px-8 space-y-12">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between">
          <Link href="/">
            <GlassButton variant="ghost" size="sm" icon={<ArrowLeft className="w-4 h-4" />}>
              Back to Home
            </GlassButton>
          </Link>
          <div className="flex items-center gap-2">
            <GlassBadge status="safe" label="POLICY V1.0.0" />
            <span className="text-xs text-white/40 font-mono">EFFECTIVE: OCT 2026</span>
          </div>
        </div>

        {/* Header */}
        <div className="space-y-4 text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-surface border border-status-safe/30 text-xs font-mono text-status-safe">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Transparent Data Sovereignty Policy</span>
          </div>
          <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white">
            PRIVACY POLICY
          </h1>
          <p className="text-sm md:text-base text-white/60 max-w-2xl leading-relaxed">
            Privacy Eye is architected around the fundamental principle of data minimization. We do not monetize your media, train unauthorized models on your biometric data, or retain unconsented files.
          </p>
        </div>

        {/* Important Notice Callout */}
        <div className="p-6 rounded-3xl bg-white/5 border border-white/15 space-y-2">
          <div className="flex items-center gap-2 text-white font-bold text-sm">
            <Lock className="w-4 h-4 text-white" />
            <span>Zero-Knowledge Default Architecture</span>
          </div>
          <p className="text-xs text-white/80 leading-relaxed">
            By default, uploaded media payloads (images, video streams, audio clips) exist solely in volatile random-access memory (RAM) for the duration of mathematical feature extraction. Immediately upon response dispatch, temporary buffers are cleared and zero raw media bytes are stored on disk.
          </p>
        </div>

        {/* Detailed Sections */}
        <div className="space-y-8 text-sm">
          {/* Section 1 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-white" />
              1. What Data We Collect
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>We strictly limit collection to categories necessary for service operation:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li><strong className="text-white">Account Information:</strong> Email address, cryptographically hashed passwords (Argon2id), optional display name, and assigned account tier.</li>
                <li><strong className="text-white">Transient Media Payloads:</strong> Uploaded images, video clips, and audio files submitted for deepfake and manipulation inspection.</li>
                <li><strong className="text-white">Forensic Telemetry:</strong> SHA-256 cryptographic file hashes, MIME types, file sizes, processing execution duration, and extracted mathematical residuals.</li>
                <li><strong className="text-white">Live Biometric Challenge Data:</strong> Base64 eye-orbit crops and landmark jitter values processed client-side or during active live liveness challenges.</li>
                <li><strong className="text-white">Consent Audit Trails:</strong> Timestamped records of granular consent decisions, policy version acknowledgments, and withdrawal timestamps.</li>
              </ul>
            </div>
          </GlassCard>

          {/* Section 2 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Cpu className="w-5 h-5 text-white/90" />
              2. Why Each Category of Data is Processed
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>Every data processing action is tied to a specific lawful basis and purpose:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li><strong className="text-white">Detection & Forensics:</strong> Necessary to execute requested 2D-FFT noise, error level analysis, temporal consistency, and spectral voice analysis.</li>
                <li><strong className="text-white">Authentication & Account Security:</strong> Necessary to verify access rights, issue JSON Web Tokens, prevent credential stuffing, and isolate multi-tenant data.</li>
                <li><strong className="text-white">Audit History (Optional):</strong> Maintained only when user has granted explicit consent to retain analysis summaries.</li>
                <li><strong className="text-white">Model Improvement (Opt-In Only):</strong> Strictly opt-in; facial or voice samples are added to calibration datasets only with explicit affirmative consent.</li>
              </ul>
            </div>
          </GlassCard>

          {/* Section 3 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Trash2 className="w-5 h-5 text-status-safe" />
              3. Lifecycle of Uploaded Media (Images, Video, Audio)
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>
                When you submit a file for analysis:
              </p>
              <ol className="list-decimal list-inside space-y-1.5 pl-2">
                <li>The payload is received in memory via an encrypted HTTPS connection.</li>
                <li>Format magic bytes and file integrity are validated in memory.</li>
                <li>Forensic and neural classifiers compute spatial, frequency, and temporal residual scores.</li>
                <li>The resulting detection scores and signals are saved to your account report.</li>
                <li><strong className="text-status-safe">Immediate Purge:</strong> The raw media buffer is discarded from memory. If a temporary file was required for video container demuxing, it is unlinked immediately via a guaranteed <code className="text-white bg-white/10 px-1 py-0.5 rounded">try...finally</code> block.</li>
              </ol>
              <p className="font-semibold text-white">
                Under no circumstances does Privacy Eye store raw user images, full video recordings, or voice recordings on permanent disk storage without dedicated, unbundled consent.
              </p>
            </div>
          </GlassCard>

          {/* Section 4 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-white/90" />
              4. Local vs. Server-Side Inference
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>
                <strong className="text-white">Live Scan HUD:</strong> Computer vision checks (such as YuNet facial detection, EAR eye blink tracking, and 2D-FFT Moiré screen detection) run inside your browser session or on the dedicated backend instance depending on your selected processing mode.
              </p>
              <p>
                <strong className="text-white">Media Ingestion Pipeline:</strong> Large media files (up to 500MB) are processed by our private FastAPI backend instance. Your media is <strong className="text-white">never</strong> shared with public third-party generative AI providers (such as OpenAI, Google Gemini, or Anthropic) for detection unless you explicitly enable third-party cloud acceleration.
              </p>
            </div>
          </GlassCard>

          {/* Section 5 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <FileKey className="w-5 h-5 text-status-warning" />
              5. Cookies, Tokens, and Session Storage
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>We use strictly functional security tokens:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li><strong className="text-white">access_token:</strong> Short-lived JWT access token verifying API authorization.</li>
                <li><strong className="text-white">refresh_token:</strong> Secure token used for transparent session rotation without requiring re-authentication.</li>
                <li><strong className="text-white">csrf_token:</strong> Double-submit cryptographic token preventing cross-site request forgery attacks.</li>
              </ul>
              <p>We do not use third-party advertising trackers, cross-site beacons, or commercial retargeting cookies.</p>
            </div>
          </GlassCard>

          {/* Section 6 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-white" />
              6. Your Legal Rights & Data Sovereignty
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>In accordance with GDPR, CCPA, and global privacy standards, you maintain absolute control over your records:</p>
              <ul className="list-disc list-inside space-y-1.5 pl-2">
                <li><strong className="text-white">Right of Access (Article 15):</strong> Download your full forensic archive in structured JSON format at any time from the Privacy Center.</li>
                <li><strong className="text-white">Right to Erasure (Article 17):</strong> Purge individual analysis records or permanently delete your entire user account and all cascaded audit trails with one click.</li>
                <li><strong className="text-white">Right to Withdraw Consent:</strong> You may toggle off optional purposes (history saving, model improvement, telemetry) at any time. Changes take effect immediately for all subsequent processing.</li>
              </ul>
            </div>
          </GlassCard>

          {/* Section 7 */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-status-warning" />
              7. Algorithmic Nature & Limitation Disclosures
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>
                Privacy Eye provides <strong className="text-white">probabilistic forensic assessments</strong>. Machine learning models and signal processing heuristics evaluate statistical patterns; they do not represent absolute, infallible legal proofs of authenticity or forgery.
              </p>
              <p>
                Downsampling, extreme lossy re-encoding (e.g., social media compression), optical lens blur, or atypical lighting conditions can affect confidence scores. Always corroborate findings with human domain expertise.
              </p>
            </div>
          </GlassCard>

          {/* Section 8: Legal Entity & Contact */}
          <GlassCard variant="elevated" className="p-6 md:p-8 space-y-4 border border-white/10">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Building className="w-5 h-5 text-white/70" />
              8. Contact Details & Legal Entity
            </h2>
            <div className="space-y-3 text-white/70 leading-relaxed text-xs">
              <p>
                For privacy inquiries, data subject access requests, or regulatory questions, contact our designated privacy officer:
              </p>
              <div className="p-4 rounded-2xl bg-white/4 border border-white/6 space-y-2 font-mono">
                <div className="flex items-center gap-2">
                  <Mail className="w-4 h-4 text-white" />
                  <span>Email: privacy@privacyeye.ai</span>
                </div>
                <div className="flex items-center gap-2">
                  <Building className="w-4 h-4 text-white/80" />
                  <span>Entity: [LEGAL_ENTITY_NAME] (Requires User Legal Registration Input)</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-status-safe" />
                  <span>Version: 1.0.0-prototype · Effective Date: October 19, 2026</span>
                </div>
              </div>
              <p className="text-[11px] text-white/40 italic">
                Notice: Specific corporate registration numbers, physical headquarters address, and appointed Data Protection Officer credentials will be updated upon final formal corporate filing prior to public production deployment.
              </p>
            </div>
          </GlassCard>
        </div>

        {/* Footer Navigation */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-8 border-t border-white/8 text-xs text-white/50">
          <p>© 2026 Privacy Eye Platform. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <Link href="/dashboard/privacy" className="hover:text-white transition-colors">
              Privacy Sovereignty Center
            </Link>
            <span>·</span>
            <Link href="/auth/register" className="hover:text-white transition-colors">
              Account Registration
            </Link>
            <span>·</span>
            <Link href="/" className="hover:text-white transition-colors">
              Platform Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
