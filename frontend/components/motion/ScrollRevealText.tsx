'use client'
import React, { useRef } from 'react'
import { motion, useScroll, useTransform, useReducedMotion, type MotionValue } from 'framer-motion'

interface WordProps {
  word: string
  index: number
  total: number
  progress: MotionValue<number>
  highlight: boolean
  reduced: boolean | null
}

function RevealWord({ word, index, total, progress, highlight, reduced }: WordProps) {
  const start = Math.max(0, index / total - 0.1)
  const end = Math.min(1, index / total + 0.06)
  const opacity = useTransform(progress, [start, end], [0.16, 1])

  return (
    <motion.span
      style={reduced ? { opacity: 1 } : { opacity }}
      className={highlight ? 'text-white font-semibold' : 'text-white/85'}
    >
      {word}{' '}
    </motion.span>
  )
}

interface ScrollRevealTextProps {
  text: string
  highlightWords?: string[]
  className?: string
}

/**
 * MotionSites Scroll-Linked Word-by-Word Opacity Reveal.
 * Words light up from 16% to 100% opacity synced to viewport scroll progress.
 */
export const ScrollRevealText: React.FC<ScrollRevealTextProps> = ({
  text,
  highlightWords = [],
  className = '',
}) => {
  const containerRef = useRef<HTMLParagraphElement>(null)
  const shouldReduceMotion = useReducedMotion()

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 0.88', 'end 0.42'],
  })

  const words = text.trim().split(/\s+/)
  const highlightSet = new Set(highlightWords.map((w) => w.toLowerCase()))

  return (
    <p ref={containerRef} className={className}>
      {words.map((word, idx) => {
        const clean = word.toLowerCase().replace(/[.,!?;:]/g, '')
        return (
          <RevealWord
            key={`${idx}-${word}`}
            word={word}
            index={idx}
            total={words.length}
            progress={scrollYProgress}
            highlight={highlightSet.has(clean)}
            reduced={shouldReduceMotion}
          />
        )
      })}
    </p>
  )
}
