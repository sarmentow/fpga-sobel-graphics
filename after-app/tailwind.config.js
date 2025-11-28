/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        surface: {
          900: '#0a0a0b',
          800: '#121214',
          700: '#1a1a1d',
          600: '#242428',
        },
        accent: {
          DEFAULT: '#00ff9f',
          dim: '#00cc7f',
        }
      }
    }
  },
  plugins: [],
}

