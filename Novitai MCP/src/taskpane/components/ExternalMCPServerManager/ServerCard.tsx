import React, { useState } from "react";
import {
  Button,
  Text,
  Badge,
  Spinner,
  Dialog,
  DialogSurface,
  DialogTitle,
  DialogBody,
  DialogContent,
  DialogActions,
} from "@fluentui/react-components";
import {
  Delete24Regular,
  Settings24Regular,
  Warning24Regular,
  CheckmarkCircle24Regular,
  ErrorCircle24Regular,
  Info24Regular,
  Toolbox24Regular,
} from "@fluentui/react-icons";

interface ServerCardProps {
  server: {
    id: string;
    name: string;
    url: string;
    status: "connected" | "disconnected" | "connecting" | "error";
    toolCount: number;
    lastSeen: string;
    health: {
      status: string;
      response_time?: number;
      error_message?: string;
      uptime?: string;
    };
  };
  onRemove: (serverId: string) => void;
  onRefresh: (serverId: string) => void;
}

export const ServerCard: React.FC<ServerCardProps> = ({ server, onRemove, onRefresh }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "connected":
        return "success";
      case "connecting":
        return "warning";
      case "error":
        return "danger";
      default:
        return "brand";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "connected":
        return <CheckmarkCircle24Regular />;
      case "connecting":
        return <Warning24Regular />;
      case "error":
        return <ErrorCircle24Regular />;
      default:
        return <Info24Regular />;
    }
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Simulate refresh
      await new Promise((resolve) => setTimeout(resolve, 1000));
      onRefresh(server.id);
      setSuccess("Server refreshed successfully!");
    } catch (err) {
      setError("Failed to refresh server");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemove = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Simulate removal
      await new Promise((resolve) => setTimeout(resolve, 1000));
      onRemove(server.id);
      setShowDeleteDialog(false);
    } catch (err) {
      setError("Failed to remove server");
    } finally {
      setIsLoading(false);
    }
  };

  const formatLastSeen = (lastSeen: string) => {
    try {
      const date = new Date(lastSeen);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / (1000 * 60));

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffMins < 1440) return `${Math.floor(diffMins / 60)}h ago`;
      return `${Math.floor(diffMins / 1440)}d ago`;
    } catch {
      return "Unknown";
    }
  };

  return (
    <>
      <div
        style={{
          backgroundColor: "var(--colorNeutralBackground1)",
          border: "1px solid var(--colorNeutralStroke1)",
          borderRadius: "var(--borderRadiusMedium)",
          padding: "20px",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginBottom: "16px",
          }}
        >
          <div style={{ flex: 1 }}>
            <div
              style={{
                fontSize: "18px",
                fontWeight: "bold",
                marginBottom: "8px",
              }}
            >
              {server.name}
            </div>
            <div
              style={{
                fontSize: "14px",
                color: "var(--colorNeutralForeground3)",
                fontFamily: "monospace",
              }}
            >
              {server.url}
            </div>
          </div>

          <Badge appearance="filled" color={getStatusColor(server.status)}>
            {getStatusIcon(server.status)}
            {server.status}
          </Badge>
        </div>

        <div style={{ marginBottom: "16px" }}>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(100px, 1fr))",
              gap: "12px",
              marginBottom: "16px",
            }}
          >
            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "var(--colorNeutralBackground2)",
                borderRadius: "var(--borderRadiusSmall)",
                border: "1px solid var(--colorNeutralStroke2)",
              }}
            >
              <div style={{ fontSize: "20px", fontWeight: "bold" }}>{server.toolCount}</div>
              <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>Tools</div>
            </div>
            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "var(--colorNeutralBackground2)",
                borderRadius: "var(--borderRadiusSmall)",
                border: "1px solid var(--colorNeutralStroke2)",
              }}
            >
              <div style={{ fontSize: "20px", fontWeight: "bold" }}>
                {server.health.response_time ? `${server.health.response_time}ms` : "N/A"}
              </div>
              <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>
                Response
              </div>
            </div>
            <div
              style={{
                textAlign: "center",
                padding: "12px",
                backgroundColor: "var(--colorNeutralBackground2)",
                borderRadius: "var(--borderRadiusSmall)",
                border: "1px solid var(--colorNeutralStroke2)",
              }}
            >
              <div style={{ fontSize: "20px", fontWeight: "bold" }}>
                {formatLastSeen(server.lastSeen)}
              </div>
              <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>
                Last Seen
              </div>
            </div>
          </div>

          <div style={{ marginBottom: "16px" }}>
            <Text size={400} weight="semibold" style={{ marginBottom: "8px" }}>
              Health Status
            </Text>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "8px 0",
                borderBottom: "1px solid var(--colorNeutralStroke2)",
              }}
            >
              <span>Status:</span>
              <span
                style={{
                  color:
                    server.health.status === "healthy"
                      ? "var(--colorPaletteGreenForeground1)"
                      : "var(--colorPaletteRedForeground1)",
                }}
              >
                {server.health.status}
              </span>
            </div>

            {server.health.uptime && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 0",
                  borderBottom: "1px solid var(--colorNeutralStroke2)",
                }}
              >
                <span>Uptime:</span>
                <span>{server.health.uptime}</span>
              </div>
            )}

            {server.health.error_message && (
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "8px 0",
                  borderBottom: "1px solid var(--colorNeutralStroke2)",
                }}
              >
                <span>Error:</span>
                <span style={{ color: "var(--colorPaletteRedForeground1)" }}>
                  {server.health.error_message}
                </span>
              </div>
            )}
          </div>

          {error && (
            <div
              style={{
                color: "var(--colorPaletteRedForeground1)",
                fontSize: "12px",
                marginBottom: "16px",
              }}
            >
              {error}
            </div>
          )}
          {success && (
            <div
              style={{
                color: "var(--colorPaletteGreenForeground1)",
                fontSize: "12px",
                marginBottom: "16px",
              }}
            >
              {success}
            </div>
          )}

          <div
            style={{
              display: "flex",
              gap: "8px",
              justifyContent: "flex-end",
              paddingTop: "16px",
              borderTop: "1px solid var(--colorNeutralStroke2)",
            }}
          >
            <Button
              appearance="subtle"
              icon={<Settings24Regular />}
              onClick={() => alert("Server settings - Coming Soon!")}
            >
              Settings
            </Button>
            <Button
              appearance="outline"
              icon={<Toolbox24Regular />}
              onClick={handleRefresh}
              disabled={isLoading}
            >
              {isLoading ? <Spinner size="tiny" /> : "Refresh"}
            </Button>
            <Button
              appearance="outline"
              icon={<Delete24Regular />}
              onClick={() => setShowDeleteDialog(true)}
              disabled={isLoading}
            >
              Remove
            </Button>
          </div>
        </div>
      </div>

      <Dialog
        open={showDeleteDialog}
        onOpenChange={(_, data) => !data.open && setShowDeleteDialog(false)}
      >
        <DialogSurface>
          <DialogTitle>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Warning24Regular />
              <Text weight="semibold">Remove Server</Text>
            </div>
          </DialogTitle>

          <DialogBody>
            <DialogContent>
              <Text>
                Are you sure you want to remove "{server.name}"? This action cannot be undone.
              </Text>
            </DialogContent>
          </DialogBody>

          <DialogActions>
            <Button
              appearance="subtle"
              onClick={() => setShowDeleteDialog(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button
              appearance="outline"
              onClick={handleRemove}
              disabled={isLoading}
              icon={<Delete24Regular />}
            >
              {isLoading ? "Removing..." : "Remove Server"}
            </Button>
          </DialogActions>
        </DialogSurface>
      </Dialog>
    </>
  );
};
