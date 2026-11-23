/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'uber-black':   '#111111',
        'uber-white':   '#ffffff',
        'uber-surface': '#f6f6f6',
        'uber-border':  '#333333',
        'uber-muted':   '#525252',
        'uber-blue':    '#276ef1',
        'uber-red':     '#f43b00',
        'uber-orange':  '#fc993c',
        'uber-green':   '#0ca555',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        'slide-in': {
          '0%':   { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
      animation: {
        'slide-in': 'slide-in 0.22s cubic-bezier(0.16, 1, 0.3, 1) both',
      },
    },
  },
  plugins: [],
}

