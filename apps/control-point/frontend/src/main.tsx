import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import { ConfigProvider, theme } from "antd";
import ControlPointApp from "./App";

const root = createRoot(document.getElementById("root")!);
root.render(
  <StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
      }}
    >
      <ControlPointApp />
    </ConfigProvider>
  </StrictMode>
);
