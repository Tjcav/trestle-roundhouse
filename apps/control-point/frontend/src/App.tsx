import React from "react";
import {
  Badge,
  Button,
  Card,
  Col,
  Image,
  Input,
  Layout,
  Menu,
  Row,
  Space,
  Typography,
} from "antd";

type ReviewStatus = "idle" | "checking" | "ok" | "warning" | "error";

type Diagnostics = {
  model?: string;
  total_tokens?: number;
  input_tokens?: number;
  output_tokens?: number;
  created_at?: number | string;
  error_source?: string;
};

type StatusView = {
  statusText: string;
  resultHeadline: string;
  badgeStatus: "success" | "processing" | "warning" | "error" | "default";
  resultType?: "success" | "warning" | "danger";
};

export type ControlPointAppProps = {
  embedded?: boolean;
};

const SIGNAL_SVG_DATA = encodeURIComponent(
  '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" role="img"><rect x="11" y="6" width="2" height="12" fill="#ffffff"/><circle cx="12" cy="6" r="4" fill="#ffffff"/><circle cx="12" cy="18" r="4" fill="#ffffff"/></svg>'
);

const DEFAULT_PROMPT_TEMPLATE = `You are a custodian AI.

Your job:
- Detect scope creep
- Detect violations of user preferences
- Detect large or risky changes
- Keep feedback short

User rules:
- Do not expand scope unless explicitly asked
- Avoid inventing architecture
- Prefer small, boring solutions
- Avoid large diffs or multi-file rewrites
- Prefer removal over deprecation
- Do not preserve backward compatibility unless explicitly requested
- Do not leave dead, unused, or obsolete code behind
- Favor the cleanest correct design over incremental compatibility
- If something feels heavy, flag it

Plan to review:
{{PLAN}}

Respond with:
- "OK" if no issues
- Otherwise: "RED FLAGS:" followed by bullets
`;

