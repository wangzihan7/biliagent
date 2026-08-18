import type { Config } from 'tailwindcss';

// Tailwind design tokens for BiliAgent Studio
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Primary blue tone (Bilibili-ish but more professional)
        primary: {
          50: '#e5f1ff',
          100: '#d0e4ff',
          200: '#a6c7ff',
          300: '#7ca9ff',
          400: '#4f8aff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#172554',
        },
        accent: {
          400: '#a855f7',
          500: '#8b5cf6',
          600: '#7c3aed',
        },
        // Neutral slate-ish palette tuned for dark UI
        surface: {
          50: '#0b0d12',
          100: '#111827',
          200: '#131722',
          300: '#1f2937',
        },
      },
      boxShadow: {
        'soft-card': '0 18px 45px rgba(15, 23, 42, 0.6)',
      },
      borderRadius: {
        'xl2': '1rem',
      },
      fontFamily: {
        sans: [
          '"HarmonyOS Sans"',
          '"PingFang SC"',
          '"Microsoft YaHei"',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'sans-serif',
        ],
      },
    },
  },
  plugins: [],
} satisfies Config;

