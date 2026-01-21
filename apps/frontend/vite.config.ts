import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const frontendPort = Number(env.VITE_FRONTEND_PORT);
  if (!frontendPort) {
    throw new Error("VITE_FRONTEND_PORT is not set");
  }
  const backendUrl = env.VITE_BACKEND_URL;
  if (!backendUrl) {
    throw new Error("VITE_BACKEND_URL is not set");
  }

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
