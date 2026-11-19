/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        theme: {
          bg: 'var(--bg)',
          'bg-2': 'var(--bg-2)',
          glass: 'var(--glass)',
          'glass-border': 'var(--glass-border)',
          'glass-border-hover': 'var(--glass-border-hover)',
          primary: 'var(--primary)',
          accent: 'var(--accent)',
          'accent-2': 'var(--accent-2)',
          text: 'var(--text)',
          muted: 'var(--muted)',
          success: 'var(--success)',
          danger: 'var(--danger)',
          'btn-text': 'var(--btn-text)',
        }
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #F3E5AB 0%, #D4AF37 50%, #B8860B 100%)',
        'brand-gradient-hover': 'linear-gradient(135deg, #FFF0B8 0%, #E5C07B 50%, #C99700 100%)',
      }
    },
  },
  plugins: [],
}
