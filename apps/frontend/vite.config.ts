import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const frontendPort = Number(env.VITE_FRONTEND_PORT || 5173);
  const backendUrl = env.VITE_BACKEND_URL || "http://localhost:8090";

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      strictPort: true,
      host: "0.0.0.0",
      proxy: {
        "/api": {
          target: backendUrl,
          changeOrigin: true,
        },
      },
      fs: {
        allow: ["..", "../control-point/frontend/src"],
      },
    },
  };
});
