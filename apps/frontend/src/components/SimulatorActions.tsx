import { Button, Popconfirm, Space, message } from "antd";
import { useState } from "react";

type OperationError = {
  key: "refresh" | "rollback";
  message: string;
};

export default function SimulatorActions({
  onOperationError,
  onOperationSuccess,
  disabled = false,
}: {
  onOperationError: (error: OperationError) => void;
  onOperationSuccess: (key: OperationError["key"]) => void;
  disabled?: boolean;
}) {
  const [loading, setLoading] = useState(false);

  async function refreshManifest() {
    setLoading(true);
    try {
      const res = await fetch("/api/simulators/refresh-manifest", { method: "POST" });
      if (!res.ok) throw new Error("Failed to refresh manifest");
      message.success("Manifest refreshed");
      onOperationSuccess("refresh");
    } catch (e: any) {
      onOperationError({ key: "refresh", message: e.message || "Refresh failed" });
    } finally {
      setLoading(false);
    }
  }

  async function rollback() {
    setLoading(true);
    try {
      // For demo: just call rollback with a dummy timestamp
      const res = await fetch("/api/simulators/rollback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ timestamp: new Date().toISOString() }),
      });
      if (!res.ok) throw new Error("Failed to rollback");
      message.success("Rollback complete");
      onOperationSuccess("rollback");
    } catch (e: any) {
      onOperationError({ key: "rollback", message: e.message || "Rollback failed" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <Space>
      <Button onClick={refreshManifest} loading={loading} disabled={disabled}>
        Refresh Manifest
      </Button>
      <Popconfirm title="Rollback to previous simulator?" onConfirm={rollback}>
        <Button loading={loading} disabled={disabled}>
          Rollback
        </Button>
      </Popconfirm>
    </Space>
  );
}
