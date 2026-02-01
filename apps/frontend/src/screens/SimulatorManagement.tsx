import { Alert, Button, Card, Empty, Flex, Layout, Result, Select, Spin, Tooltip } from "antd";
import { ReloadOutlined } from "@ant-design/icons";
import { useEffect, useMemo, useState } from "react";
import PageHeader from "../components/PageHeader";
import SimulatorViewport from "../components/SimulatorViewport";

const compareVersions = (a: string, b: string) => {
  const aParts = a.split(".").map((part) => parseInt(part, 10));
  const bParts = b.split(".").map((part) => parseInt(part, 10));
  const max = Math.max(aParts.length, bParts.length);
  for (let i = 0; i < max; i += 1) {
    const av = aParts[i] ?? 0;
    const bv = bParts[i] ?? 0;
    if (av > bv) return -1;
    if (av < bv) return 1;
  }
  return 0;
};

export default function SimulatorManagement() {
  const simulatorBaseUrl =
    ((import.meta as any).env?.VITE_SIMULATOR_URL as string | undefined) ?? "/api/simulators/viewer";
  const [inventory, setInventory] = useState<
    {
      artifact_name: string;
      simulator_id: string;
      platform: string;
      version: string;
      release_tag: string;
      artifact_type: string;
      status: string;
      size_bytes: number;
      build_timestamp: string;
    }[]
  >([]);
  const [currentVersion, setCurrentVersion] = useState<string | null>(null);
  const [currentReleaseTag, setCurrentReleaseTag] = useState<string | null>(null);
  const [activeArtifactFilename, setActiveArtifactFilename] = useState<string | null>(null);
  const [loadingInventory, setLoadingInventory] = useState(true);
  const [loadingSelect, setLoadingSelect] = useState(false);
  const [inventoryError, setInventoryError] = useState<{ code: string; message: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastInventoryLoadedAt, setLastInventoryLoadedAt] = useState<number | null>(null);
  const [dropdownOpen, setDropdownOpen] = useState(false);

  const currentRecord = useMemo(
    () => inventory.find((item) => item.release_tag === currentReleaseTag && item.artifact_type === "wasm") || null,
    [inventory, currentReleaseTag],
  );

  const wasmInventory = inventory.filter((item) => item.artifact_type === "wasm");
  const selectOptions = wasmInventory.map((item) => ({
    value: item.release_tag,
    label: `${item.simulator_id} v${item.version} (${item.platform.toUpperCase()})`,
  }));
  const hasLoadedInventory = lastInventoryLoadedAt !== null;
  const isInitialLoading = loadingInventory && !hasLoadedInventory;

  const describeInventoryError = (error: { code: string; message: string }) => {
    switch (error.code) {
      case "REPO_AUTH_FAILED":
        return { title: "Cannot access repository", subtitle: "Authentication failed. Check your GitHub token." };
      case "REPO_FORBIDDEN":
        return { title: "Cannot access repository", subtitle: "Check credentials or repository permissions." };
      case "REPO_NOT_FOUND":
        return { title: "Repository not found", subtitle: "Check the configured repository name." };
      case "REPO_INVALID_URL":
        return { title: "Repository URL is invalid", subtitle: "Check configuration." };
      case "MANIFEST_INVALID_JSON":
      case "MANIFEST_SCHEMA_INVALID":
        return { title: "Release is invalid", subtitle: "The simulator manifest exists but failed validation." };
      case "MANIFEST_EMPTY":
        return { title: "Release is invalid", subtitle: "The simulator manifest contains no artifacts." };
      case "MANIFEST_PLATFORM_NOT_FOUND":
        return { title: "No simulator available", subtitle: "No WASM manifest found for this release." };
      default:
        return { title: "Unable to load simulators", subtitle: error.message };
    }
  };

  const loadInventory = async () => {
    setLoadingInventory(true);
      try {
        const [invRes, activeRes] = await Promise.all([
          fetch("/api/simulators/inventory"),
          fetch("/api/simulators/active"),
        ]);
        if (!invRes.ok) {
          const err = await invRes.json().catch(() => ({}));
          const detail = err?.detail ?? {};
          const code = detail?.error || err?.error || "UNKNOWN_ERROR";
          const message = detail?.message || err?.message || err?.detail || "Failed to load simulator inventory";
          throw { code, message };
        }
        if (!activeRes.ok) {
          const err = await activeRes.json().catch(() => ({}));
          throw new Error(err?.detail?.message || err?.detail || "Failed to load simulator selection");
        }
        const invData = await invRes.json();
        const activeData = await activeRes.json();
        setInventory(Array.isArray(invData) ? invData : []);
        setCurrentVersion(activeData.version || null);
        setCurrentReleaseTag(activeData.release_tag || null);
        setActiveArtifactFilename(activeData.artifact_filename || null);
        setLastInventoryLoadedAt(Date.now());
        setInventoryError(null);
      } catch (error: any) {
        if (error?.code && error?.message) {
          setInventoryError({ code: error.code, message: error.message });
        } else {
          setInventoryError({ code: "UNKNOWN_ERROR", message: error?.message || "Unable to load simulators" });
        }
      } finally {
        setLoadingInventory(false);
      }
    };

  useEffect(() => {
    loadInventory();
  }, []);

  useEffect(() => {
    if (loadingInventory || currentReleaseTag || wasmInventory.length === 0) return;
    const sorted = [...wasmInventory].sort((a, b) => {
      if (a.build_timestamp && b.build_timestamp) {
        return b.build_timestamp.localeCompare(a.build_timestamp);
      }
      return compareVersions(a.version, b.version);
    });
    handleSelect(sorted[0].release_tag);
  }, [loadingInventory, currentReleaseTag, wasmInventory]);

  const refreshManifest = async (options?: { silent?: boolean }) => {
    setRefreshing(true);
    if (!options?.silent) {
      setInventoryError(null);
    }
    try {
      const res = await fetch("/api/simulators/refresh-manifest", { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        const detail = err?.detail ?? {};
        const code = detail?.error || err?.error || "UNKNOWN_ERROR";
        const message = detail?.message || err?.message || err?.detail || "Failed to refresh simulator manifest";
        throw { code, message };
      }
      await loadInventory();
    } catch (error: any) {
      if (error?.code && error?.message) {
        setInventoryError({ code: error.code, message: error.message });
      } else {
        setInventoryError({ code: "UNKNOWN_ERROR", message: error?.message || "Unable to refresh manifest" });
      }
    } finally {
      setRefreshing(false);
    }
  };

  const handleSelect = async (releaseTag: string) => {
    setLoadingSelect(true);
    setLoadError(null);
    try {
      const res = await fetch("/api/simulators/select", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ release_tag: releaseTag }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail?.message || err?.detail || `Failed to load simulator ${releaseTag}`);
      }
      const selected = wasmInventory.find((item) => item.release_tag === releaseTag) || null;
      setCurrentReleaseTag(releaseTag);
      setCurrentVersion(selected?.version || currentVersion);
      setActiveArtifactFilename(selected?.artifact_name || activeArtifactFilename);
    } catch (error: any) {
      setLoadError(error?.message || "Failed to load simulator");
    } finally {
      setLoadingSelect(false);
    }
  };

  const content = () => {
    if (isInitialLoading) {
      return (
        <Card bodyStyle={{ padding: 24 }} style={{ flex: 1, minHeight: 360 }}>
          <Spin size="large" tip="Loading simulators…" />
        </Card>
      );
    }

    if (inventoryError && inventoryError.code !== "MANIFEST_NOT_FOUND" && wasmInventory.length === 0) {
      const copy = describeInventoryError(inventoryError);
      return (
        <Card bodyStyle={{ padding: 24 }} style={{ flex: 1, minHeight: 360 }}>
          <Result
            status="error"
            title={copy.title}
            subTitle={copy.subtitle}
            extra={
              <Button onClick={() => refreshManifest()} icon={<ReloadOutlined />} loading={refreshing || loadingInventory}>
                Reload list
              </Button>
            }
          />
        </Card>
      );
    }

    if (wasmInventory.length === 0) {
      return (
        <Card bodyStyle={{ padding: 24 }} style={{ flex: 1, minHeight: 360 }}>
          <Result
            status="info"
            title="No simulators available"
            subTitle="No releases found for this project."
            extra={
              <Button onClick={() => refreshManifest()} icon={<ReloadOutlined />} loading={refreshing || loadingInventory}>
                Refresh
              </Button>
            }
          />
        </Card>
      );
    }

    const artifactRef = activeArtifactFilename ?? currentRecord?.artifact_name ?? null;
    return (
      <Card bodyStyle={{ padding: 0 }} style={{ flex: 1, minHeight: 360 }}>
        <div style={{ position: "relative", width: "100%", height: "100%" }}>
          <SimulatorViewport artifactRef={artifactRef} viewerUrl={simulatorBaseUrl} />
          {loadingSelect ? (
            <div
              style={{
                position: "absolute",
                inset: 0,
                background: "rgba(15, 17, 21, 0.55)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                zIndex: 1,
              }}
            >
              <Spin tip="Loading simulator…" size="large" />
            </div>
          ) : null}
        </div>
      </Card>
    );
  };

  return (
    <Layout style={{ height: "100%", overflowX: "hidden" }}>
      <PageHeader
        title="Simulator"
        extra={
          <Flex align="center" gap={8}>
            <Select
              placeholder="Select simulator"
              loading={false}
              value={currentReleaseTag}
              options={selectOptions}
              onChange={handleSelect}
              onDropdownVisibleChange={(open) => {
                setDropdownOpen(open);
              }}
              notFoundContent={
                dropdownOpen && loadingInventory ? (
                  <Spin size="small" />
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No simulators" />
                )
              }
              disabled={loadingInventory || refreshing}
              style={{ minWidth: 240 }}
            />
            <Tooltip
              title="Refresh manifest"
              getPopupContainer={() => document.body}
              placement="bottom"
              overlayStyle={{ maxWidth: 240, whiteSpace: "nowrap" }}
            >
              <Button
                icon={<ReloadOutlined />}
                onClick={() => refreshManifest()}
                loading={refreshing}
                disabled={refreshing || loadingInventory}
                type="text"
              />
            </Tooltip>
          </Flex>
        }
      />
      <Layout.Content style={{ flex: 1, display: "flex", flexDirection: "column", gap: 16, overflow: "hidden", overflowX: "hidden" }}>
        {inventoryError && inventoryError.code !== "MANIFEST_NOT_FOUND" && wasmInventory.length > 0 ? (
          <Alert type="error" message={inventoryError.message} showIcon />
        ) : null}
        {loadError ? (
          <Alert
            type="error"
            message={
              currentRecord ? `Failed to load simulator v${currentRecord.version}` : "Failed to load simulator"
            }
            action={
              <Button size="small" onClick={() => currentReleaseTag && handleSelect(currentReleaseTag)}>
                Retry
              </Button>
            }
            showIcon
          />
        ) : null}
        {content()}
      </Layout.Content>
    </Layout>
  );
}
