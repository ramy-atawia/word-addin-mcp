// Auth0 configuration - will be set by environment
const auth0Config = {
  domain: window.AUTH0_DOMAIN || process.env.REACT_APP_AUTH0_DOMAIN || "dev-bktskx5kbc655wcl.us.auth0.com",
  clientId: window.AUTH0_CLIENT_ID || process.env.REACT_APP_AUTH0_CLIENT_ID || "INws849yDXaC6MZVXnLhMJi6CZC4nx6U",
  redirectUri: window.location.origin + "/auth-callback.html",
  scope: "openid profile email",
  audience: window.AUTH0_AUDIENCE || process.env.REACT_APP_AUTH0_AUDIENCE || (window.location.hostname.includes('dev') ? 
    "https://novitai-word-mcp-backend-dev.azurewebsites.net" : 
    "https://novitai-word-mcp-backend.azurewebsites.net"),
  cacheLocation: "memory",
  useRefreshTokens: true,
};

// Dialog instance
let dialog = null;

// Login function - opens the Auth0 login dialog
function login() {
  const dialogWidth = 35;
  const dialogHeight = 45;
  
  const dialogUrl = window.location.origin + window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/')) + '/login-dialog.html';
  
  Office.context.ui.displayDialogAsync(
      dialogUrl,
      { height: dialogHeight, width: dialogWidth, displayInIframe: false },
      function(result) {
          if (result.status === Office.AsyncResultStatus.Failed) {
              console.error("Dialog failed to open: " + result.error.message);
          } else {
              dialog = result.value;
              dialog.addEventHandler(Office.EventType.DialogMessageReceived, processDialogMessage);
              dialog.addEventHandler(Office.EventType.DialogEventReceived, processDialogClosed);
          }
      }
  );
}

// Process messages sent from the dialog
function processDialogMessage(arg) {
  try {
      const messageFromDialog = JSON.parse(arg.message);
      
      if (messageFromDialog.type === "auth-success") {
          try {
              const ev = new CustomEvent('auth-tokens', { 
                detail: { 
                  accessToken: messageFromDialog.accessToken || null, 
                  idToken: messageFromDialog.idToken || null, 
                  userProfile: messageFromDialog.userProfile || null 
                } 
              });
              window.dispatchEvent(ev);
          } catch (e) { 
            console.warn('Failed to dispatch auth-tokens event', e); 
          }
          
          if (dialog) {
              dialog.close();
              dialog = null;
          }
      } else if (messageFromDialog.type === "auth-error") {
          console.error("Authentication error: " + messageFromDialog.error);
          
          if (dialog) {
              dialog.close();
              dialog = null;
          }
      }
  } catch (error) {
      console.error("Error processing message: " + error);
  }
}

// Handle dialog closed event
function processDialogClosed(arg) {
  dialog = null;
}

// Logout function
function logout() {
  try { 
    window.dispatchEvent(new CustomEvent('auth-tokens', { 
      detail: { accessToken: null, idToken: null, userProfile: null } 
    })); 
  } catch (e) { 
    console.warn('Failed to clear auth tokens via event', e); 
  }
  showLoginUI();
}

// Expose for imports
if (typeof module !== 'undefined' && module.exports) {
  module.exports = auth0Config;
}
if (typeof window !== 'undefined') {
  window.__AUTH0_CONFIG__ = auth0Config;
}
