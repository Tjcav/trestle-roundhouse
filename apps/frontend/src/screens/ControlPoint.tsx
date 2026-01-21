import ControlPointApp from "../../../control-point/frontend/src/App";
import PageHeader from "../components/PageHeader";
import ScreenLayout from "../components/ScreenLayout";

export default function ControlPoint() {
  return <ScreenLayout header={<PageHeader title="Control Point" />} primary={<ControlPointApp embedded />} />;
}
