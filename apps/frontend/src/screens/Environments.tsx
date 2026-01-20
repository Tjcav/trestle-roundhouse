import { Alert, Card, Space, Spin, Typography } from "antd";
import { useEffect, useState } from "react";
import styles from "./Environments.module.css";

const { Title, Text } = Typography;

type HAStatus = {
  ha_available: boolean;
};

type TrestleStatus = {
  trestle_available: boolean;
};

export default function Environments() {
  const [ha, setHa] = useState<HAStatus | null>(null);
  const [trestle, setTrestle] = useState<TrestleStatus | null>(null);
  const [haEntities, setHaEntities] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [haRes, trestleRes] = await Promise.all([
          fetch("/api/ha/status"),
          fetch("/api/trestle/status"),
        ]);

        const haData = haRes.ok ? await haRes.json() : { ha_available: false };
        const trestleData = trestleRes.ok
          ? await trestleRes.json()
          : { trestle_available: false };

        if (!cancelled) {
          setHa(haData);
          setTrestle(trestleData);
          setError(null);
        }

        if (haData.ha_available) {
          const entitiesRes = await fetch("/api/ha/entities");
          if (entitiesRes.ok) {
            const entitiesData = await entitiesRes.json();
            const count = Array.isArray(entitiesData.entities)
              ? entitiesData.entities.length
              : 0;
            if (!cancelled) {
              setHaEntities(count);
            }
          }
        }
      } catch {
        if (!cancelled) {
          setError("Unable to reach Roundhouse backend");
        }
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (error) {
    return <Alert type="error" message={error} showIcon />;
  }

  if (!ha || !trestle) {
    return <Spin />;
  }

  return (
    <Space direction="vertical" size="large" className={styles.fullWidth}>
      <Title level={2}>Environments</Title>

      <Card title="Home Assistant">
        {ha.ha_available ? (
          <Space direction="vertical" size="small">
            <Text type="success">Connected</Text>
            {haEntities !== null && (
              <Text type="secondary">{haEntities} entities discovered</Text>
            )}
            <Text type="secondary">
              Enables system discovery, environment snapshots, and read-only inspection.
            </Text>
          </Space>
        ) : (
          <Space direction="vertical" size="small">
            <Text type="danger">Not configured</Text>
            <Text type="secondary">
              Configure HA to enable system discovery and runtime tools.
            </Text>
            <Text type="secondary">
              Enables system discovery, environment snapshots, and read-only inspection.
            </Text>
          </Space>
        )}
      </Card>

      <Card title="Trestle-HA">
        {trestle.trestle_available ? (
          <Space direction="vertical" size="small">
            <Text type="success">Connected</Text>
            <Text type="secondary">Enables validation, simulation, and apply workflows.</Text>
          </Space>
        ) : (
          <Space direction="vertical" size="small">
            <Text type="danger">Not configured</Text>
            <Text type="secondary">
              Trestle-HA is required for validation, simulation, and apply.
            </Text>
            <Text type="secondary">Enables validation, simulation, and apply workflows.</Text>
          </Space>
        )}
      </Card>
    </Space>
  );
}
