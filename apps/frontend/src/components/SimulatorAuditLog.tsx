import { Collapse, Timeline, Spin } from "antd";
import { useState } from "react";

export default function SimulatorAuditLog() {
  const [open, setOpen] = useState(false);
  const [log, setLog] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  async function loadLog() {
    setLoading(true);
    try {
      const res = await fetch("/api/simulators/audit-log");
      const data = res.ok ? await res.json() : { log: [] };
      setLog(data.log || []);
    } finally {
      setLoading(false);
    }
  }

  return (
    <Collapse
      onChange={key => {
        if (key.length && !log.length) loadLog();
        setOpen(!!key.length);
      }}
      items={[{
        key: "audit",
        label: "Audit Log",
        children: loading ? <Spin /> : (
          <Timeline
            items={log.map((entry: any) => ({
              color: entry.outcome === "error" ? "red" : "blue",
              children: `${entry.timestamp} — ${entry.user}: ${entry.action || "select"} ${entry.artifact_name}`,
            }))}
          />
        ),
      }]}
    />
  );
}
