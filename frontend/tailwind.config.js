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
          green: '#00B14F',
          lightGreen: '#E6F7EE',
          blue: '#2563EB',
          indigo: '#4F46E5',
        },
      },
      boxShadow: {
        'soft': '0 10px 40px -10px rgba(0,0,0,0.1)',
      },
    },
  },
  plugins: [],
}
