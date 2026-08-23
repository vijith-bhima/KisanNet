import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        paddy: {
          DEFAULT: "#1E4A32",
          light: "#2C6644",
          dark: "#123420",
        },
        turmeric: {
          DEFAULT: "#E5A114",
          light: "#F4BE4C",
          dark: "#B87D0B",
        },
        soil: {
          DEFAULT: "#6B4226",
          light: "#8A5A37",
        },
        husk: {
          DEFAULT: "#FBF6EA",
          dark: "#F2E9D3",
        },
        monsoon: {
          DEFAULT: "#2F86A6",
          light: "#4FA3C2",
        },
        chili: {
          DEFAULT: "#C0392B",
        },
      },
      fontFamily: {
        display: ["var(--font-baloo)", "sans-serif"],
        body: ["var(--font-mukta)", "sans-serif"],
      },
      borderRadius: {
        "4xl": "2rem",
        "5xl": "2.5rem",
      },
      boxShadow: {
        soft: "0 8px 30px rgba(30, 74, 50, 0.12)",
        card: "0 4px 16px rgba(107, 66, 38, 0.10)",
      },
      animation: {
        "pulse-ring": "pulse-ring 2.2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "pulse-ring-delay": "pulse-ring 2.2s cubic-bezier(0.4, 0, 0.6, 1) infinite 0.6s",
        "float-slow": "float 6s ease-in-out infinite",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { transform: "scale(1)", opacity: "0.55" },
          "100%": { transform: "scale(1.9)", opacity: "0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
