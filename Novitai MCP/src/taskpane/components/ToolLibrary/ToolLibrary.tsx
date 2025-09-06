import * as React from "react";
import { Text, Spinner, makeStyles, tokens } from "@fluentui/react-components";
import { Toolbox24Regular } from "@fluentui/react-icons";
import ToolCard from "./ToolCard";
import { MCPTool } from "../../services/types";

interface ToolLibraryProps {
  tools: MCPTool[];
  loading: boolean;
  selectedTool: MCPTool | null;
  onToolSelect: (tool: MCPTool) => void;
}

const useStyles = makeStyles({
  container: {
    padding: "20px",
    height: "100%", // Take full height
    overflow: "hidden", // Prevent scrolling on container
    display: "flex",
    flexDirection: "column",
    minHeight: 0, // Allow container to shrink below content size
  },
  header: {
    marginBottom: "24px",
    textAlign: "center",
  },
  headerIcon: {
    width: "48px",
    height: "48px",
    borderRadius: "12px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    margin: "0 auto 16px",
  },
  headerTitle: {
    fontSize: "24px",
    fontWeight: "600",
    marginBottom: "8px",
    color: tokens.colorNeutralForeground1,
  },
  headerSubtitle: {
    fontSize: "16px",
    color: tokens.colorNeutralForeground2,
    lineHeight: "1.5",
  },
  toolGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
    gap: "20px",
    marginBottom: "24px",
    flex: 1, // Take remaining space
    overflowY: "auto", // Enable scrolling for tools
    paddingRight: "8px", // Space for scrollbar
    minHeight: 0, // Allow container to shrink below content size
  },
  loadingContainer: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    padding: "60px 20px",
    flexDirection: "column",
    gap: "16px",
  },
  emptyState: {
    textAlign: "center",
    padding: "60px 20px",
    color: tokens.colorNeutralForeground3,
  },
  statsContainer: {
    display: "flex",
    justifyContent: "center",
    gap: "32px",
    marginBottom: "32px",
    padding: "16px",
    backgroundColor: tokens.colorNeutralBackground2,
    borderRadius: tokens.borderRadiusMedium,
    border: `1px solid ${tokens.colorNeutralStroke1}`,
  },
  statItem: {
    textAlign: "center",
  },
  statNumber: {
    fontSize: "24px",
    fontWeight: "600",
    color: tokens.colorBrandForeground1,
  },
  statLabel: {
    fontSize: "14px",
    color: tokens.colorNeutralForeground2,
    marginTop: "4px",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
});

const ToolLibrary: React.FC<ToolLibraryProps> = ({
  tools,
  loading,
  selectedTool,
  onToolSelect,
}) => {
  const styles = useStyles();

  const getToolCategories = () => {
    const categories: { [key: string]: number } = {};
    tools.forEach((tool) => {
      const category = tool.name.split("_")[0];
      categories[category] = (categories[category] || 0) + 1;
    });
    return categories;
  };

  const categories = getToolCategories();

  if (loading) {
    return (
      <div className={styles.loadingContainer}>
        <Spinner size="large" />
        <Text size={400}>Loading AI tools...</Text>
      </div>
    );
  }

  if (tools.length === 0) {
    return (
      <div className={styles.emptyState}>
        <Text size={400} style={{ marginBottom: "8px" }}>
          No tools available
        </Text>
        <Text size={200}>Please check your connection to the MCP server</Text>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerIcon}>
          <Toolbox24Regular />
        </div>
        <div className={styles.headerTitle}>AI Tools Library</div>
        <div className={styles.headerSubtitle}>
          Powerful AI tools for document processing, research, and analysis
        </div>
      </div>

      <div className={styles.statsContainer}>
        <div className={styles.statItem}>
          <div className={styles.statNumber}>{tools.length}</div>
          <div className={styles.statLabel}>Total Tools</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statNumber}>{Object.keys(categories).length}</div>
          <div className={styles.statLabel}>Categories</div>
        </div>
        <div className={styles.statItem}>
          <div className={styles.statNumber}>
            {tools.filter((t) => t.parameters && Object.keys(t.parameters).length > 0).length}
          </div>
          <div className={styles.statLabel}>Configurable</div>
        </div>
      </div>

      <div className={styles.toolGrid}>
        {tools.map((tool) => (
          <ToolCard
            key={tool.name}
            tool={tool}
            onSelect={onToolSelect}
            isSelected={selectedTool?.name === tool.name}
          />
        ))}
      </div>
    </div>
  );
};

export default ToolLibrary;
