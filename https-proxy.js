const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// HTTPS options with self-signed certificate
const httpsOptions = {
  key: fs.readFileSync(path.join(__dirname, 'ssl', 'localhost-key.pem')),
  cert: fs.readFileSync(path.join(__dirname, 'ssl', 'localhost.pem'))
};

// Create HTTPS server that proxies to HTTP backend
const server = https.createServer(httpsOptions, (req, res) => {
  // Set CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // Proxy to local HTTP server
  const options = {
    hostname: 'localhost',
    port: 3001,
    path: req.url,
    method: req.method,
    headers: req.headers
  };
  
  const proxyReq = http.request(options, (proxyRes) => {
    res.writeHead(proxyRes.statusCode, proxyRes.headers);
    proxyRes.pipe(res);
  });
  
  proxyReq.on('error', (err) => {
    console.error('Proxy error:', err);
    res.writeHead(500);
    res.end('Proxy error');
  });
  
  req.pipe(proxyReq);
});

// Start server
server.listen(3000, () => {
  console.log('🔒 HTTPS proxy server running on https://localhost:3000');
  console.log('📡 Proxying to http://localhost:3001');
  console.log('📱 Word Add-in manifest: ./Novitai MCP/manifest.xml');
});

// Handle errors
server.on('error', (err) => {
  console.error('HTTPS server error:', err);
});
