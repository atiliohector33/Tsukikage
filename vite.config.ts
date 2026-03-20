import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import dts from "vite-plugin-dts";
import { resolve } from "path";

export default defineConfig({
  plugins: [
    react(),
    // Generates .d.ts files automatically from your TypeScript sources
    dts({
      include: ["src"],
      exclude: ["src/demo"],
      insertTypesEntry: true,
    }),
  ],
  build: {
    lib: {
      // Entry point — everything exported from here is the public API
      entry: resolve(__dirname, "src/index.ts"),
      name: "Tsukikage",
      // Vite generates: tsukikage.js (ESM) and tsukikage.umd.cjs (UMD)
      fileName: (format) => `tsukikage.${format === "es" ? "js" : "umd.cjs"}`,
      formats: ["es", "umd"],
    },
    rollupOptions: {
      // React must NOT be bundled — consumers provide it
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
