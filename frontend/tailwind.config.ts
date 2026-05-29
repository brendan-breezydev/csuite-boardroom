import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          navy:  '#0b1e30',
          blue:  '#6e9db8',
          white: '#fcfcfc',
          // exec card gradient (navy → blue)
          ceo:   '#0b1e30',
          cfo:   '#163347',
          coo:   '#2c4a60',
          cmo:   '#4a7a9b',
          cto:   '#6e9db8',
        },
      },
      fontFamily: {
        sans: ['Montserrat', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
