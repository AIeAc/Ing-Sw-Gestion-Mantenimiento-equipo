import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  base: "./",
  build: {
    outDir: "app/static/dist",
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(import.meta.dirname, "frontend/src/main.js"),
      output: {
        entryFileNames: "app.js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.names?.some((name) => name.endsWith(".css"))) {
            return "app.css";
          }
          return "assets/[name][extname]";
        },
      },
    },
  },
});
