import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import ControlPointApp from "./App";

const root = createRoot(document.getElementById("root")!);
root.render(
  <StrictMode>
    <ControlPointApp />
  </StrictMode>
);
