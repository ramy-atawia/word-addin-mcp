import * as React from "react";
import { createRoot } from "react-dom/client";
import App from "./components/App";
import { FluentProvider, webLightTheme } from "@fluentui/react-components";

/* global document, Office, module, require, HTMLElement */

// Suppress Office telemetry errors in console
const originalConsoleError = console.error;
console.error = (...args) => {
  const message = args[0];
  if (typeof message === "string") {
    // Filter out Office telemetry errors
    if (
      message.includes("word-telemetry.officeapps.live.com") ||
      message.includes("RemoteTelemetry.ashx") ||
      message.includes("RemoteUls.ashx") ||
      message.includes("Access to XMLHttpRequest") ||
      message.includes("CORS policy")
    ) {
      return; // Don't log these errors
    }
  }
  originalConsoleError.apply(console, args);
};

// Suppress Office telemetry fetch errors
const originalFetch = window.fetch;
window.fetch = function (...args) {
  const url = args[0];
  if (typeof url === "string" && url.includes("word-telemetry.officeapps.live.com")) {
    // Return a rejected promise for telemetry requests to prevent errors
    return Promise.reject(new Error("Telemetry blocked"));
  }
  return originalFetch.apply(this, args);
};

const rootElement: HTMLElement | null = document.getElementById("container");
const root = rootElement ? createRoot(rootElement) : undefined;

/* Render application after Office initializes */
Office.onReady(() => {
  root?.render(
    <FluentProvider theme={webLightTheme}>
      <App />
    </FluentProvider>
  );
});

if ((module as any).hot) {
  (module as any).hot.accept("./components/App", () => {
    const NextApp = require("./components/App").default;
    root?.render(
      <FluentProvider theme={webLightTheme}>
        <NextApp />
      </FluentProvider>
    );
  });
}
