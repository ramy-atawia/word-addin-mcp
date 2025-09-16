const https = require('https');
const fs = require('fs');
const path = require('path');
const os = require('os');

// Use official Office Add-in development certificates
const sslOptions = {
    key: fs.readFileSync(path.join(os.homedir(), '.office-addin-dev-certs/localhost.key')),
    cert: fs.readFileSync(path.join(os.homedir(), '.office-addin-dev-certs/localhost.crt'))
};

// Create HTTPS server
const server = https.createServer(sslOptions, (req, res) => {
    console.log(`Request: ${req.method} ${req.url}`);
    
    // Handle CORS preflight
    if (req.method === 'OPTIONS') {
        res.writeHead(200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization',
            'Access-Control-Max-Age': '86400'
        });
        res.end();
        return;
    }

    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

    let filePath = req.url;
    
    // Handle root path
    if (filePath === '/' || filePath === '/index.html') {
        filePath = '/taskpane.html';
    }
    
    // Remove query parameters
    filePath = filePath.split('?')[0];
    
    // Map to dist directory
    const fullPath = path.join(__dirname, 'dist', filePath);
    
    // Check if file exists
    if (!fs.existsSync(fullPath)) {
        console.log(`File not found: ${fullPath}`);
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('File not found');
        return;
    }
    
    // Get file extension for content type
    const ext = path.extname(fullPath);
    let contentType = 'text/plain';
    
    switch (ext) {
        case '.html':
            contentType = 'text/html';
            break;
        case '.js':
            contentType = 'application/javascript';
            break;
        case '.css':
            contentType = 'text/css';
            break;
        case '.png':
            contentType = 'image/png';
            break;
        case '.jpg':
        case '.jpeg':
            contentType = 'image/jpeg';
            break;
        case '.ico':
            contentType = 'image/x-icon';
            break;
        case '.json':
            contentType = 'application/json';
            break;
    }
    
    // Read and serve file
    fs.readFile(fullPath, (err, data) => {
        if (err) {
            console.error(`Error reading file: ${err}`);
            res.writeHead(500, { 'Content-Type': 'text/plain' });
            res.end('Internal server error');
            return;
        }
        
        res.writeHead(200, { 'Content-Type': contentType });
        res.end(data);
        console.log(`Served: ${filePath} (${contentType})`);
    });
});

// Error handling
server.on('error', (err) => {
    console.error('Server error:', err);
});

// Start server
const PORT = 3000;
server.listen(PORT, () => {
    console.log(`🚀 HTTPS server running on https://localhost:${PORT}`);
    console.log(`📁 Serving files from: ${path.join(__dirname, 'dist')}`);
    console.log(`🌐 Main UI: https://localhost:${PORT}/taskpane.html`);
    console.log(`🏠 Root path: https://localhost:${PORT}/`);
    console.log(`🔒 Using official Office Add-in SSL certificates`);
    console.log(`✅ No more security warnings - certificates are trusted!`);
});
