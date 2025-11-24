import React, { useState, useRef, useEffect } from 'react';

// Minimal WebSocket test component
export const WebSocketDebugComponent: React.FC = () => {
  const [status, setStatus] = useState('disconnected');
  const [logs, setLogs] = useState<string[]>([]);
  const [url, setUrl] = useState('ws://localhost:8000/ws');
  const wsRef = useRef<WebSocket | null>(null);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log(logMessage);
    setLogs(prev => [...prev, logMessage]);
  };

  const connect = () => {
    addLog(`Attempting to connect to: ${url}`);
    setStatus('connecting');

    // Clean up existing connection
    if (wsRef.current) {
      addLog('Closing existing connection...');
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      addLog('Creating new WebSocket...');
      const ws = new WebSocket(url);
      wsRef.current = ws;
      addLog('WebSocket object created');

      ws.onopen = () => {
        addLog('✓ WebSocket connected!');
        setStatus('connected');
      };

      ws.onclose = (event) => {
        addLog(`WebSocket closed: ${event.code} - ${event.reason}`);
        setStatus('disconnected');
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        addLog('✗ WebSocket error occurred');
        console.error('WebSocket error:', error);
        setStatus('error');
      };

      ws.onmessage = (event) => {
        addLog(`← Received: ${event.data}`);
      };
    } catch (error) {
      addLog(`✗ Failed to create WebSocket: ${error}`);
      setStatus('error');
      console.error(error);
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      addLog('Disconnecting...');
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  // Clean up on unmount
  useEffect(() => {
    addLog('Component mounted');
    return () => {
      addLog('Component unmounting, cleaning up...');
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Log any URL changes
  useEffect(() => {
    addLog(`URL changed to: ${url}`);
  }, [url]);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>WebSocket Debug Component</h2>

      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{ width: '300px', marginRight: '10px' }}
        />
        <button onClick={connect} disabled={status === 'connected'}>
          Connect
        </button>
        <button onClick={disconnect} disabled={status !== 'connected'} style={{ marginLeft: '10px' }}>
          Disconnect
        </button>
      </div>

      <div style={{
        padding: '10px',
        backgroundColor: status === 'connected' ? '#4CAF50' :
                        status === 'error' ? '#f44336' :
                        status === 'connecting' ? '#ff9800' : '#999',
        color: 'white',
        borderRadius: '5px',
        marginBottom: '20px'
      }}>
        Status: {status}
      </div>

      <div style={{
        backgroundColor: '#f5f5f5',
        padding: '10px',
        height: '300px',
        overflow: 'auto',
        fontFamily: 'monospace',
        fontSize: '12px'
      }}>
        {logs.map((log, i) => (
          <div key={i}>{log}</div>
        ))}
      </div>

      <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
        <p>React StrictMode: {React.version.includes('18') ? 'May cause double renders' : 'Active'}</p>
        <p>Window location: {window.location.href}</p>
        <p>Protocol: {window.location.protocol}</p>
      </div>
    </div>
  );
};

// Export as default for easy import
export default WebSocketDebugComponent;