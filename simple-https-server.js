const https = require('https');
const fs = require('fs');
const path = require('path');
const { createProxyServer } = require('http-proxy');

// Create proxy server
const proxy = createProxyServer();

// HTTPS options with self-signed certificate
const httpsOptions = {
  key: fs.readFileSync(path.join(__dirname, 'ssl', 'localhost-key.pem'), 'utf8'),
  cert: fs.readFileSync(path.join(__dirname, 'ssl', 'localhost.pem'), 'utf8')
};

// Create HTTPS server that proxies to HTTP backend
const server = https.createServer(httpsOptions, (req, res) => {
  // Set CORS headers for cross-origin requests
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // Proxy to HTTP server
  proxy.web(req, res, {
    target: 'http://localhost:3001',
    changeOrigin: true,
    secure: false
  });
});

// Handle proxy errors
proxy.on('error', (err, req, res) => {
  console.error('Proxy error:', err);
  res.writeHead(500, {
    'Content-Type': 'text/plain'
  });
  res.end('Proxy error');
});

// Start server
server.listen(3000, () => {
  console.log('🔒 HTTPS proxy server running on https://localhost:3000');
  console.log('📡 Proxying to http://localhost:3001');
});

// Handle errors
server.on('error', (err) => {
  console.error('HTTPS server error:', err);
});
