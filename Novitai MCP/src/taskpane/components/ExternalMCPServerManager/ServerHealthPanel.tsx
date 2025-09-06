import React, { useState, useEffect } from "react";
import { Button, Text, Badge, Spinner } from "@fluentui/react-components";
import {
  Warning24Regular,
  CheckmarkCircle24Regular,
  ErrorCircle24Regular,
  Info24Regular,
  Toolbox24Regular,
  Settings24Regular,
} from "@fluentui/react-icons";

interface ServerHealthData {
  id: string;
  name: string;
  url: string;
  status: "healthy" | "warning" | "error" | "unknown";
  response_time?: number;
  uptime?: string;
  last_check: string;
  error_message?: string;
}

export const ServerHealthPanel: React.FC = () => {
  const [servers, setServers] = useState<ServerHealthData[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    loadHealthData();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(loadHealthData, 30000); // Refresh every 30 seconds
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const loadHealthData = async () => {
    setIsLoading(true);
    try {
      // Simulate loading health data
      await new Promise((resolve) => setTimeout(resolve, 1000));

      // Simulate some server data
      setServers([
        {
          id: "1",
          name: "GitHub MCP Server",
          url: "https://api.github.com/mcp",
          status: "healthy",
          response_time: 45,
          uptime: "99.9%",
          last_check: new Date().toISOString(),
        },
        {
          id: "2",
          name: "Slack MCP Server",
          url: "https://api.slack.com/mcp",
          status: "warning",
          response_time: 120,
          uptime: "98.5%",
          last_check: new Date().toISOString(),
          error_message: "High response time",
        },
      ]);
      setError(null);
    } catch (err) {
      setError("Failed to load health data");
    } finally {
      setIsLoading(false);
    }
  };

  const refreshHealthData = async () => {
    setError(null);
    setSuccess(null);
    await loadHealthData();
    setSuccess("Health data refreshed successfully!");
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy":
        return "success";
      case "warning":
        return "warning";
      case "error":
        return "danger";
      default:
        return "brand";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy":
        return <CheckmarkCircle24Regular />;
      case "warning":
        return <Warning24Regular />;
      case "error":
        return <ErrorCircle24Regular />;
      default:
        return <Info24Regular />;
    }
  };

  const getTotalServers = () => servers.length;
  const getHealthyServers = () => servers.filter((s) => s.status === "healthy").length;
  const getWarningServers = () => servers.filter((s) => s.status === "warning").length;
  const getErrorServers = () => servers.filter((s) => s.status === "error").length;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "16px",
        height: "100%",
        padding: "16px",
      }}
    >
      <div
        style={{
          backgroundColor: "var(--colorNeutralBackground1)",
          border: "1px solid var(--colorNeutralStroke1)",
          borderRadius: "var(--borderRadiusMedium)",
          padding: "20px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "12px",
            }}
          >
            <Text size={600} weight="semibold">
              Server Health Monitor
            </Text>
            <Badge appearance="filled" color="brand">
              {servers.length} Servers
            </Badge>
          </div>
          <div
            style={{
              display: "flex",
              gap: "8px",
            }}
          >
            <Button
              icon={<Settings24Regular />}
              onClick={() => alert("Health Settings - Coming Soon!")}
              appearance="subtle"
            >
              Settings
            </Button>
            <Button
              icon={<Toolbox24Regular />}
              onClick={refreshHealthData}
              disabled={isLoading}
              appearance="outline"
            >
              {isLoading ? <Spinner size="tiny" /> : "Refresh"}
            </Button>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
            gap: "16px",
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
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>{getTotalServers()}</div>
            <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>
              Total Servers
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
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>{getHealthyServers()}</div>
            <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>Healthy</div>
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
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>{getWarningServers()}</div>
            <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>Warning</div>
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
            <div style={{ fontSize: "24px", fontWeight: "bold" }}>{getErrorServers()}</div>
            <div style={{ fontSize: "12px", color: "var(--colorNeutralForeground3)" }}>Errors</div>
          </div>
        </div>
      </div>

      {error && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--borderRadiusMedium)",
            border: "1px solid var(--colorNeutralStroke2)",
            backgroundColor: "var(--colorNeutralBackground2)",
          }}
        >
          <Text color="danger">{error}</Text>
        </div>
      )}

      {success && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "var(--borderRadiusMedium)",
            border: "1px solid var(--colorNeutralStroke2)",
            backgroundColor: "var(--colorNeutralBackground2)",
          }}
        >
          <Text color="success">{success}</Text>
        </div>
      )}

      <div
        style={{
          backgroundColor: "var(--colorNeutralBackground1)",
          border: "1px solid var(--colorNeutralStroke1)",
          borderRadius: "var(--borderRadiusMedium)",
          padding: "20px",
          flex: 1,
        }}
      >
        <Text size={500} weight="semibold" style={{ marginBottom: "16px" }}>
          Server Health Status
        </Text>

        {isLoading ? (
          <div style={{ textAlign: "center", padding: "16px" }}>
            <Spinner size="large" label="Loading health data..." />
          </div>
        ) : servers.length === 0 ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              padding: "40px 20px",
              textAlign: "center",
            }}
          >
            <Info24Regular
              style={{
                fontSize: "48px",
                color: "var(--colorNeutralForeground3)",
                marginBottom: "16px",
              }}
            />
            <Text size={500} color="neutralSecondary">
              No servers configured for health monitoring
            </Text>
            <Text size={300} color="neutralTertiary" style={{ marginBottom: "16px" }}>
              Add external MCP servers to start monitoring their health
            </Text>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
            {servers.map((server) => (
              <div
                key={server.id}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "16px",
                  borderBottom:
                    server.id === servers[servers.length - 1]?.id
                      ? "none"
                      : "1px solid var(--colorNeutralStroke2)",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "4px",
                  }}
                >
                  <div
                    style={{
                      fontSize: "16px",
                      fontWeight: "600",
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

                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <Badge appearance="filled" color={getStatusColor(server.status)}>
                    {getStatusIcon(server.status)}
                    {server.status}
                  </Badge>

                  {server.response_time && (
                    <Text size={300} color="neutralSecondary">
                      {server.response_time}ms
                    </Text>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
