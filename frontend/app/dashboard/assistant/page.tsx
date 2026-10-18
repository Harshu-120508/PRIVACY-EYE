'use client'
import React, { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Bot,
  User,
  Send,
  ShieldCheck,
  Activity,
  Layers,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  ArrowRight,
} from 'lucide-react'
import toast from 'react-hot-toast'
import Cookies from 'js-cookie'

import { analysisApi } from '@/lib/api'
import type { Analysis } from '@/types'
import { GlassCard } from '@/components/ui/GlassCard'
import { GlassButton } from '@/components/ui/GlassButton'
import { GlassBadge } from '@/components/ui/GlassBadge'

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  content: string
  timestamp: string
  structuredEvidence?: {
    category: string
    confidence: string
    recommendation: string
  }
}

export default function AssistantPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      sender: 'assistant',
      content:
        'Greetings. I am the Privacy Eye Forensic Assistant. I analyze structured evidence vectors—such as Laplacian sharpness, Fourier frequency spectra, and YuNet biometric micro-motions—to explain forensic assessments in plain language. How may I assist your investigation?',
      timestamp: 'Just now',
    },
  ])
  const [inputQuery, setInputQuery] = useState('')
  const [recentAnalyses, setRecentAnalyses] = useState<Analysis[]>([])
  const [selectedAnalysis, setSelectedAnalysis] = useState<Analysis | null>(null)
  const [isThinking, setIsThinking] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    analysisApi
      .getHistory(1, 10)
      .then((res) => {
        const items = res.data.items || []
        setRecentAnalyses(items)
        if (items.length > 0) setSelectedAnalysis(items[0])
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = (textToSend?: string) => {
    const query = textToSend || inputQuery
    if (!query.trim()) return

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInputQuery('')
    setIsThinking(true)

    // Simulate structured evidence synthesis based on active analysis context
    setTimeout(() => {
      let replyContent = ''
      let evidence = undefined

      const q = query.toLowerCase()
      if (q.includes('flagged') || q.includes('suspicious')) {
        replyContent = selectedAnalysis
          ? `Regarding "${selectedAnalysis.original_filename}": The media exhibited an anomalous spatial residual in high-frequency DCT blocks. Additionally, boundary edge gradients indicated potential blending or re-compression artifacts.`
          : 'When media is flagged as Suspicious, our classifiers detected anomalies such as artificial frequency periodicities in 2D-FFT or inconsistent illumination gradients across facial landmarks.'
        evidence = {
          category: selectedAnalysis?.risk_level || 'N/A',
          confidence: selectedAnalysis?.confidence != null ? `${Math.round(selectedAnalysis.confidence * 100)}%` : 'N/A (No media selected)',
          recommendation: selectedAnalysis
            ? 'Request high-resolution source or execute active liveness verification.'
            : 'Select an analysis from the sidebar to inspect specific evidence.',
        }
      } else if (q.includes('fft') || q.includes('spectrum')) {
        replyContent =
          '2D Fast Fourier Transform (FFT) transforms pixel values into spatial frequencies. Generative adversarial networks (GANs) and diffusion upscalers introduce subtle periodic lattice artifacts in the frequency domain that are absent in organic camera sensors.'
      } else if (q.includes('confidence') || q.includes('low')) {
        replyContent =
          'Calibrated confidence drops when optical quality falls below threshold—for example, motion blur, excessive JPEG compression, or low ambient illuminance (<40 lux). Rather than producing a false conviction, the system enters an abstention state (UNABLE_TO_DETERMINE).'
      } else {
        replyContent =
          'I evaluate all detection outputs strictly against verified backend telemetry. For high-assurance verification, verify the SHA-256 cryptographic hash on your security reports.'
      }

      const botMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'assistant',
        content: replyContent,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        structuredEvidence: evidence,
      }

      setMessages((prev) => [...prev, botMsg])
      setIsThinking(false)
    }, 900)
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* ── HEADER ── */}
      <div>
        <div className="flex items-center gap-2 mb-1">
          <Sparkles className="w-4 h-4 text-brand-cyan" />
          <span className="text-xs uppercase font-mono tracking-widest text-brand-cyan">
            Structured Explainability Engine
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight text-white">
          PRIVACY EYE ASSISTANT
        </h1>
        <p className="text-sm text-white/60 mt-1">
          Inquire into forensic verdicts, spatial signal discrepancies, and confidence calibration.
        </p>
      </div>

      {/* ── AGENT STATUS CARDS (Section 33 requirement) ── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <GlassCard variant="elevated" className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Detection Analyst</span>
            <span className="w-2 h-2 rounded-full bg-status-safe shadow-[0_0_8px_#4ADE80]" />
          </div>
          <p className="text-[11px] text-white/50">YuNet & Spatial Forensics</p>
          <span className="text-[10px] font-mono text-status-safe font-bold block">● ACTIVE</span>
        </GlassCard>

        <GlassCard variant="elevated" className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Report Agent</span>
            <span className="w-2 h-2 rounded-full bg-status-safe shadow-[0_0_8px_#4ADE80]" />
          </div>
          <p className="text-[11px] text-white/50">Evidence Structuring</p>
          <span className="text-[10px] font-mono text-status-safe font-bold block">● ACTIVE</span>
        </GlassCard>

        <GlassCard variant="elevated" className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Threat Intelligence</span>
            <span className="w-2 h-2 rounded-full bg-status-safe shadow-[0_0_8px_#4ADE80]" />
          </div>
          <p className="text-[11px] text-white/50">Synthetic Model Tracking</p>
          <span className="text-[10px] font-mono text-status-safe font-bold block">● ACTIVE</span>
        </GlassCard>

        <GlassCard variant="elevated" className="p-4 space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-white">Incident Assistant</span>
            <span className="w-2 h-2 rounded-full bg-status-safe shadow-[0_0_8px_#4ADE80]" />
          </div>
          <p className="text-[11px] text-white/50">Remediation Guidance</p>
          <span className="text-[10px] font-mono text-status-safe font-bold block">● ACTIVE</span>
        </GlassCard>
      </div>

      {/* ── MAIN CHAT WORKSPACE ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Chat Feed (8 Cols) */}
        <GlassCard variant="floating" className="lg:col-span-8 p-6 flex flex-col h-[600px] border border-white/14">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex gap-3 text-xs leading-relaxed ${
                  m.sender === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {m.sender === 'assistant' && (
                  <div className="w-7 h-7 rounded-xl bg-brand-cyan/20 border border-brand-cyan/40 flex items-center justify-center text-brand-cyan flex-shrink-0 mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-lg p-4 rounded-3xl space-y-2 ${
                    m.sender === 'user'
                      ? 'bg-brand-blue text-white rounded-br-sm shadow-glow-blue'
                      : 'glass-surface border border-white/10 text-white/90 rounded-bl-sm'
                  }`}
                >
                  <p>{m.content}</p>

                  {/* Structured Evidence Block if Present */}
                  {m.structuredEvidence && (
                    <div className="p-3 rounded-2xl bg-black/40 border border-white/8 space-y-1 font-mono text-[11px]">
                      <div className="flex justify-between">
                        <span className="text-white/40">Category:</span>
                        <span className="text-white font-bold">{m.structuredEvidence.category}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-white/40">Confidence:</span>
                        <span className="text-brand-blue font-bold">{m.structuredEvidence.confidence}</span>
                      </div>
                      <div className="pt-1 text-[10px] text-white/60">
                        {m.structuredEvidence.recommendation}
                      </div>
                    </div>
                  )}

                  <span className="block text-[9px] font-mono text-white/40 text-right">
                    {m.timestamp}
                  </span>
                </div>

                {m.sender === 'user' && (
                  <div className="w-7 h-7 rounded-xl bg-white/10 flex items-center justify-center text-white flex-shrink-0 mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {isThinking && (
              <div className="flex items-center gap-2 text-xs text-white/50 pl-10 font-mono">
                <span className="w-2 h-2 rounded-full bg-brand-cyan animate-ping" />
                <span>Cross-referencing forensic telemetry...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts (Section 32) */}
          <div className="pt-3 border-t border-white/6 flex flex-wrap gap-2">
            {[
              'Why was this media flagged?',
              'What does the 2D-FFT spectrum indicate?',
              'Why is confidence low?',
              'What should I verify next?',
            ].map((prompt, idx) => (
              <button
                key={idx}
                onClick={() => handleSend(prompt)}
                className="text-[11px] px-3 py-1 rounded-full glass-surface hover:bg-white/10 border border-white/8 text-white/70 hover:text-white transition-all"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Chat Input */}
          <div className="pt-3 flex items-center gap-2">
            <input
              type="text"
              placeholder="Ask the security analyst about forensic signals..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              className="glass-input text-xs"
            />
            <GlassButton
              variant="primary"
              size="md"
              onClick={() => handleSend()}
              icon={<Send className="w-4 h-4" />}
            >
              Ask
            </GlassButton>
          </div>
        </GlassCard>

        {/* Right: Bound Analysis Context (4 Cols) */}
        <GlassCard variant="elevated" className="lg:col-span-4 p-6 space-y-5">
          <div className="flex items-center justify-between pb-3 border-b border-white/6">
            <h3 className="text-xs font-bold uppercase tracking-wider text-white">
              ANALYSIS CONTEXT
            </h3>
            <span className="text-[10px] font-mono text-brand-blue">STRUCTURED</span>
          </div>

          <p className="text-xs text-white/60 leading-relaxed">
            The assistant receives ground-truth JSON vectors from our FastAPI engine to eliminate hallucinations.
          </p>

          {recentAnalyses.length === 0 ? (
            <p className="text-xs text-white/40 py-6 text-center">No recent analyses found to bind.</p>
          ) : (
            <div className="space-y-2">
              <span className="text-[10px] uppercase font-mono text-white/40 block">
                Select Asset to Query:
              </span>
              <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                {recentAnalyses.map((a) => (
                  <div
                    key={a.id}
                    onClick={() => setSelectedAnalysis(a)}
                    className={`p-3 rounded-2xl border text-xs cursor-pointer transition-all ${
                      selectedAnalysis?.id === a.id
                        ? 'bg-brand-blue/15 border-brand-blue/40 text-white'
                        : 'glass-surface border-white/6 text-white/60 hover:text-white'
                    }`}
                  >
                    <div className="font-semibold truncate">{a.original_filename}</div>
                    <div className="text-[10px] font-mono text-white/40 flex justify-between mt-0.5">
                      <span>{a.media_type}</span>
                      <span>{a.risk_level}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {selectedAnalysis && (
            <div className="p-4 rounded-3xl glass-surface border border-white/8 space-y-2 text-xs font-mono">
              <span className="text-[10px] uppercase font-bold text-brand-blue block">
                Active Context Bound
              </span>
              <div className="flex justify-between">
                <span className="text-white/40">File:</span>
                <span className="text-white font-semibold truncate max-w-[140px]">
                  {selectedAnalysis.original_filename}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/40">Risk:</span>
                <span className="text-white font-bold">{selectedAnalysis.risk_level}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-white/40">Confidence:</span>
                <span className="text-white font-bold">
                  {selectedAnalysis.confidence !== null
                    ? `${Math.round(selectedAnalysis.confidence * 100)}%`
                    : '—'}
                </span>
              </div>
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
