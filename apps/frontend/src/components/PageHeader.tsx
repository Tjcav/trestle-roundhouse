import { Flex, Space, Typography } from "antd";
import type { ReactNode } from "react";

type PageHeaderProps = {
  title: string;
  status?: ReactNode;
  extra?: ReactNode;
  children?: ReactNode;
};

export default function PageHeader({ title, status, extra, children }: PageHeaderProps) {
  return (
    <Space direction="vertical" size="small">
      <Flex justify="space-between" align="center">
        <Space align="center">
          <Typography.Title level={4}>{title}</Typography.Title>
          {status}
        </Space>
        {extra}
      </Flex>
      {children}
    </Space>
  );
}
