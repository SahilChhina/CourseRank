/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        western: {
          purple: "#4F2683",
          gold: "#807F44",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};
