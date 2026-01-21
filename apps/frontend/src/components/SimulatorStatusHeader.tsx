import { Badge, Space, Spin, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import PageHeader from "./PageHeader";

export default function SimulatorStatusHeader() {
  const [status, setStatus] = useState<string>("loading");
  const [current, setCurrent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      setLoading(true);
      try {
        const [statusRes, currentRes] = await Promise.all([
          fetch("/api/simulators/status"),
          fetch("/api/simulators/current"),
        ]);
        const statusData = statusRes.ok ? await statusRes.json() : { status: "unknown" };
        const currentData = currentRes.ok ? await currentRes.json() : {};
        if (!cancelled) {
          setStatus(statusData.status || "unknown");
          setCurrent(currentData.artifact_name ? currentData : null);
        }
      } catch {
        if (!cancelled) setStatus("error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    poll();
    const interval = setInterval(poll, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  let badgeStatus: "success" | "processing" | "error" | "default" = "default";
  let badgeText = "Unknown";
  if (status === "ready") { badgeStatus = "success"; badgeText = "Ready"; }
  else if (status === "activating" || status === "downloading") { badgeStatus = "processing"; badgeText = "Activating"; }
  else if (status === "error" || status === "failed") { badgeStatus = "error"; badgeText = "Error"; }

  return (
    <PageHeader
      title="Simulator Management"
      status={<Badge status={badgeStatus} text={badgeText} />}
      extra={loading ? <Spin size="small" /> : null}
    >
      {current ? (
        <Space size="small">
          <Tag color="default" bordered={false}>
            Panel
          </Tag>
          <Tag color="default" bordered={false}>
            WASM
          </Tag>
          <Tag color="default" bordered={false}>
            {current.artifact_name}
          </Tag>
        </Space>
      ) : (
        <Typography.Text type="secondary">No simulator selected</Typography.Text>
      )}
    </PageHeader>
  );
}
