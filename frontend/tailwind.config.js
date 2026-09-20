/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#070B14',
        sidebar: '#080D17',
        'bg-secondary': '#080D17',
        card: '#0E1726',
        'card-hover': '#121E30',
        border: '#1B2B40',
        'dfir-blue': '#1683FF',
        'dfir-cyan': '#16C7D9',
        'dfir-green': '#20C997',
        'dfir-amber': '#F2B84B',
        'dfir-purple': '#8B6CFF',
        surface: {
          DEFAULT: '#0E1726',
          subtle: '#080D17',
          inset: '#070B14',
          elevated: '#121E30',
          border: '#1B2B40',
        },
        primary: {
          DEFAULT: '#F1F5F9',
          muted: '#94A3B8',
          subtle: '#64748B',
        },
        accent: {
          DEFAULT: '#16C7D9',
          light: '#5EEAD4',
          dark: '#0891B2',
          blue: '#1683FF',
          glow: 'rgba(22, 199, 217, 0.08)',
        },
        success: {
          DEFAULT: '#20C997',
          light: '#6EE7B7',
          dark: '#059669',
          glow: 'rgba(32, 201, 151, 0.08)',
        },
        warning: {
          DEFAULT: '#F2B84B',
          light: '#FDE68A',
          dark: '#D97706',
          glow: 'rgba(242, 184, 75, 0.08)',
        },
        danger: {
          DEFAULT: '#FB7185',
          light: '#FDA4AF',
          dark: '#E11D48',
          glow: 'rgba(251, 113, 133, 0.08)',
        },
        dark: {
          950: '#070B14',
          900: '#080D17',
          800: '#0E1726',
          750: '#141F32',
          700: '#1E3048',
          600: '#283E5C',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'SFMono-Regular', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.35)',
        'card': '0 4px 16px -2px rgba(0, 0, 0, 0.5), 0 1px 3px 0 rgba(0, 0, 0, 0.3)',
        'elevated': '0 8px 24px -4px rgba(0, 0, 0, 0.6), 0 4px 8px -2px rgba(0, 0, 0, 0.4)',
        'blue-subtle': '0 0 16px -2px rgba(22, 131, 255, 0.15)',
        'cyan-subtle': '0 0 16px -2px rgba(25, 211, 230, 0.15)',
      },
    },
  },
  plugins: [],
}
