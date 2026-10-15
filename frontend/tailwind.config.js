/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      colors: {
        surface: {
          50:  '#ffffff',
          100: '#f8f9fc',
          200: '#f1f3f8',
          300: '#e8ebf4',
          400: '#dde1ef',
          500: '#c8cedf',
          600: '#a0a8c0',
          700: '#6b7494',
        },
        accent: {
          DEFAULT: '#4f46e5',
          light:   '#6366f1',
          dark:    '#3730a3',
          glow:    'rgba(79,70,229,0.15)',
        },
        brand: {
          50:  '#eef2ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          500: '#6366f1',
          600: '#4f46e5',
          700: '#4338ca',
        },
      },
      boxShadow: {
        'glow-accent':  '0 0 20px rgba(79,70,229,0.2)',
        'glow-sm':      '0 0 8px rgba(79,70,229,0.12)',
        'card':         '0 2px 16px rgba(0,0,0,0.08)',
        'card-hover':   '0 8px 32px rgba(0,0,0,0.12)',
        'soft':         '0 1px 4px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.06)',
      },
      animation: {
        'fade-in':    'fadeIn 0.3s ease-out',
        'slide-up':   'slideUp 0.35s ease-out',
        'pulse-slow': 'pulse 3s infinite',
        'shimmer':    'shimmer 2s infinite',
      },
      keyframes: {
        fadeIn:  { '0%': { opacity: 0 },             '100%': { opacity: 1 }             },
        slideUp: { '0%': { opacity: 0, transform: 'translateY(12px)' }, '100%': { opacity: 1, transform: 'translateY(0)' } },
        shimmer: { '0%,100%': { opacity: 0.5 }, '50%': { opacity: 1 } },
      },
    },
  },
  plugins: [],
}
