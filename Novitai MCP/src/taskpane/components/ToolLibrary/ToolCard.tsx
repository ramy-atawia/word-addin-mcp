import * as React from "react";
import { Text, Badge, makeStyles, tokens } from "@fluentui/react-components";
import type { GriffelStyle } from "@griffel/react";
import {
  Globe24Regular,
  DocumentText24Regular,
  Search24Regular,
  Toolbox24Regular,
  Play24Regular,
} from "@fluentui/react-icons";
import { MCPTool } from "../../services/types";

interface ToolCardProps {
  tool: MCPTool;
  onSelect: (tool: MCPTool) => void;
  isSelected?: boolean;
}

const useStyles = makeStyles({
  card: {
    cursor: "pointer",
    transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
    border: `2px solid ${tokens.colorNeutralStroke1}`,
    borderRadius: tokens.borderRadiusLarge,
    backgroundColor: tokens.colorNeutralBackground1,
    position: "relative",
    overflow: "hidden",
    "&:hover": {
      transform: "translateY(-8px) scale(1.02)",
      boxShadow: tokens.shadow16,
      borderColor: tokens.colorBrandStroke1,
      "&::before": {
        opacity: 1,
      },
    },
    "&::before": {
      content: '""',
      position: "absolute",
      top: 0,
      left: 0,
      right: 0,
      height: "4px",
      background: `linear-gradient(90deg, ${tokens.colorBrandBackground} 0%, ${tokens.colorBrandBackground2} 100%)`,
      opacity: 0,
      transition: "opacity 0.3s ease",
    },
  } as GriffelStyle,
  selectedCard: {
    borderColor: tokens.colorBrandStroke1,
    backgroundColor: tokens.colorBrandBackground2,
    boxShadow: tokens.shadow8,
    transform: "translateY(-4px)",
  } as GriffelStyle,
  header: {
    padding: tokens.spacingHorizontalL,
    position: "relative",
  } as GriffelStyle,
  icon: {
    width: tokens.spacingHorizontalXXXL,
    height: tokens.spacingHorizontalXXXL,
    borderRadius: tokens.borderRadiusLarge,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    marginBottom: tokens.spacingHorizontalM,
    backgroundColor: tokens.colorBrandBackground2,
    color: tokens.colorBrandForeground1,
    transition: "all 0.3s ease",
    position: "relative",
    "&::after": {
      content: '""',
      position: "absolute",
      top: "-2px",
      left: "-2px",
      right: "-2px",
      bottom: "-2px",
      borderRadius: tokens.borderRadiusLarge,
      background: `linear-gradient(45deg, ${tokens.colorBrandBackground}, ${tokens.colorBrandBackground2})`,
      zIndex: -1,
      opacity: 0,
      transition: "opacity 0.3s ease",
    },
  } as GriffelStyle,
  name: {
    fontSize: tokens.fontSizeBase500,
    fontWeight: "700",
    marginBottom: "12px",
    color: tokens.colorNeutralForeground1,
    transition: "color 0.3s ease",
  } as GriffelStyle,
  description: {
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground2,
    lineHeight: "1.6",
    marginBottom: "16px",
    transition: "color 0.3s ease",
  } as GriffelStyle,
  footer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: "16px",
    borderTop: `1px solid ${tokens.colorNeutralStroke1}`,
    transition: "border-color 0.3s ease",
  } as GriffelStyle,
  parameters: {
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorNeutralForeground3,
    display: "flex",
    alignItems: "center",
    gap: "4px",
  } as GriffelStyle,
  parameterIcon: {
    width: "16px",
    height: "16px",
    opacity: 0.7,
  } as GriffelStyle,
  selectButton: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    fontSize: tokens.fontSizeBase200,
    color: tokens.colorBrandForeground1,
    fontWeight: "600",
    padding: "8px 16px",
    borderRadius: tokens.borderRadiusSmall,
    backgroundColor: tokens.colorBrandBackground,
    transition: "all 0.3s ease",
    "&:hover": {
      backgroundColor: tokens.colorBrandBackground2,
      transform: "translateX(4px)",
    },
  } as GriffelStyle,
  toolType: {
    position: "absolute",
    top: "12px",
    right: "12px",
    padding: "4px 8px",
    fontSize: tokens.fontSizeBase100,
    fontWeight: "600",
    borderRadius: tokens.borderRadiusSmall,
    backgroundColor: tokens.colorNeutralBackground3,
    color: tokens.colorNeutralForeground2,
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  } as GriffelStyle,
});

const ToolCard: React.FC<ToolCardProps> = ({ tool, onSelect, isSelected = false }) => {
  const styles = useStyles();

  const getToolIcon = (toolName: string) => {
    switch (toolName) {
      case "web_content_fetcher":
        return <Globe24Regular />;
      case "text_processor":
        return <DocumentText24Regular />;
      case "file_reader":
        return <DocumentText24Regular />;
      case "document_analyzer":
        return <DocumentText24Regular />;
      case "data_formatter":
        return <Toolbox24Regular />;
      default:
        return <Toolbox24Regular />;
    }
  };

  const getToolColor = (toolName: string) => {
    switch (toolName) {
      case "web_content_fetcher":
        return {
          bg: tokens.colorStatusSuccessBackground1,
          color: tokens.colorStatusSuccessForeground1,
        };
      case "text_processor":
        return {
          bg: tokens.colorStatusWarningBackground1,
          color: tokens.colorStatusWarningForeground1,
        };
      case "file_reader":
        return {
          bg: tokens.colorStatusWarningBackground1,
          color: tokens.colorStatusWarningForeground1,
        };
      case "document_analyzer":
        return { bg: tokens.colorBrandBackground2, color: tokens.colorBrandForeground1 };
      case "data_formatter":
        return { bg: tokens.colorNeutralBackground3, color: tokens.colorNeutralForeground2 };
      default:
        return { bg: tokens.colorNeutralBackground3, color: tokens.colorNeutralForeground2 };
    }
  };

  const formatToolName = (name: string) => {
    return name.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
  };

  const getParameterCount = () => {
    if (!tool.parameters) return 0;
    return Object.keys(tool.parameters).length;
  };

  const colors = getToolColor(tool.name);

  return (
    <div
      className={`${styles.card} ${isSelected ? styles.selectedCard : ""}`}
      onClick={() => onSelect(tool)}
    >
      <div className={styles.toolType}>{tool.name.split("_")[0]}</div>
      <div className={styles.header}>
        <div className={styles.icon} style={{ backgroundColor: colors.bg, color: colors.color }}>
          {getToolIcon(tool.name)}
        </div>

        <div className={styles.name}>{formatToolName(tool.name)}</div>

        <div className={styles.description}>{tool.description}</div>

        <div className={styles.footer}>
          <div className={styles.parameters}>
            {getParameterCount()} parameter{getParameterCount() !== 1 ? "s" : ""}
          </div>

          <div className={styles.selectButton}>
            <Play24Regular />
            Select Tool
          </div>
        </div>
      </div>
    </div>
  );
};

export default ToolCard;
