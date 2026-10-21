import type { Metadata } from 'next'
import './globals.css'
import { Toaster } from 'react-hot-toast'
import { AmbientBackground } from '@/components/layout/AmbientBackground'
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: { default: 'Privacy Eye — See Through The Fake', template: '%s | Privacy Eye' },
  description: 'AI-powered digital authenticity and deepfake protection. Real-time multi-signal biometric and forensic inference.',
  keywords: ['deepfake detection', 'AI authenticity', 'live liveness verification', 'synthetic media', 'cybersecurity'],
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-canvas text-white font-sans antialiased selection:bg-white/25 selection:text-white">
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
              background: 'rgba(10, 10, 10, 0.92)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              color: '#FFFFFF',
              border: '1px solid rgba(255, 255, 255, 0.14)',
              borderRadius: '16px',
              fontSize: '13px',
              fontWeight: '500',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.85)',
            },
            success: { iconTheme: { primary: '#4ADE80', secondary: '#000000' } },
            error: { iconTheme: { primary: '#FB7185', secondary: '#000000' } },
          }}
        />
      </body>
    </html>
  )
}
