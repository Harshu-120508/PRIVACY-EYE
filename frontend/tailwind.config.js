/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        canvas: {
          DEFAULT: '#000000',
          surface: '#050505',
          card: '#0A0A0A',
          border: 'rgba(255, 255, 255, 0.12)',
        },
        brand: {
          blue: '#FFFFFF',
          violet: '#D4D4D8',
          cyan: '#E4E4E7',
          glow: 'rgba(255, 255, 255, 0.20)',
          dark: '#000000',
        },
        status: {
          safe: '#4ADE80',
          warning: '#FBBF24',
          danger: '#FB7185',
          undetermined: '#94A3B8',
        },
      },
      borderRadius: {
        '2xl': '18px',
        '3xl': '24px',
        '4xl': '28px',
      },
      backdropBlur: {
        xs: '4px',
        sm: '8px',
        md: '12px',
        lg: '16px',
        xl: '20px',
        '2xl': '28px',
      },
      boxShadow: {
        glass: '0 10px 30px -10px rgba(0, 0, 0, 0.85)',
        'glass-hover': '0 16px 40px -10px rgba(0, 0, 0, 0.95), 0 0 24px rgba(255, 255, 255, 0.08)',
        'glass-floating': '0 24px 64px rgba(0, 0, 0, 0.95), 0 0 32px rgba(255, 255, 255, 0.06)',
        'glow-blue': '0 0 35px rgba(255, 255, 255, 0.22)',
        'glow-violet': '0 0 35px rgba(212, 212, 216, 0.18)',
        'glow-safe': '0 0 30px rgba(74, 222, 128, 0.25)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-vertical': 'scanVertical 3s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
      },
      keyframes: {
        scanVertical: {
          '0%, 100%': { transform: 'translateY(0%)', opacity: '0.1' },
          '50%': { transform: 'translateY(100%)', opacity: '0.6' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
      },
    },
  },
  plugins: [],
}
