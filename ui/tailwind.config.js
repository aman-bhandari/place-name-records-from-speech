// Tokens: Survey of India toposheet inks on map paper — black lettering, contour brown, drainage blue, forest green.
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Mukta', 'system-ui', 'sans-serif'],
        name: ['"Tiro Devanagari Hindi"', 'Georgia', 'serif'],
        ipa: ['"Noto Sans"', 'system-ui', 'sans-serif'],
      },
      colors: {
        paper: '#F7F6F1',
        ink: { DEFAULT: '#17201F', soft: '#4A5553', faint: '#7C8684' },
        contour: { DEFAULT: '#8F5A2E', soft: '#EFE4D8' },
        water: { DEFAULT: '#2B6C8C', soft: '#E3EDF2' },
        forest: { DEFAULT: '#3F6D4E', soft: '#E4EDE6' },
        grid: '#CDD5D3',
        alert: { DEFAULT: '#9A3B2E', soft: '#F3E4E1' },
      },
    },
  },
  plugins: [],
}
