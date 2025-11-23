/**
 * TypeScript definitions for Electron API exposed via context bridge
 */

interface AudioDevice {
  deviceId: string;
  label: string;
  kind: string;
  groupId?: string;
}

interface ElectronAPI {
  recording: {
    start: () => Promise<{ success: boolean; message: string }>;
    stop: () => Promise<{ success: boolean; message: string }>;
  };

  audio: {
    getDevices: () => Promise<{ success: boolean; devices: AudioDevice[] }>;
    updateSettings: (settings: Record<string, any>) => Promise<{ success: boolean }>;
  };

  transcription: {
    process: (audioData: ArrayBuffer | Blob) => Promise<{
      success: boolean;
      text: string;
      confidence: number;
    }>;
    onUpdate: (callback: (data: any) => void) => () => void;
  };

  window: {
    minimize: () => Promise<void>;
    maximize: () => Promise<void>;
    close: () => Promise<void>;
    hide: () => Promise<void>;
    show: () => Promise<void>;
    onStateChange: (callback: (state: any) => void) => () => void;
  };

  app: {
    getVersion: () => Promise<string>;
    getPath: (name: string) => Promise<string>;
    on: (channel: string, callback: (...args: any[]) => void) => () => void;
  };

  settings: {
    get: () => Promise<Record<string, any>>;
    update: (settings: Record<string, any>) => Promise<{ success: boolean }>;
    reset: () => Promise<{ success: boolean }>;
    onChange: (callback: (settings: Record<string, any>) => void) => () => void;
  };

  isDev: () => boolean;
  platform: string;
  send: (channel: string, data: any) => void;
  invoke: (channel: string, ...args: any[]) => Promise<any>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
    __electronAPIVersion?: string;
  }
}

export {};
