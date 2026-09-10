/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          500: '#6366F1',
          600: '#4F46E5', // Primary Indigo
          700: '#4338CA',
          900: '#312E81',
        },
        quantum: {
          purple: '#8B5CF6',
          cyan: '#06B6D4',
          indigo: '#4F46E5',
          light: '#F5F3FF'
        },
        legitimate: {
          DEFAULT: '#10B981',
          bg: '#ECFDF5',
          text: '#047857',
          border: '#A7F3D0'
        },
        warning: {
          DEFAULT: '#F59E0B',
          bg: '#FFFBEB',
          text: '#B45309',
          border: '#FDE68A'
        },
        malicious: {
          DEFAULT: '#EF4444',
          bg: '#FEF2F2',
          text: '#B91C1C',
          border: '#FECACA'
        }
      },
      boxShadow: {
        'soft': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px -1px rgba(0, 0, 0, 0.05)',
        'card': '0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -1px rgba(0, 0, 0, 0.02)',
      }
    },
  },
  plugins: [],
}
