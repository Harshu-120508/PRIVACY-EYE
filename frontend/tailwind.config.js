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
          card: '#080808',
          border: 'rgba(255, 255, 255, 0.08)',
        },
        brand: {
          cyan: '#13D2E8',
          violet: '#C010ED',
          glow: 'rgba(19, 210, 232, 0.22)',
        },
        status: {
          safe: '#13D2E8',
          warning: '#C010ED',
          danger: '#F90202',
          undetermined: 'rgba(255, 255, 255, 0.40)',
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
        glass: '0 10px 30px -10px rgba(0, 0, 0, 0.8)',
        'glass-hover': '0 16px 40px -10px rgba(0, 0, 0, 0.9), 0 0 24px rgba(19, 210, 232, 0.12)',
        'glass-floating': '0 24px 64px rgba(0, 0, 0, 0.9), 0 0 32px rgba(19, 210, 232, 0.1)',
        'glow-blue': '0 0 35px rgba(19, 210, 232, 0.28)',
        'glow-violet': '0 0 35px rgba(192, 16, 237, 0.25)',
        'glow-safe': '0 0 30px rgba(19, 210, 232, 0.25)',
      },
      fontFamily: {
        sans: ['var(--font-sans)', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['var(--font-mono)', 'JetBrains Mono', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'scan-vertical': 'scanVertical 3s ease-in-out infinite',
        float: 'float 6s ease-in-out infinite',
      },
      keyframes: {
        scanVertical: {
          '0%, 100%': { transform: 'translateY(0%)', opacity: '0.2' },
          '50%': { transform: 'translateY(100%)', opacity: '0.85' },
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
