'use client'
import React, { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  UploadCloud,
  Image as ImageIcon,
  Video,
  Music,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Sparkles,
  ArrowRight,
  Shield,
  Activity,
  Layers,
  Cpu,
} from 'lucide-react'
import toast from 'react-hot-toast'

import { analysisApi, getErrorMessage } from '@/lib/api'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'
import { GlassTabs } from '@/components/ui/GlassTabs'

type MediaTypeTab = 'IMAGE' | 'VIDEO' | 'AUDIO'

const MEDIA_CONFIG: Record<
  MediaTypeTab,
  {
    label: string
    icon: React.ElementType
    accept: Record<string, string[]>
    maxMB: number
    description: string
  }
> = {
  IMAGE: {
    label: 'Image',
    icon: ImageIcon,
    accept: { 'image/jpeg': ['.jpg', '.jpeg'], 'image/png': ['.png'], 'image/webp': ['.webp'] },
    maxMB: 20,
    description: 'JPEG, PNG, WebP up to 20MB. Analyzes ELA, 2D-FFT noise, EXIF metadata, and boundary seams.',
  },
  VIDEO: {
    label: 'Video',
    icon: Video,
    accept: { 'video/mp4': ['.mp4'], 'video/quicktime': ['.mov'], 'video/webm': ['.webm'] },
    maxMB: 500,
    description: 'MP4, MOV, WebM up to 500MB. Evaluates temporal frame continuity, facial warping, and compression artifacts.',
  },
  AUDIO: {
    label: 'Audio',
    icon: Music,
    accept: {
      'audio/mpeg': ['.mp3'],
      'audio/wav': ['.wav'],
      'audio/ogg': ['.ogg'],
      'audio/flac': ['.flac'],
    },
    maxMB: 50,
    description: 'MP3, WAV, OGG, FLAC up to 50MB. Inspects Mel-spectrogram variance, synthetic pitch, and vocoder artifacts.',
  },
}

