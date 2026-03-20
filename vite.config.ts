import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import dts from "vite-plugin-dts";
import cssInjectedByJsPlugin from "vite-plugin-css-injected-by-js";
import { resolve } from "path";

export default defineConfig({
  plugins: [
    react(),
    dts({ include: ["src"], exclude: ["src/demo"], insertTypesEntry: true }),
    cssInjectedByJsPlugin(), 
  ],
  build: {
    lib: {
      entry: resolve(__dirname, "src/index.ts"),
      name: "Tsukikage",
      fileName: (format) => `tsukikage.${format === "es" ? "js" : "umd.cjs"}`,
      formats: ["es", "umd"],
    },
    rollupOptions: {
      external: ["react", "react-dom", "react/jsx-runtime"],
      output: {
        globals: {
          react: "React",
          "react-dom": "ReactDOM",
          "react/jsx-runtime": "jsxRuntime",
        },
      },
    },
    sourcemap: true,
    emptyOutDir: true,
  },
});