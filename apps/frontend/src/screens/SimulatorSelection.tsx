import { Alert, Button, Card, Spin, Table, Typography } from "antd";
import { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader";
import ScreenLayout from "../components/ScreenLayout";

const { Text } = Typography;

export type SimulatorInventoryItem = {
  simulator_id: string;
  platform: string;
  version: string;
  status: string;
  size_bytes: number;
  build_timestamp: string;
  checksum: string;
};

export type SimulatorCurrentResponse = {
  artifact_name: string | null;
};

export default function SimulatorSelection() {
  const [inventory, setInventory] = useState<SimulatorInventoryItem[] | null>(null);
  const [current, setCurrent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selecting, setSelecting] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const [invRes, curRes] = await Promise.all([
          fetch("/api/simulators/inventory"),
          fetch("/api/simulators/current"),
        ]);
        if (!invRes.ok || !curRes.ok) throw new Error("Failed to load simulator data");
        const invData = await invRes.json();
        const curData = await curRes.json();
        if (!cancelled) {
          setInventory(invData);
          setCurrent(curData.artifact_name || null);
          setError(null);
        }
      } catch (e: any) {
        if (!cancelled) setError(e.message || "Unknown error");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [selecting]);

  async function handleSelect(simulator_id: string) {
    setSelecting(simulator_id);
    try {
      const res = await fetch("/api/simulators/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artifact_name: simulator_id }),
      });
      if (!res.ok) throw new Error("Failed to select simulator");
      setCurrent(simulator_id);
    } catch (e: any) {
      setError(e.message || "Unknown error");
    } finally {
      setSelecting(null);
    }
  }

  const header = <PageHeader title="Simulators" />;
  if (loading) return <ScreenLayout header={header} primary={<Spin />} />;
  if (error) return <ScreenLayout header={header} alert={<Alert type="error" message={error} showIcon />} />;
  if (!inventory) return <ScreenLayout header={header} />;

  return (
    <ScreenLayout
      header={header}
      primary={
        <Card title="Available Simulators">
          <Table
            dataSource={inventory}
            rowKey="simulator_id"
            pagination={false}
            size="small"
            columns={[
              { title: "Simulator ID", dataIndex: "simulator_id" },
              { title: "Platform", dataIndex: "platform" },
              { title: "Version", dataIndex: "version" },
              { title: "Status", dataIndex: "status" },
              {
                title: "Size",
                dataIndex: "size_bytes",
                render: (v: number) => <Text type="secondary">{`${(v / 1024 / 1024).toFixed(2)} MB`}</Text>,
              },
              { title: "Build", dataIndex: "build_timestamp", render: (v: string) => <Text type="secondary">{v}</Text> },
              { title: "Checksum", dataIndex: "checksum" },
              {
                title: "Actions",
                key: "action",
                align: "right",
                render: (_, rec) => (
                  <Button
                    type={rec.simulator_id === current ? "primary" : "default"}
                    loading={selecting === rec.simulator_id}
                    disabled={rec.simulator_id === current || rec.status !== "available"}
                    onClick={() => handleSelect(rec.simulator_id)}
                  >
                    {rec.simulator_id === current ? "Active" : "Activate"}
                  </Button>
                ),
              },
            ]}
          />
        </Card>
      }
    />
  );
}
