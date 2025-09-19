import React, { useState } from 'react';
import './LoginForm.css';

export const LoginForm: React.FC = () => {
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const openLoginDialog = async (): Promise<void> => {
    try {
      setIsLoading(true);
      
      // Use Office.js dialog for proper Auth0 integration
      if (window.Office && window.Office.context && window.Office.context.ui) {
        const dialogWidth = 35;
        const dialogHeight = 45;
        // Use complete URL construction like reference
        const dialogUrl = window.location.origin + window.location.pathname.substring(0, window.location.pathname.lastIndexOf('/')) + '/login-dialog.html';
        
        window.Office.context.ui.displayDialogAsync(
          dialogUrl,
          { height: dialogHeight, width: dialogWidth, displayInIframe: false },
          (result) => {
            if (result.status === window.Office.AsyncResultStatus.Failed) {
              console.error("Dialog failed to open: " + result.error.message);
              setIsLoading(false);
            } else {
              const dialog = result.value;
              
              // Event handler for messages from the dialog
              dialog.addEventHandler(window.Office.EventType.DialogMessageReceived, (arg: any) => {
                try {
                  // Check if arg has message property (success case)
                  if ('message' in arg) {
                    const messageFromDialog = JSON.parse(arg.message);
                    
                    if (messageFromDialog.type === "auth-success") {
                      // Dispatch auth-tokens event
                      const ev = new CustomEvent('auth-tokens', { 
                        detail: { 
                          accessToken: messageFromDialog.accessToken || null, 
                          idToken: messageFromDialog.idToken || null, 
                          userProfile: messageFromDialog.userProfile || null 
                        } 
                      });
                      window.dispatchEvent(ev);
                      
                      // Close the dialog
                      dialog.close();
                      setIsLoading(false);
                    } else if (messageFromDialog.type === "auth-error") {
                      console.error("Authentication error: " + messageFromDialog.error);
                      dialog.close();
                      setIsLoading(false);
                    }
                  } else if ('error' in arg) {
                    // Handle error case
                    console.error("Dialog error: " + arg.error);
                    dialog.close();
                    setIsLoading(false);
                  }
                } catch (error) {
                  console.error("Error processing message: " + error);
                  setIsLoading(false);
                }
              });
              
              // Event handler for dialog close event
              dialog.addEventHandler(window.Office.EventType.DialogEventReceived, () => {
                setIsLoading(false);
              });
            }
          }
        );
      } else {
        // Fallback for non-Office environment
        const dialogUrl = `${window.location.origin}/login-dialog.html`;
        window.open(dialogUrl, 'auth', 'width=600,height=700');
        setIsLoading(false);
      }
    } catch (error) {
      console.error('Failed to open login dialog:', error);
      setIsLoading(false);
    }
  };

  return (
    <div className="login-form-container">
      <div className="login-header">
        <div className="header-logo-container">
          <img 
            src="/assets/NovitaiPatentLogo3-removebg-preview.png" 
            alt="NovitAI Logo" 
            className="header-logo large"
          />
        </div>
        <div className="header-text">
          <h2>Welcome to NovitAI MCP</h2>
          <p>Your AI-powered patent drafting companion</p>
        </div>
      </div>
      
      <div className="login-description">
        <h3>What you can do:</h3>
        <ul>
          <li>Generate comprehensive patent claims using AI</li>
          <li>Search and analyze prior art efficiently</li>
          <li>Create professional patent reports</li>
          <li>Get intelligent drafting suggestions</li>
          <li>Export content directly to Word documents</li>
        </ul>
      </div>
      
      <div className="login-form">
        <button 
          onClick={openLoginDialog}
          className="login-button primary"
          disabled={isLoading}
        >
          {isLoading ? 'Opening login...' : 'Sign In with Auth0'}
        </button>
      </div>
      
      <div className="login-footer">
        <p>Secure authentication powered by Auth0</p>
        <p>Your data is protected and never shared</p>
      </div>
    </div>
  );
};
