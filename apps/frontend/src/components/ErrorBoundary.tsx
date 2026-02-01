import React from "react";

type ErrorBoundaryState = {
  error: Error | null;
};

export default class ErrorBoundary extends React.Component<React.PropsWithChildren, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error("UI error boundary caught:", error);
  }

  render() {
    const { error } = this.state;
    if (error) {
      return (
        <div style={{ padding: 24, color: "#e6eaf2", fontFamily: "Segoe UI, Tahoma, Geneva, Verdana, sans-serif" }}>
          <h1 style={{ margin: 0, fontSize: 20 }}>Something went wrong</h1>
          <p style={{ marginTop: 8, opacity: 0.8 }}>{error.message}</p>
        </div>
      );
    }
    return this.props.children;
  }
}
