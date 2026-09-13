/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#080B14',
        card: '#111827',
        border: '#253044',
        surface: {
          DEFAULT: '#111827',
          subtle: '#0D1322',
          inset: '#0B0F19',
          elevated: '#162032',
          border: '#253044',
        },
        primary: {
          DEFAULT: '#F8FAFC',
          muted: '#94A3B8',
          subtle: '#64748B',
        },
        accent: {
          DEFAULT: '#22D3EE',
          light: '#67E8F9',
          dark: '#0891B2',
          glow: 'rgba(34, 211, 238, 0.15)',
        },
        success: {
          DEFAULT: '#34D399',
          light: '#6EE7B7',
          dark: '#059669',
          glow: 'rgba(52, 211, 153, 0.15)',
        },
        warning: {
          DEFAULT: '#FBBF24',
          light: '#FDE68A',
          dark: '#D97706',
          glow: 'rgba(251, 191, 36, 0.15)',
        },
        danger: {
          DEFAULT: '#FB7185',
          light: '#FDA4AF',
          dark: '#E11D48',
          glow: 'rgba(251, 113, 133, 0.15)',
        },
        dark: {
          950: '#080B14',
          900: '#0D1322',
          800: '#111827',
          750: '#162032',
          700: '#1E293B',
          600: '#253044',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.3)',
        'card': '0 4px 20px -2px rgba(8, 11, 20, 0.7), 0 2px 6px -1px rgba(0, 0, 0, 0.4)',
        'elevated': '0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
        'cyan-glow': '0 0 15px -3px rgba(34, 211, 238, 0.25)',
      },
    },
  },
  plugins: [],
}
