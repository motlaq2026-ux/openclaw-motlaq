/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        claw: {
          50: '#fff1f0',
          100: '#ffe4e1',
          200: '#fecdc7',
          300: '#fda99e',
          400: '#fb7a6a',
          500: '#f94d3a',
          600: '#e63024',
          700: '#c02218',
          800: '#9d1e17',
          900: '#811f19',
        },
        dark: {
          50: '#f6f6f7',
          100: '#e2e3e6',
          200: '#c4c6cc',
          300: '#9ea2aa',
          400: '#747880',
          500: '#5c5f66',
          600: '#4a4d52',
          700: '#3d3f42',
          800: '#28292b',
          900: '#111113',
          950: '#0a0a0b',
        },
      },
    },
  },
  plugins: [],
}
