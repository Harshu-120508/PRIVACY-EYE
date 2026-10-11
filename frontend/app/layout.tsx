import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { AmbientBackground } from '@/components/layout/AmbientBackground'
import { AuthProvider } from '@/contexts/AuthContext'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-sans',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: { default: 'Privacy Eye — See Through The Fake', template: '%s | Privacy Eye' },
  description: 'AI-powered digital authenticity and deepfake protection. Real-time multi-signal biometric and forensic inference.',
  keywords: ['deepfake detection', 'AI authenticity', 'live liveness verification', 'synthetic media', 'cybersecurity'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="bg-canvas text-white font-sans antialiased selection:bg-brand-cyan/30 selection:text-white">
        <AmbientBackground />
        <AuthProvider>
          <div className="relative z-10 min-h-screen flex flex-col">
            {children}
          </div>
        </AuthProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            style: {
              background: 'rgba(13, 17, 28, 0.85)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.12)',
              borderRadius: '16px',
              fontSize: '13px',
              fontWeight: '500',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            },
            success: { iconTheme: { primary: '#4ADE80', secondary: '#05070D' } },
            error: { iconTheme: { primary: '#FB7185', secondary: '#05070D' } },
          }}
        />
      </body>
    </html>
  )
}
