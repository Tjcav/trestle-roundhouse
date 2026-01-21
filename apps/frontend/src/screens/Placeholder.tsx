import { Alert, Button } from "antd";
import { useNavigate } from "react-router-dom";
import PageHeader from "../components/PageHeader";
import ScreenLayout from "../components/ScreenLayout";

type Props = {
  title: string;
  blocked?: boolean;
  blockedMessage?: string;
};

export default function Placeholder({ title, blocked = false, blockedMessage }: Props) {
  const navigate = useNavigate();

  const header = <PageHeader title={title} />;

  if (blocked) {
    return (
      <ScreenLayout
        header={header}
        alert={
          <Alert
            type="warning"
            message={blockedMessage || "This tool is unavailable."}
            description={
              <Button type="link" onClick={() => navigate("/systems/environments")}>
                View environment status
              </Button>
            }
            showIcon
          />
        }
      />
    );
  }

  return <ScreenLayout header={header} />;
}
