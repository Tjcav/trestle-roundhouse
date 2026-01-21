import { Space } from "antd";
import type { ReactNode } from "react";

type ScreenLayoutProps = {
  header: ReactNode;
  alert?: ReactNode;
  actions?: ReactNode;
  primary?: ReactNode;
  secondary?: ReactNode;
};

export default function ScreenLayout({ header, alert, actions, primary, secondary }: ScreenLayoutProps) {
  return (
    <Space direction="vertical" size="large">
      {header}
      {alert}
      {actions}
      {primary}
      {secondary}
    </Space>
  );
}
