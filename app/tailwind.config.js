/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    borderRadius: {
      none: '0px',
      sm: '4px',
      DEFAULT: '4px',
      md: '4px',
      lg: '4px',
      xl: '4px',
      '2xl': '4px',
      '3xl': '4px',
      full: '9999px',
    },
    extend: {
      colors: {
        prussian: '#012652',
        dodger: '#0D94FB',
        ink: '#1A1F36',
        slate: '#5A6478',
        line: '#E3E8EF',
        canvas: '#F7F9FC',
        surface: '#FFFFFF',
        contest: '#0F7B4F',
        accept: '#B45309',
        gap: '#C0392B',
      },
    },
  },
  plugins: [],
}
