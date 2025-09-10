# Multi-stage build for React Word Add-in frontend with HTTPS
FROM node:18-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Development stage with HTTPS support
FROM node:18-alpine as development

# Install curl for health checks
RUN apk add --no-cache curl

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev)
RUN npm ci

# Copy application source
COPY . .

# Create SSL certificate directory and set permissions
RUN mkdir -p /app/certs && chmod 755 /app/certs

# Create non-root user (but Office Add-in dev certs need root access initially)
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Expose port
EXPOSE 3002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -k -f https://localhost:3002 || exit 1

# Default command - run webpack dev server with HTTPS
# Set environment variable to skip certificate installation
ENV OFFICE_ADDIN_DEV_CERTS_PATH=/app/certs

# Default command for development (use simple config without certs)
CMD ["npm", "run", "dev-simple"]

# Production build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /app/node_modules ./node_modules
COPY . .

# Build the application
RUN npm run build

# Production stage with nginx
FROM nginx:alpine as production

# Install curl for health checks
RUN apk add --no-cache curl openssl

# Copy built application
COPY --from=build /app/dist /usr/share/nginx/html

# Copy SSL certificate generation script
COPY <<EOF /usr/local/bin/generate-ssl.sh
#!/bin/sh
# Generate self-signed SSL certificates for production if they don't exist
if [ ! -f /etc/nginx/ssl/localhost.crt ]; then
    mkdir -p /etc/nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/nginx/ssl/localhost.key \
        -out /etc/nginx/ssl/localhost.crt \
        -subj "/C=US/ST=CA/L=San Francisco/O=WordAddin/CN=localhost"
fi
EOF

# Make script executable
RUN chmod +x /usr/local/bin/generate-ssl.sh

# Copy nginx configuration
COPY <<EOF /etc/nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    sendfile        on;
    keepalive_timeout  65;
    
    # Gzip configuration
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    server {
        listen 80;
        server_name localhost;
        return 301 https://\$server_name\$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name localhost;
        
        ssl_certificate /etc/nginx/ssl/localhost.crt;
        ssl_certificate_key /etc/nginx/ssl/localhost.key;
        
        # Modern SSL configuration
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;
        
        # Security headers
        add_header X-Frame-Options SAMEORIGIN;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        root /usr/share/nginx/html;
        index index.html;
        
        # Handle SPA routing
        location / {
            try_files \$uri \$uri/ /index.html;
        }
        
        # Handle Office.js manifest
        location ~ \.(xml|json)$ {
            add_header Content-Type application/xml;
            add_header Access-Control-Allow-Origin "*";
        }
        
        # Asset optimization
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
EOF

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -k -f https://localhost || exit 1

# Expose ports
EXPOSE 80 443

# Start script
CMD ["/bin/sh", "-c", "/usr/local/bin/generate-ssl.sh && nginx -g 'daemon off;'"]
