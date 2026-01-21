import { Alert, Typography } from "antd";
import PageHeader from "../components/PageHeader";
import ScreenLayout from "../components/ScreenLayout";

const { Paragraph } = Typography;

export default function Simulation() {
  // This is a placeholder for the simulation UI.
  // If backend is unavailable, show a warning, otherwise show simulation controls/UI.
  // You can expand this with real simulation logic as needed.
  let backendAvailable = true; // TODO: wire up real backend check if needed

  // For now, always show a message for demonstration
  return (
    <ScreenLayout
      header={<PageHeader title="Simulation" />}
      alert={
        backendAvailable ? null : (
          <Alert
            type="warning"
            message="No backend connection detected. Running in standalone simulation mode."
            showIcon
          />
        )
      }
      primary={
        <Paragraph>
          {/* Simulation UI goes here. Replace this with your actual simulation panel or WASM display. */}
          This is the simulation panel. Add your LVGL/WASM or other simulation display here.
        </Paragraph>
      }
    />
  );
}
