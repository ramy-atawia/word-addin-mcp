import * as React from "react";
import MCPToolManager from "./MCPToolManager";
import { makeStyles } from "@fluentui/react-components";

const useStyles = makeStyles({
  root: {
    minHeight: "100vh",
  },
});

const App: React.FC = () => {
  const styles = useStyles();

  return (
    <div className={styles.root}>
      <MCPToolManager />
    </div>
  );
};

export default App;
