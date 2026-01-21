import React from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import { BrowserRouter } from "react-router-dom";
import AppShell from "./AppShell";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}
const root = createRoot(rootElement);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  </React.StrictMode>,
);
