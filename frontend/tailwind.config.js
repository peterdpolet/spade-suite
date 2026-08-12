/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        paper: '#F6F3EC',
        'paper-dim': '#EDE8DC',
        ink: '#1B1E23',
        'ink-soft': '#5A5D63',
        line: '#DCD5C4',
        teal: { DEFAULT: '#1B4F4C', dark: '#123634', tint: '#E4EEED' },
        ochre: { DEFAULT: '#C48A2E', tint: '#F7ECD9' },
        danger: { DEFAULT: '#A8452F', tint: '#F4DCD5' },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
