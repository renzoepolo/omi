/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        border: 'hsl(210 20% 85%)',
        input: 'hsl(210 20% 85%)',
        ring: 'hsl(210 54% 39%)',
        background: 'hsl(210 22% 97%)',
        foreground: 'hsl(215 20% 22%)',
        primary: {
          DEFAULT: 'hsl(210 54% 39%)',
          foreground: 'hsl(0 0% 100%)',
        },
        muted: {
          DEFAULT: 'hsl(210 20% 94%)',
          foreground: 'hsl(214 14% 41%)',
        },
        card: {
          DEFAULT: 'hsl(0 0% 100% / 0.94)',
          foreground: 'hsl(215 20% 22%)',
        },
      },
      borderRadius: {
        lg: '1rem',
        md: '1rem',
        sm: '1rem',
      },
      spacing: {
        1: '8px',
        2: '16px',
        3: '24px',
        4: '32px',
      },
    },
  },
  plugins: [],
};
