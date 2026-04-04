import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./src/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        graphite: {
          50: "#f6f7f8",
          100: "#dde1e4",
          200: "#b7c0c7",
          300: "#8f9ca8",
          400: "#687889",
          500: "#4d5b6a",
          600: "#3b4654",
          700: "#2b333d",
          800: "#1b232b",
          900: "#10161c"
        },
        safety: {
          orange: "#ff7b31",
          amber: "#ffb54d",
          mint: "#7ce7c6",
          steel: "#94a3b8"
        }
      },
      boxShadow: {
        panel: "0 24px 60px rgba(0, 0, 0, 0.28)"
      },
      fontFamily: {
        display: ["var(--font-rajdhani)", "sans-serif"],
        body: ["var(--font-plex)", "sans-serif"]
      },
      backgroundImage: {
        grid: "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)"
      }
    }
  },
  plugins: []
};

export default config;

