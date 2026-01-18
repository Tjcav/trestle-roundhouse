import React from "react";
import { createRoot } from "react-dom/client";
import "antd/dist/reset.css";
import { ConfigProvider, Layout, Menu, Space, Typography } from "antd";
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

  const suiteItems = SUITES.map((item) => ({ key: item.key, label: item.label }));
  const sectionItems = SECTIONS[suite].map((item) => ({
    key: item.key,
    label: item.label,
  }));

  React.useEffect(() => {
    const firstSection = SECTIONS[suite][0];
    if (firstSection && !SECTIONS[suite].some((item) => item.key === section)) {
      setSection(firstSection.key);
    }
  }, [suite, section]);

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
