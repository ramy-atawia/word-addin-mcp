const fs = require('fs');
const path = require('path');

class EnvInjectionPlugin {
  constructor(options = {}) {
    this.options = options;
  }

  apply(compiler) {
    compiler.hooks.emit.tapAsync('EnvInjectionPlugin', (compilation, callback) => {
      // Get environment variables with dynamic defaults
      // Since we're building for both environments, we'll inject both and let the client-side code decide
      const envVars = {
        AUTH0_DOMAIN: process.env.REACT_APP_AUTH0_DOMAIN || 'dev-bktskx5kbc655wcl.us.auth0.com',
        AUTH0_CLIENT_ID: process.env.REACT_APP_AUTH0_CLIENT_ID || 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U',
        AUTH0_AUDIENCE: process.env.REACT_APP_AUTH0_AUDIENCE || 'INws849yDXaC6MZVXnLhMJi6CZC4nx6U',
        BACKEND_URL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:9000',
        FRONTEND_URL: process.env.REACT_APP_FRONTEND_URL || 'https://localhost:3000'
      };

      // Process HTML files
      Object.keys(compilation.assets).forEach(filename => {
        if (filename.endsWith('.html')) {
          let content = compilation.assets[filename].source();
          
          // Convert to string if it's a Buffer
          if (Buffer.isBuffer(content)) {
            content = content.toString();
          } else if (typeof content !== 'string') {
            content = String(content);
          }
          
          // Inject environment variables as window globals
          const envScript = `
    <script>
      window.AUTH0_DOMAIN = '${envVars.AUTH0_DOMAIN}';
      window.AUTH0_CLIENT_ID = '${envVars.AUTH0_CLIENT_ID}';
      window.AUTH0_AUDIENCE = '${envVars.AUTH0_AUDIENCE}';
      window.BACKEND_URL = '${envVars.BACKEND_URL}';
      window.FRONTEND_URL = '${envVars.FRONTEND_URL}';
    </script>
`;
          
          // Insert before closing head tag
          content = content.replace('</head>', envScript + '</head>');
          
          compilation.assets[filename] = {
            source: () => content,
            size: () => content.length
          };
        }
      });

      callback();
    });
  }
}

module.exports = EnvInjectionPlugin;
