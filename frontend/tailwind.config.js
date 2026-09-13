/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#090D16',
          800: '#111827',
          700: '#1F2937',
          600: '#374151',
        },
        cyber: {
          teal: '#00F2FE',
          cyan: '#4FACFE',
          emerald: '#10B981',
          amber: '#F59E0B',
          rose: '#EF4444',
        }
      }
    },
  },
  plugins: [],
}
