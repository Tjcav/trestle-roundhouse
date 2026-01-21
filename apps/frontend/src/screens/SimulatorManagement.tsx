import { Alert, Card, Col, Row, Space } from "antd";
import SimulatorStatusHeader from "../components/SimulatorStatusHeader";
import SimulatorTable from "../components/SimulatorTable";
import SimulatorActions from "../components/SimulatorActions";
import SimulatorAuditLog from "../components/SimulatorAuditLog";
import { useState } from "react";
import ScreenLayout from "../components/ScreenLayout";

export default function SimulatorManagement() {
  const [systemError, setSystemError] = useState<string | null>(null);
  const [operationError, setOperationError] = useState<{ key: "refresh" | "rollback"; message: string } | null>(
    null,
  );

  const handleSystemError = (message: string | null) => {
    setSystemError(message);
    if (message) {
      setOperationError(null);
    }
  };

  const handleOperationError = (error: { key: "refresh" | "rollback"; message: string }) => {
    if (systemError) return;
    setOperationError(error);
  };

  const clearOperationError = (key: "refresh" | "rollback") => {
    if (operationError?.key === key) {
      setOperationError(null);
    }
  };

  return (
    <ScreenLayout
      header={<SimulatorStatusHeader />}
      alert={systemError ? <Alert type="error" message={systemError} showIcon /> : null}
      actions={
        <Space direction="vertical" size="small" align="end">
          <Row justify="end">
            <Col>
              <SimulatorActions
                onOperationError={handleOperationError}
                onOperationSuccess={clearOperationError}
                disabled={Boolean(systemError)}
              />
            </Col>
          </Row>
          {!systemError && operationError ? (
            <Alert type="error" message={operationError.message} showIcon />
          ) : null}
        </Space>
      }
      primary={
        <Card title="Available Simulators">
          <SimulatorTable
            onSystemError={handleSystemError}
            disableActions={Boolean(systemError)}
            suppressActionErrors={Boolean(systemError || operationError)}
          />
        </Card>
      }
      secondary={
        <Card size="small">
          <SimulatorAuditLog />
        </Card>
      }
    />
  );
}
