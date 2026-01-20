import { Alert, Button, Space, Typography } from "antd";
import { useNavigate } from "react-router-dom";
import styles from "./Placeholder.module.css";

const { Title } = Typography;

type Props = {
  title: string;
  blocked?: boolean;
  blockedMessage?: string;
};

export default function Placeholder({ title, blocked = false, blockedMessage }: Props) {
  const navigate = useNavigate();

  if (blocked) {
    return (
      <Space direction="vertical" size="middle" className={styles.fullWidth}>
        <Title level={2}>{title}</Title>
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
      </Space>
    );
  }

  return <Title level={2}>{title}</Title>;
}