export default function AnalyzeMediaPage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<MediaTypeTab>('IMAGE')
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadPercent, setUploadPercent] = useState(0)
  const [processingState, setProcessingState] = useState<'uploading' | 'inferring' | 'complete' | 'failed'>('uploading')
  const [statusMessage, setStatusMessage] = useState('Preparing media for upload...')
  const abortControllerRef = useRef<AbortController | null>(null)

  // Clean up in-flight requests and timers on component unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const config = MEDIA_CONFIG[activeTab]

  const onDrop = (acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0]
      if (file.size > config.maxMB * 1024 * 1024) {
        toast.error(`File exceeds maximum size of ${config.maxMB}MB`)
        return
      }
      setSelectedFile(file)
    }
  }

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: config.accept,
    multiple: false,
    disabled: isUploading,
  })

  const cancelAnalysis = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      abortControllerRef.current = null
    }
    setIsUploading(false)
    setProcessingState('uploading')
    setUploadPercent(0)
    toast.error('Analysis ingestion cancelled')
  }

  const runAnalysis = async () => {
    if (!selectedFile) return
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    abortControllerRef.current = new AbortController()

    setIsUploading(true)
    setUploadPercent(0)
    setProcessingState('uploading')
    setStatusMessage(`Uploading ${selectedFile.name}...`)

    const handleProgress = (percent: number) => {
      setUploadPercent(percent)
      if (percent < 100) {
        setStatusMessage(`Uploading payload (${percent}%)...`)
      } else {
        setProcessingState('inferring')
        setStatusMessage('Payload received. Running forensic & neural model inference...')
      }
    }

    try {
      let res
      if (activeTab === 'IMAGE') {
        res = await analysisApi.analyzeImage(selectedFile, handleProgress)
      } else if (activeTab === 'VIDEO') {
        res = await analysisApi.analyzeVideo(selectedFile, handleProgress)
      } else {
        res = await analysisApi.analyzeAudio(selectedFile, handleProgress)
      }

      setProcessingState('complete')
      setStatusMessage('Inference verified. Loading audit report...')
      toast.success('Analysis complete!')
      router.push(`/dashboard/analysis/${res.data.id}`)
    } catch (err: any) {
      if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
        return
      }
      setProcessingState('failed')
      setIsUploading(false)
      toast.error(getErrorMessage(err))
    }
  }

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      {/* ── HEADER ── */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full glass-surface border border-white/10 text-xs font-mono text-brand-blue mb-2">
          <Activity className="w-3.5 h-3.5" />
          <span>Forensic Media Ingestion</span>
        </div>
        <h1 className="text-3xl md:text-5xl font-black tracking-tight text-white">
          ANALYZE MEDIA
        </h1>
        <p className="text-sm text-white/60 max-w-lg mx-auto">
          Upload media to detect deepfakes, face swaps, GAN synthesis artifacts, voice cloning, and tampering.
        </p>
      </div>

      {/* ── TABS ── */}
      <div className="flex justify-center">
        <GlassTabs
          tabs={[
            { id: 'IMAGE', label: 'Image Forensics', icon: <ImageIcon className="w-3.5 h-3.5" /> },
            { id: 'VIDEO', label: 'Video Analysis', icon: <Video className="w-3.5 h-3.5" /> },
            { id: 'AUDIO', label: 'Audio / Voice', icon: <Music className="w-3.5 h-3.5" /> },
          ]}
          activeTab={activeTab}
          onChange={(tab) => {
            setActiveTab(tab as MediaTypeTab)
            setSelectedFile(null)
          }}
        />
      </div>

      {/* ── DROPZONE / SCANNER CONTAINER ── */}
      <GlassCard variant="elevated" className="p-8 md:p-12 relative overflow-hidden">
        {isUploading ? (
          /* Truthful Forensic & Neural Ingestion Progress */
          <div className="py-12 flex flex-col items-center justify-center text-center space-y-6">
            <div className="relative w-28 h-28 flex items-center justify-center">
              {/* Outer pulsing ring */}
              <div className="absolute inset-0 rounded-full border border-brand-blue/30 animate-ping opacity-60" />
              <div className="absolute inset-2 rounded-full border border-brand-violet/40 animate-spin" />
              {/* Center icon */}
              <div className="w-16 h-16 rounded-3xl glass-card flex items-center justify-center border border-white/20 shadow-glow-blue">
                <Sparkles className="w-7 h-7 text-brand-blue animate-pulse" />
              </div>
            </div>

            <div className="space-y-2 max-w-md">
              <span className="text-xs font-mono uppercase tracking-widest text-brand-blue">
                {processingState === 'uploading' ? 'Ingesting Media Buffer' : 'Running Forensic & Neural Classifiers'}
              </span>
              <h3 className="text-lg font-bold text-white transition-all duration-300">
                {statusMessage}
              </h3>
              <p className="text-xs text-white/40 font-mono">
                {processingState === 'uploading'
                  ? `Upload progress: ${uploadPercent}%`
                  : 'Backend pipeline executing · Memory buffer only'}
              </p>
            </div>

            {/* Real Progress Bar & Indeterminate Inference Indicator */}
            <div className="w-full max-w-sm h-1.5 bg-white/10 rounded-full overflow-hidden">
              <div
                className={`h-full bg-gradient-to-r from-brand-blue to-brand-violet rounded-full transition-all duration-300 ease-out ${
                  processingState === 'inferring' ? 'animate-pulse w-full' : ''
                }`}
                style={{ width: processingState === 'uploading' ? `${Math.max(uploadPercent, 5)}%` : '100%' }}
              />
            </div>

            <button
              type="button"
              onClick={cancelAnalysis}
              className="text-xs text-white/40 hover:text-white underline underline-offset-4 transition-colors"
            >
              Cancel Ingestion
            </button>
          </div>
        ) : (
          /* Drag and Drop Zone */
          <div className="space-y-6">
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-3xl p-10 md:p-14 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center gap-4 ${
                isDragActive
                  ? 'border-brand-blue bg-brand-blue/10 scale-[0.99]'
                  : 'border-white/14 hover:border-white/30 bg-white/[0.02]'
              }`}
            >
              <input {...getInputProps()} />

              <div className="w-16 h-16 rounded-3xl glass-surface border border-white/15 flex items-center justify-center text-brand-blue shadow-glass">
                <UploadCloud className="w-8 h-8" />
              </div>

              <div className="space-y-1">
                <p className="text-base font-semibold text-white">
                  Drop your {config.label.toLowerCase()} here, or{' '}
                  <span className="text-brand-blue underline underline-offset-4">browse files</span>
                </p>
                <p className="text-xs text-white/50">{config.description}</p>
              </div>

              {selectedFile && (
                <div className="mt-2 px-4 py-2 rounded-2xl glass-floating border border-brand-blue/30 text-xs font-mono text-white flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-status-safe" />
                  <span className="font-semibold">{selectedFile.name}</span>
                  <span className="text-white/40">
                    ({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
              )}
            </div>

            {/* Action Bar */}
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
              <div className="flex items-center gap-2 text-xs text-white/50">
                <Shield className="w-4 h-4 text-status-safe" />
                <span>Files are processed in memory and never retained without consent</span>
              </div>

              <GlassButton
                variant="primary"
                size="lg"
                onClick={runAnalysis}
                disabled={!selectedFile}
                className="w-full sm:w-auto shadow-glow-blue"
                icon={<Sparkles className="w-4 h-4" />}
              >
                Start In-Depth Analysis
              </GlassButton>
            </div>
          </div>
        )}
      </GlassCard>

      {/* ── FORENSIC TECHNIQUES OVERVIEW ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
        <GlassCard variant="base" className="p-4 space-y-1.5">
          <span className="font-bold text-white block">Error Level Analysis (ELA)</span>
          <p className="text-white/60 leading-relaxed">
            Re-compresses high-frequency DCT blocks to identify spliced boundaries and composite layers.
          </p>
        </GlassCard>

        <GlassCard variant="base" className="p-4 space-y-1.5">
          <span className="font-bold text-white block">2D-FFT Spectral Noise</span>
          <p className="text-white/60 leading-relaxed">
            Transforms pixels into 2D spatial frequencies to detect GAN generator grid periodicities.
          </p>
        </GlassCard>

        <GlassCard variant="base" className="p-4 space-y-1.5">
          <span className="font-bold text-white block">EXIF & Provenance Hashes</span>
          <p className="text-white/60 leading-relaxed">
            Parses camera hardware metadata, quantization tables, and C2PA cryptographic provenance.
          </p>
        </GlassCard>
      </div>
    </div>
  )
}
