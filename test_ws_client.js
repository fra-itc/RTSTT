// Simple WebSocket client test
const WebSocket = require('ws');

const wsUrl = 'ws://localhost:8000/ws';
console.log(`Connecting to ${wsUrl}...`);

const ws = new WebSocket(wsUrl);

ws.on('open', () => {
    console.log('✓ WebSocket connected successfully!');
    console.log('Sending test message...');

    const testMessage = JSON.stringify({
        type: 'test',
        data: 'Hello from Node.js test client'
    });

    ws.send(testMessage);
    console.log(`Sent: ${testMessage}`);
});

ws.on('message', (data) => {
    console.log(`Received: ${data}`);
});

ws.on('close', (code, reason) => {
    console.log(`Connection closed. Code: ${code}, Reason: ${reason}`);
    process.exit(0);
});

ws.on('error', (error) => {
    console.error(`✗ WebSocket error: ${error.message}`);
    process.exit(1);
});

// Close after 5 seconds
setTimeout(() => {
    console.log('Test complete, closing connection...');
    ws.close();
}, 5000);
