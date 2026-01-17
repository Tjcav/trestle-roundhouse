import React from "react";
import { createRoot } from "react-dom/client";
import Dashboard from "./pages/Dashboard";

const root = createRoot(document.getElementById("root")!);
root.render(<Dashboard />);
