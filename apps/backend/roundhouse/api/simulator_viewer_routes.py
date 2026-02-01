from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/simulators", tags=["simulators"])


@router.get("/viewer")
async def simulator_viewer() -> HTMLResponse:
    html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Simulator Viewer</title>
    <style>
      html,
      body {
        height: 100%;
        width: 100%;
        margin: 0;
        background: #0f1115;
        color: #e6eaf2;
        font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
      }
      #root {
        height: 100%;
        width: 100%;
        position: relative;
        overflow: hidden;
      }
      #runtime {
        position: absolute;
        inset: 0;
      }
      .empty {
        text-align: center;
        opacity: 0.7;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
      }
      #overlay {
        position: absolute;
        inset: 0;
        background: rgba(15, 17, 21, 0.85);
        color: #e6eaf2;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        letter-spacing: 0.02em;
        opacity: 0;
        pointer-events: none;
        transition: opacity 160ms ease;
        z-index: 2;
      }
      #overlay.visible {
        opacity: 1;
      }
    </style>
  </head>
  <body>
    <div id="root">
      <div id="runtime">
        <div class="empty">No simulator selected.</div>
      </div>
      <div id="overlay">Loading simulator…</div>
    </div>
    <script>
      const overlay = document.getElementById("overlay");
      const runtime = document.getElementById("runtime");
      let bootTimeout = null;

      function showOverlay(message) {
        overlay.textContent = message || "Loading simulator…";
        overlay.classList.add("visible");
      }

      function hideOverlay() {
        if (bootTimeout) {
          clearTimeout(bootTimeout);
          bootTimeout = null;
        }
        overlay.classList.remove("visible");
      }

      function setEmpty(message) {
        runtime.innerHTML = "";
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = message || "No simulator selected.";
        runtime.appendChild(empty);
      }

      function cleanupRuntime() {
        runtime.innerHTML = "";
        delete window.Module;
        delete window.simulatorReady;
      }

      async function resolveGlueScript(baseName) {
        const candidates = [`${baseName}.js`, `${baseName}.mjs`];
        for (const candidate of candidates) {
          const res = await fetch(`/api/artifacts/download/${encodeURIComponent(candidate)}`, {
            method: "GET",
            headers: { Range: "bytes=0-0" },
          });
          if (res.ok) return candidate;
        }
        return null;
      }

      async function loadArtifact(artifactName) {
        if (!artifactName) {
          setEmpty("No simulator selected.");
          hideOverlay();
          return;
        }

        showOverlay("Loading simulator…");
        if (bootTimeout) {
          clearTimeout(bootTimeout);
        }
        bootTimeout = setTimeout(() => {
          overlay.textContent = "Still loading simulator…";
        }, 8000);
        cleanupRuntime();

        const isWasm = artifactName.toLowerCase().endsWith(".wasm");
        const baseName = isWasm ? artifactName.slice(0, -5) : artifactName;
        const wasmUrl = isWasm ? `/api/artifacts/download/${encodeURIComponent(artifactName)}` : null;

        try {
          const glue = await resolveGlueScript(baseName);
          if (!glue) {
            throw new Error("Missing glue script (.js or .mjs) for simulator.");
          }

          window.simulatorReady = () => {
            hideOverlay();
            parent.postMessage({ type: "simulator:booted" }, "*");
          };

          if (wasmUrl) {
            window.Module = {
              locateFile: (path) => (path.endsWith(".wasm") ? wasmUrl : path),
              onRuntimeInitialized: () => window.simulatorReady(),
            };
          }

          const script = document.createElement("script");
          script.src = `/api/artifacts/download/${encodeURIComponent(glue)}`;
          script.async = true;
          if (glue.endsWith(".mjs")) {
            script.type = "module";
          }

          script.onload = () => {
            // Wait for runtime to signal readiness via simulatorReady / onRuntimeInitialized.
          };
          script.onerror = () => {
            setEmpty("Failed to load simulator glue script.");
            hideOverlay();
            parent.postMessage({ type: "simulator:error", message: "Failed to load simulator glue script." }, "*");
          };

          runtime.appendChild(script);
        } catch (err) {
          setEmpty(err.message || "Failed to load simulator.");
          hideOverlay();
          parent.postMessage({ type: "simulator:error", message: err.message || "Failed to load simulator." }, "*");
        }
      }

      window.addEventListener("message", (event) => {
        if (!event.data || event.data.type !== "simulator:load") return;
        loadArtifact(event.data.artifact);
      });

      const params = new URLSearchParams(window.location.search);
      const initial = params.get("artifact");
      if (initial) {
        loadArtifact(initial);
      } else {
        setEmpty("No simulator selected.");
      }

      parent.postMessage({ type: "simulator:ready" }, "*");
    </script>
  </body>
</html>
"""
    return HTMLResponse(content=html)
