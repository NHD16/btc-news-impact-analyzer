import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev: proxy mọi request /api về backend FastAPI (cổng 8000).
// Build: xuất ra ../app/static để FastAPI phục vụ ở production.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "../app/static",
    emptyOutDir: true,
  },
});
