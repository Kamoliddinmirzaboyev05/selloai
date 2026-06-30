import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#151719",
        mist: "#f4f6f8",
        line: "#d9dee5",
        teal: "#137c72",
        coral: "#c84f3f",
        gold: "#b8872f",
      },
    },
  },
  plugins: [],
};

export default config;

