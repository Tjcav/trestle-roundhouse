import React from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import { Alert, Badge, ConfigProvider, Layout, Menu, Space, Typography } from "antd";
import ControlPointApp from "../../control-point/frontend/src/App";

const { Header, Sider, Content } = Layout;
const { Title, Text } = Typography;

type SuiteKey = "overview" | "systems" | "profiles";
type SectionKey = string;

const SUITES: { key: SuiteKey; label: string }[] = [
  { key: "overview", label: "Overview" },
  { key: "systems", label: "Systems" },
  { key: "profiles", label: "Profiles" },
];

const SECTIONS: Record<SuiteKey, { key: SectionKey; label: string }[]> = {
  overview: [
    { key: "status", label: "Status" },
    { key: "configuration", label: "Configuration" },
    { key: "export", label: "Export" },
    { key: "control-point", label: "Control Point" },
  ],
  systems: [
    { key: "home-assistant", label: "Home Assistant" },
    { key: "zigbee", label: "Zigbee" },
    { key: "matter", label: "Matter" },
    { key: "trestle", label: "Trestle" },
    { key: "activity", label: "Activity" },
  ],
  profiles: [
    { key: "editor", label: "Editor" },
    { key: "simulate", label: "Simulate" },
    { key: "insights", label: "Insights" },
  ],
};

function App() {
  const [suite, setSuite] = React.useState<SuiteKey>("overview");
  const [section, setSection] = React.useState<SectionKey>("status");
  const [haAvailable, setHaAvailable] = React.useState<boolean>(false);
  const [trestleAvailable, setTrestleAvailable] = React.useState<boolean>(false);
  const [statusError, setStatusError] = React.useState<string | null>(null);

  const suiteItems = SUITES.map((item) => ({
    key: item.key,
    label: item.label,
    disabled: item.key === "systems" ? !haAvailable : item.key === "profiles" ? !trestleAvailable : false,
  }));
  const sectionItems = SECTIONS[suite].map((item) => ({
    key: item.key,
    label: item.label,
    disabled: item.key === "status" ? false : suite === "systems" ? !haAvailable : suite === "profiles" ? !trestleAvailable : false,
  }));

  React.useEffect(() => {
    const firstSection = SECTIONS[suite][0];
    if (firstSection && !SECTIONS[suite].some((item) => item.key === section)) {
      setSection(firstSection.key);
    }
  }, [suite, section]);

  React.useEffect(() => {
    let cancelled = false;
    const fetchStatus = async () => {
      try {
        const [haRes, trestleRes] = await Promise.all([
          fetch("/api/ha/status"),
          fetch("/api/trestle/status"),
        ]);
        const haData = haRes.ok ? await haRes.json() : { ha_available: false };
        const trestleData = trestleRes.ok ? await trestleRes.json() : { trestle_available: false };
        if (!cancelled) {
          setHaAvailable(Boolean(haData.ha_available));
          setTrestleAvailable(Boolean(trestleData.trestle_available));
          setStatusError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setStatusError("Unable to reach Roundhouse backend");
          setHaAvailable(false);
          setTrestleAvailable(false);
        }
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 6,
          controlHeight: 32,
          fontSize: 14,
        },
      }}
    >
      <Layout style={{ minHeight: "100vh" }}>
        <Header style={{ background: "#fff", borderBottom: "1px solid #f0f0f0" }}>
          <Menu
            mode="horizontal"
            selectedKeys={[suite]}
            items={suiteItems}
            onClick={(info) => setSuite(info.key as SuiteKey)}
          />
        </Header>
        <Layout>
          <Sider width={220} style={{ background: "#fff", borderRight: "1px solid #f0f0f0" }}>
            <Menu
              mode="inline"
              selectedKeys={[section]}
              items={sectionItems}
              onClick={(info) => setSection(info.key)}
              style={{ height: "100%", borderRight: 0 }}
            />
          </Sider>
          <Content style={{ padding: 24, background: "#fafafa" }}>
            <Space direction="vertical" size="middle" style={{ width: "100%" }}>
              <Title level={2} style={{ margin: 0 }}>
                {SUITES.find((item) => item.key === suite)?.label}
              </Title>
              <Space size="middle">
                <Badge status={haAvailable ? "success" : "error"} text="HA API" />
                <Badge status={trestleAvailable ? "success" : "error"} text="Trestle-HA" />
              </Space>
              {statusError && (
                <Alert
                  type="error"
                  message="Backend unavailable"
                  description={statusError}
                  showIcon
                />
              )}
              {!haAvailable && !trestleAvailable && !statusError && (
                <Alert
                  type="warning"
                  message="No backends configured"
                  description="Configure HA or Trestle-HA to enable features."
                  showIcon
                />
              )}
              <Text type="secondary">Section: {section}</Text>
              {suite === "overview" && section === "control-point" ? (
                <ControlPointApp embedded />
              ) : (
                <Text>
                  This is the Roundhouse shell layout (Ant-based). Sub-app content will
                  render here once mounted.
                </Text>
              )}
            </Space>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
}

const root = createRoot(document.getElementById("root")!);
root.render(<App />);
