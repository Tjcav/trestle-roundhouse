import { Badge, Button, ConfigProvider, Flex, Layout, Menu, Select, Space, Typography, theme } from "antd";
import { useEffect, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import styles from "./AppShell.module.css";
import ControlPoint from "./screens/ControlPoint";
import Environments from "./screens/Environments";
import Overview from "./screens/Overview";
import Placeholder from "./screens/Placeholder";

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

export default function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const [haAvailable, setHaAvailable] = useState(false);
  const [trestleAvailable, setTrestleAvailable] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const loadStatus = async () => {
      try {
        const [haRes, trestleRes] = await Promise.all([fetch("/api/ha/status"), fetch("/api/trestle/status")]);
        const haData = haRes.ok ? await haRes.json() : { ha_available: false };
        const trestleData = trestleRes.ok ? await trestleRes.json() : { trestle_available: false };

        if (!cancelled) {
          setHaAvailable(Boolean(haData.ha_available));
          setTrestleAvailable(Boolean(trestleData.trestle_available));
        }
      } catch {
        if (!cancelled) {
          setHaAvailable(false);
          setTrestleAvailable(false);
        }
      }
    };

    loadStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
      }}
    >
      <Layout className={styles.rootLayout}>
        <Header>
          <Flex justify="space-between" align="center">
            <Space size="middle">
              <Title level={4}>Roundhouse</Title>
              <Select value="default" options={[{ label: "Default", value: "default" }]} />
            </Space>
            <Space size="small">
              <Badge status={haAvailable ? "success" : "error"} text="HA API" />
              <Badge status={trestleAvailable ? "success" : "error"} text="Trestle-HA" />
              <Button type="link" onClick={() => navigate("/systems/environments")}>
                View details
              </Button>
            </Space>
          </Flex>
        </Header>

        <Layout>
          <Sider width={220}>
            <Menu
              mode="inline"
              selectedKeys={[location.pathname]}
              onClick={({ key }) => navigate(key)}
              items={[
                {
                  key: "/overview",
                  label: "Overview",
                },
                {
                  key: "systems",
                  label: "Systems",
                  children: [
                    {
                      key: "/systems/environments",
                      label: "Environments",
                    },
                  ],
                },
                {
                  key: "profiles",
                  label: "Profiles",
                  disabled: !trestleAvailable,
                  children: [
                    {
                      key: "/profiles/control-point",
                      label: "Control Point",
                    },
                    {
                      key: "/profiles/editor",
                      label: "Profile Editor",
                    },
                    {
                      key: "/profiles/validator",
                      label: "Validator",
                    },
                  ],
                },
                {
                  key: "/simulation",
                  label: "Simulation",
                  disabled: !trestleAvailable,
                },
                {
                  key: "/explain",
                  label: "Explain / Insights",
                  disabled: !trestleAvailable,
                },
                {
                  key: "/export",
                  label: "Export",
                  disabled: !trestleAvailable,
                },
              ]}
            />
          </Sider>

          <Content className={styles.content}>
            <div className={styles.contentInner}>
              <Routes>
                <Route path="/overview" element={<Overview />} />
                <Route path="/systems/environments" element={<Environments />} />
                <Route path="/profiles/control-point" element={<ControlPoint />} />
                <Route
                  path="/profiles/editor"
                  element={
                    <Placeholder
                      title="Profile Editor"
                      blocked={!trestleAvailable}
                      blockedMessage="This tool is unavailable."
                    />
                  }
                />
                <Route
                  path="/profiles/validator"
                  element={
                    <Placeholder
                      title="Validator"
                      blocked={!trestleAvailable}
                      blockedMessage="This tool is unavailable."
                    />
                  }
                />
                <Route
                  path="/simulation"
                  element={
                    <Placeholder
                      title="Simulation"
                      blocked={!trestleAvailable}
                      blockedMessage="This tool is unavailable."
                    />
                  }
                />
                <Route
                  path="/explain"
                  element={
                    <Placeholder
                      title="Explain / Insights"
                      blocked={!trestleAvailable}
                      blockedMessage="This tool is unavailable."
                    />
                  }
                />
                <Route
                  path="/export"
                  element={
                    <Placeholder
                      title="Export"
                      blocked={!trestleAvailable}
                      blockedMessage="This tool is unavailable."
                    />
                  }
                />
                <Route path="/" element={<Navigate to="/overview" replace />} />
                <Route path="*" element={<Navigate to="/overview" replace />} />
              </Routes>
            </div>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}
