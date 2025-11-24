import React, { useState, useRef, useEffect } from 'react';

// Minimal WebSocket test component for debugging
export const WebSocketDebug: React.FC = () => {
  const [status, setStatus] = useState('disconnected');
  const [logs, setLogs] = useState<string[]>([]);
  const [url, setUrl] = useState('ws://localhost:8000/ws');
  const wsRef = useRef<WebSocket | null>(null);
  const renderCount = useRef(0);

  renderCount.current++;

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const logMessage = `[${timestamp}] ${message}`;
    console.log('[WebSocketDebug]', logMessage);
    setLogs(prev => [...prev.slice(-19), logMessage]); // Keep last 20 logs
  };

  const testDirectConnection = () => {
    addLog('Testing direct WebSocket creation (no React state)...');
    try {
      const testWs = new WebSocket('ws://localhost:8000/ws');
      addLog(`Direct WebSocket created, readyState: ${testWs.readyState}`);

      testWs.onopen = () => {
        addLog('✓ Direct WebSocket opened successfully!');
        testWs.close();
      };

      testWs.onerror = (e) => {
        addLog('✗ Direct WebSocket error');
        console.error('Direct WebSocket error:', e);
      };

      testWs.onclose = () => {
        addLog('Direct WebSocket closed');
      };

      // Timeout check
      setTimeout(() => {
        if (testWs.readyState === WebSocket.CONNECTING) {
          addLog('⚠ Direct WebSocket still connecting after 3s');
          testWs.close();
        }
      }, 3000);
    } catch (e) {
      addLog(`✗ Exception creating direct WebSocket: ${e}`);
      console.error('Direct WebSocket exception:', e);
    }
  };

  const connect = () => {
    addLog(`Render #${renderCount.current}: Attempting to connect to: ${url}`);
    setStatus('connecting');

    if (wsRef.current) {
      addLog('Closing existing connection...');
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      addLog('Creating new WebSocket...');
      addLog(`URL type: ${typeof url}, value: "${url}"`);
      addLog(`Window location: ${window.location.href}`);

      const ws = new WebSocket(url);
      wsRef.current = ws;
      addLog(`WebSocket created, readyState: ${ws.readyState}`);

      ws.onopen = () => {
        addLog('✓ WebSocket connected!');
        setStatus('connected');
      };

      ws.onclose = (event) => {
        addLog(`WebSocket closed: code=${event.code}, reason="${event.reason}"`);
        setStatus('disconnected');
        wsRef.current = null;
      };

      ws.onerror = (error) => {
        addLog('✗ WebSocket error occurred');
        console.error('WebSocket error details:', error);
        console.error('WebSocket target:', (error as any).target);
        setStatus('error');
      };

      ws.onmessage = (event) => {
        addLog(`← Received: ${event.data.substring(0, 100)}`);
      };
    } catch (error) {
      addLog(`✗ Exception: ${error}`);
      console.error('WebSocket exception:', error);
      setStatus('error');
    }
  };

  const disconnect = () => {
    if (wsRef.current) {
      addLog('Disconnecting...');
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  useEffect(() => {
    addLog(`Component mounted (render #${renderCount.current})`);

    // Test if WebSocket is available
    if (typeof WebSocket !== 'undefined') {
      addLog('✓ WebSocket API is available');
    } else {
      addLog('✗ WebSocket API is NOT available!');
    }

    return () => {
      addLog('Component unmounting...');
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  return (
    <div style={{
      padding: '20px',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: '#f0f0f0',
      borderRadius: '8px',
      margin: '20px'
    }}>
      <h2>WebSocket Debug Component</h2>
      <p>Render count: {renderCount.current}</p>

      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          style={{
            width: '400px',
            padding: '8px',
            marginRight: '10px',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        />
      </div>

      <div style={{ marginBottom: '20px' }}>
        <button
          onClick={connect}
          disabled={status === 'connected'}
          style={{ marginRight: '10px', padding: '8px 16px' }}
        >
          Connect
        </button>
        <button
          onClick={disconnect}
          disabled={status !== 'connected'}
          style={{ marginRight: '10px', padding: '8px 16px' }}
        >
          Disconnect
        </button>
        <button
          onClick={testDirectConnection}
          style={{ padding: '8px 16px' }}
        >
          Test Direct Connection
        </button>
      </div>

      <div style={{
        padding: '10px',
        backgroundColor:
          status === 'connected' ? '#4CAF50' :
          status === 'error' ? '#f44336' :
          status === 'connecting' ? '#ff9800' : '#999',
        color: 'white',
        borderRadius: '4px',
        marginBottom: '20px'
      }}>
        Status: {status}
      </div>

      <div style={{
        backgroundColor: 'white',
        border: '1px solid #ddd',
        padding: '10px',
        height: '300px',
        overflow: 'auto',
        fontFamily: 'monospace',
        fontSize: '12px',
        whiteSpace: 'pre-wrap'
      }}>
        {logs.map((log, i) => (
          <div key={i}>{log}</div>
        ))}
      </div>

      <div style={{
        marginTop: '20px',
        fontSize: '11px',
        color: '#666',
        backgroundColor: 'white',
        padding: '10px',
        borderRadius: '4px'
      }}>
        <div>React Version: {React.version}</div>
        <div>Window Location: {window.location.href}</div>
        <div>Protocol: {window.location.protocol}</div>
        <div>Hostname: {window.location.hostname}</div>
        <div>Port: {window.location.port || '(default)'}</div>
        <div>User Agent: {navigator.userAgent.substring(0, 50)}...</div>
      </div>
    </div>
  );
};

export default WebSocketDebug;