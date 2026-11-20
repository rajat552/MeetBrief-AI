/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    screens: {
      'xs': '420px',
      'sm': '640px',
      'md': '768px',
      'lg': '1024px',
      'xl': '1280px',
      '2xl': '1536px',
    },
    extend: {
      colors: {
        theme: {
          bg: 'var(--bg)',
          'bg-2': 'var(--bg-2)',
          surface: 'var(--surface)',
          'surface-subtle': 'var(--surface-subtle)',
          glass: 'var(--glass)',
          'glass-border': 'var(--glass-border)',
          'glass-border-hover': 'var(--glass-border-hover)',
          primary: 'var(--primary)',
          accent: 'var(--accent)',
          'accent-2': 'var(--accent-2)',
          'accent-light': 'var(--accent-light)',
          text: 'var(--text)',
          'text-secondary': 'var(--text-secondary)',
          muted: 'var(--muted)',
          'muted-light': 'var(--muted-light)',
          success: 'var(--success)',
          danger: 'var(--danger)',
          warning: 'var(--warning)',
          'warning-bg': 'var(--warning-bg)',
          'warning-border': 'var(--warning-border)',
          'btn-text': 'var(--btn-text)',
          'btn-dark': 'var(--btn-dark)',
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #2E5A44 0%, #4E876F 100%)',
        'brand-gradient-hover': 'linear-gradient(135deg, #244736 0%, #3D735D 100%)',
      }
    },
  },
  plugins: [],
}