function ControlPointApp({ embedded = false }: ControlPointAppProps) {
  const [text, setText] = React.useState<string>("");
  const [result, setResult] = React.useState<string>("");
  const [diagnostics, setDiagnostics] = React.useState<Diagnostics>({});
  const [status, setStatus] = React.useState<ReviewStatus>("idle");
  const [promptTemplate, setPromptTemplate] = React.useState<string>(DEFAULT_PROMPT_TEMPLATE);
  const [isEditingPrompt, setIsEditingPrompt] = React.useState<boolean>(false);
  const [draftPrompt, setDraftPrompt] = React.useState<string>(DEFAULT_PROMPT_TEMPLATE);

  React.useEffect(() => {
    const stored = window.localStorage.getItem("controlPointPromptTemplate");
    if (stored) {
      setPromptTemplate(stored);
      setDraftPrompt(stored);
    }
  }, []);

  const statusView = (): StatusView => {
    if (status === "ok") {
      return {
        badgeStatus: "success",
        statusText: "Status: ✓ OK",
        resultHeadline: "✓ Safe to proceed.",
        resultType: "success",
      };
    }
    if (status === "warning") {
      return {
        badgeStatus: "warning",
        statusText: "Status: ⚠ review required",
        resultHeadline: "⚠ Review required.",
        resultType: "warning",
      };
    }
    if (status === "error") {
      return {
        badgeStatus: "error",
        statusText: "Status: ✕ error",
        resultHeadline: "✕ Review failed.",
        resultType: "danger",
      };
    }
    if (status === "checking") {
      return {
        badgeStatus: "processing",
        statusText: "Status: … checking",
        resultHeadline: "Review in progress…",
      };
    }
    return {
      badgeStatus: "default",
      statusText: "Status: idle",
      resultHeadline: "Waiting for input.",
    };
  };

  const formatDiagnostics = (data: Diagnostics): string => {
    const lines: string[] = [];
    if (data.error_source) {
      lines.push(`Error source: ${data.error_source}`);
    }
    if (data.model) {
      lines.push(`Model: ${data.model}`);
    }
    const tokenParts = [data.total_tokens, data.input_tokens, data.output_tokens];
    if (tokenParts.some((value) => value !== undefined)) {
      if (data.total_tokens !== undefined && data.input_tokens !== undefined && data.output_tokens !== undefined) {
        lines.push(`Tokens: ${data.total_tokens} (${data.input_tokens} in / ${data.output_tokens} out)`);
      } else {
        lines.push("Tokens: partial");
      }
    }
    if (data.created_at !== undefined) {
      const raw = data.created_at;
      let date: Date | null = null;
      if (typeof raw === "number") {
        const ms = raw < 1e12 ? raw * 1000 : raw;
        date = new Date(ms);
      } else if (typeof raw === "string") {
        const asNumber = Number(raw);
        if (!Number.isNaN(asNumber)) {
          const ms = asNumber < 1e12 ? asNumber * 1000 : asNumber;
          date = new Date(ms);
        } else {
          date = new Date(raw);
        }
      }
      if (date && !Number.isNaN(date.getTime())) {
        const iso = date.toISOString().replace("T", " ").replace("Z", "");
        lines.push(`Time: ${iso}`);
      }
    }
    return lines.join("\n");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) {
      setResult("No input provided");
      setDiagnostics({ error_source: "parsing" });
      setStatus("error");
      return;
    }

    const payload = text;
    setText("");
    setResult("");
    setDiagnostics({});
    setStatus("checking");

    try {
      const res = await fetch("/api/review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plan: payload,
          prompt_template: promptTemplate,
        }),
      });
      const data = await res.json();

      if (!res.ok || data.status === "error") {
        setResult(data.result || "Review failed");
        setDiagnostics(data.diagnostics || {});
        setStatus("error");
        return;
      }

      const resultText = String(data.result || "");
      setResult(resultText);
      setDiagnostics(data.diagnostics || {});
      if (resultText.startsWith("OK")) {
        setStatus("ok");
      } else if (resultText.startsWith("RED FLAGS")) {
        setStatus("warning");
      } else {
        setStatus("ok");
      }
    } catch (err) {
      setResult("Review failed — backend unavailable");
      setDiagnostics({ error_source: "network" });
      setStatus("error");
    }
  };

  const view = statusView();
  const hasDiagnostics = Object.keys(diagnostics).length > 0;
  const hasResult = result.trim().length > 0;
  const canSubmit = text.trim().length > 0 && status !== "checking";
  const diagnosticsText = formatDiagnostics(diagnostics);
  const { Title, Text } = Typography;
  const { Content, Header, Sider } = Layout;

  const suites = [
    { key: "overview", label: "Overview" },
    { key: "systems", label: "Systems" },
    { key: "profiles", label: "Profiles" },
  ];

  const suiteSections: Record<string, { key: string; label: string }[]> = {
    overview: [
      { key: "status", label: "Status" },
      { key: "configuration", label: "Configuration" },
      { key: "export", label: "Export" },
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

  const [suite, setSuite] = React.useState<string>("overview");
  const [section, setSection] = React.useState<string>("status");

  React.useEffect(() => {
    const firstSection = suiteSections[suite]?.[0];
    if (firstSection && !suiteSections[suite].some((item) => item.key === section)) {
      setSection(firstSection.key);
    }
  }, [suite, section]);

  const mainContent = (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Space align="center" size="middle">
        <Image src={`data:image/svg+xml;utf8,${SIGNAL_SVG_DATA}`} preview={false} width={22} />
        <Title level={2} style={{ margin: 0 }}>
          Control Point Review
        </Title>
      </Space>

      <Row gutter={[16, 16]} style={{ width: "100%" }}>
        <Col xs={24} md={16} lg={16}>
          <Card>
            <form onSubmit={handleSubmit}>
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Input.TextArea
                  placeholder="Paste plan text here..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  rows={12}
                />

                {isEditingPrompt && (
                  <Card type="inner" title="Prompt template">
                    <Input.TextArea
                      value={draftPrompt}
                      onChange={(e) => setDraftPrompt(e.target.value)}
                      rows={10}
                    />
                    <Space size="middle" style={{ marginTop: 8 }}>
                      <Button
                        type="link"
                        onClick={() => {
                          setPromptTemplate(draftPrompt);
                          window.localStorage.setItem("controlPointPromptTemplate", draftPrompt);
                          setIsEditingPrompt(false);
                        }}
                      >
                        Save
                      </Button>
                      <Button
                        type="link"
                        onClick={() => {
                          setDraftPrompt(promptTemplate);
                          setIsEditingPrompt(false);
                        }}
                      >
                        Cancel
                      </Button>
                    </Space>
                    <Text type="secondary" style={{ display: "block", marginTop: 8 }}>
                      Include <code>{"{{PLAN}}"}</code> where the submitted text should be injected.
                    </Text>
                  </Card>
                )}

                <Space align="center" size="middle">
                  <Button type="primary" htmlType="submit" disabled={!canSubmit}>
                    Submit
                  </Button>
                  <Button type="link" onClick={() => setIsEditingPrompt(true)}>
                    Edit prompt
                  </Button>
                </Space>
              </Space>
            </form>
          </Card>
        </Col>
        <Col xs={24} md={8} lg={8}>
          <Space direction="vertical" size="middle" style={{ width: "100%" }}>
            <Card>
              <Space align="center" size="small">
                <Badge status={view.badgeStatus} />
                <Text>{view.statusText}</Text>
              </Space>
            </Card>

            {hasResult && (
              <Card>
                <Text strong type={view.resultType} style={{ display: "block" }}>
                  {view.resultHeadline}
                </Text>
                <Text style={{ display: "block", marginTop: 8, whiteSpace: "pre-wrap" }}>
                  {result}
                </Text>
              </Card>
            )}

            {hasDiagnostics && (
              <Card size="small">
                <Text strong>Diagnostics</Text>
                <Text
                  type="secondary"
                  style={{
                    display: "block",
                    marginTop: 8,
                    whiteSpace: "pre-wrap",
                    fontFamily: "monospace",
                  }}
                >
                  {diagnosticsText}
                </Text>
              </Card>
            )}
          </Space>
        </Col>
      </Row>
    </Space>
  );

  if (embedded) {
    return mainContent;
  }

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ background: "#141414", borderBottom: "1px solid #1f1f1f" }}>
        <Menu
          mode="horizontal"
          theme="dark"
          selectedKeys={[suite]}
          items={suites}
          onClick={(info) => setSuite(info.key)}
        />
      </Header>
      <Layout>
        <Sider width={220} theme="dark" style={{ borderRight: "1px solid #1f1f1f" }}>
          <Menu
            mode="inline"
            theme="dark"
            selectedKeys={[section]}
            items={suiteSections[suite]}
            onClick={(info) => setSection(info.key)}
            style={{ height: "100%", borderRight: 0 }}
          />
        </Sider>
        <Content style={{ maxWidth: 1200, margin: "24px auto", padding: "0 16px", width: "100%" }}>
          {mainContent}
        </Content>
      </Layout>
    </Layout>
  );
}

export default ControlPointApp;
