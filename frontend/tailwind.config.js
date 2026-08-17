/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        maritime: {
          bg: '#06131F',
          panel: '#0B1D2B',
          'panel-secondary': '#102636',
          border: '#1D3A4C',
          cyan: '#20E5F5',
          'cyan-dim': '#0EA5B5',
          warning: '#F5A623',
          danger: '#FF4D5E',
          success: '#28D7A0',
          muted: '#7893A3',
          'muted-dim': '#4A6274',
        },
      },
      fontFamily: {
        sans: ['Montserrat', 'system-ui', 'sans-serif'],
        title: ['Unbounded', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      boxShadow: {
        glow: '0 0 20px rgba(32, 229, 245, 0.15)',
        'glow-lg': '0 0 40px rgba(32, 229, 245, 0.2)',
        'glow-warning': '0 0 20px rgba(245, 166, 35, 0.2)',
        'glow-danger': '0 0 20px rgba(255, 77, 94, 0.2)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'slide-right': 'slideRight 0.3s ease-out',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideRight: {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        glowPulse: {
          '0%, 100%': { boxShadow: '0 0 10px rgba(32, 229, 245, 0.1)' },
          '50%': { boxShadow: '0 0 25px rgba(32, 229, 245, 0.3)' },
        },
      },
    },
  },
  plugins: [],
};
