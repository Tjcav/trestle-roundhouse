import { Alert, Button, Space, Table, Tag, Tooltip, Typography } from "antd";
import { useEffect, useState } from "react";

export default function SimulatorTable({
  onSystemError,
  disableActions = false,
  suppressActionErrors = false,
}: {
  onSystemError: (e: string | null) => void;
  disableActions?: boolean;
  suppressActionErrors?: boolean;
}) {
  const [data, setData] = useState<any[]>([]);
  const [current, setCurrent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activating, setActivating] = useState<string | null>(null);
  const [actionErrors, setActionErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [invRes, curRes] = await Promise.all([
          fetch("/api/simulators/inventory"),
          fetch("/api/simulators/current"),
        ]);
        if (!invRes.ok || !curRes.ok) {
          throw new Error("Failed to load simulator inventory");
        }
        const invData = invRes.ok ? await invRes.json() : [];
        const curData = curRes.ok ? await curRes.json() : {};
        if (!cancelled) {
          setData(invData);
          setCurrent(curData.artifact_name || null);
          onSystemError(null);
        }
      } catch (e: any) {
        if (!cancelled) onSystemError(e.message || "Failed to load simulators");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [activating, onSystemError]);

  async function selectSimulator(record: any) {
    setActivating(record.simulator_id);
    try {
      const res = await fetch("/api/simulators/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artifact_name: record.simulator_id }),
      });
      if (!res.ok) throw new Error("Failed to activate simulator");
      if (!suppressActionErrors) {
        setActionErrors(prev => {
          const next = { ...prev };
          delete next[record.simulator_id];
          return next;
        });
      }
    } catch (e: any) {
      if (!suppressActionErrors) {
        const message = e.message || "Activation failed";
        setActionErrors(prev => ({
          ...prev,
          [record.simulator_id]: `Activation failed for ${record.simulator_id} ${record.version}: ${message}`,
        }));
      }
    } finally {
      setActivating(null);
    }
  }

  const statusColor = (status: string) => {
    switch (status) {
      case "error":
        return "error";
      default:
        return "default";
    }
  };

  return (
    <Table
      dataSource={data}
      rowKey="simulator_id"
      loading={loading}
      size="small"
      pagination={false}
      rowClassName={rec => (rec.simulator_id === current ? "ant-table-row-selected" : "")}
      columns={[
        { title: "Simulator", dataIndex: "simulator_id" },
        { title: "Platform", dataIndex: "platform", render: (v: string) => <Tag>{v}</Tag> },
        { title: "Version", dataIndex: "version" },
        {
          title: "Status",
          dataIndex: "status",
          render: (v: string) => <Tag color={statusColor(v)}>{v}</Tag>,
        },
        {
          title: "Size",
          dataIndex: "size_bytes",
          render: (v: number) => (
            <Typography.Text type="secondary">{`${(v / 1024 / 1024).toFixed(2)} MB`}</Typography.Text>
          ),
        },
        {
          title: "Built",
          dataIndex: "build_timestamp",
          render: (v: string) => <Typography.Text type="secondary">{v}</Typography.Text>,
        },
        {
          title: "Actions",
          key: "action",
          align: "right",
          render: (_, rec) => (
            <Space direction="vertical" size="small" align="end">
              <Tooltip title={rec.status === "downloadable" ? "Download & Activate" : undefined}>
                <Button
                  type={rec.simulator_id === current || actionErrors[rec.simulator_id] ? "default" : "primary"}
                  disabled={disableActions || rec.status === "unavailable"}
                  loading={activating === rec.simulator_id}
                  onClick={() => selectSimulator(rec)}
                >
                  {rec.simulator_id === current
                    ? "Active"
                    : actionErrors[rec.simulator_id]
                      ? "Retry"
                      : rec.status === "downloadable"
                        ? "Download & Activate"
                        : "Activate"}
                </Button>
              </Tooltip>
              {actionErrors[rec.simulator_id] && !suppressActionErrors ? (
                <Alert type="error" showIcon message={actionErrors[rec.simulator_id]} />
              ) : null}
            </Space>
          ),
        },
      ]}
    />
  );
}
