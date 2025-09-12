declare namespace Office {
  namespace AsyncResultStatus {
    const Succeeded: string;
    const Failed: string;
  }

  namespace EventType {
    const DialogMessageReceived: string;
    const DialogEventReceived: string;
  }

  interface DialogMessageInfo {
    message: string;
    origin: string;
  }

  interface DialogErrorInfo {
    error: number;
  }

  interface DialogResult {
    status: string;
    value?: Dialog;
    error?: {
      message: string;
    };
  }

  interface Dialog {
    addEventHandler(eventType: string, handler: (arg: DialogMessageInfo | DialogErrorInfo) => void): void;
    close(): void;
  }

  interface NotificationMessage {
    type: string;
    message: string;
    icon: string;
    persistent: boolean;
  }

  interface NotificationMessages {
    replaceAsync(key: string, message: NotificationMessage): Promise<void>;
  }

  interface MailboxItem {
    notificationMessages: NotificationMessages;
  }

  interface Document {
    url: string;
  }

  namespace context {
    namespace ui {
      function displayDialogAsync(
        startAddress: string,
        options: { height: number; width: number; displayInIframe: boolean },
        callback: (result: DialogResult) => void
      ): void;
    }

    const mailbox: {
      item?: MailboxItem;
    };

    const document: Document;
  }
}

declare global {
  interface Window {
    Office: typeof Office;
  }
}
