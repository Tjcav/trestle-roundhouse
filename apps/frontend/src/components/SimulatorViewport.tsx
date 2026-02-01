import { useEffect, useRef } from "react";

type SimulatorViewportProps = {
  artifactRef: string | null;
  viewerUrl: string;
};

export default function SimulatorViewport({ artifactRef, viewerUrl }: SimulatorViewportProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const pendingArtifactRef = useRef<string | null>(null);

  useEffect(() => {
    pendingArtifactRef.current = artifactRef;
    const frame = iframeRef.current;
    if (!frame || !frame.contentWindow || !artifactRef) return;
    frame.contentWindow.postMessage({ type: "simulator:load", artifact: artifactRef }, "*");
  }, [artifactRef]);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (!event.data || event.data.type !== "simulator:ready") return;
      const frame = iframeRef.current;
      const pending = pendingArtifactRef.current;
      if (!frame || !frame.contentWindow || !pending) return;
      frame.contentWindow.postMessage({ type: "simulator:load", artifact: pending }, "*");
    };
    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <iframe
      ref={iframeRef}
      title="Simulator"
      src={viewerUrl}
      style={{ border: "none", width: "100%", height: "100%", display: "block" }}
    />
  );
}
