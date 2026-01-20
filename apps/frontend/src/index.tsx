import React from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import { BrowserRouter } from "react-router-dom";
import AppShell from "./AppShell";

const root = createRoot(document.getElementById("root")!);
root.render(
  <React.StrictMode>
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  </React.StrictMode>,
);
