#!/bin/bash
set -e

echo "🏗️ Building Word Add-in MCP..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Build frontend
print_status "Building frontend..."
cd "Novitai MCP"

if [ ! -f "package.json" ]; then
    print_error "package.json not found. Are you in the right directory?"
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    print_status "Installing dependencies..."
    npm install
fi

# Build the project
print_status "Running webpack build..."
npm run build

# Copy required files
print_status "Copying authentication files..."
cp public/login-dialog.html dist/ 2>/dev/null || print_warning "login-dialog.html not found in public/"
cp public/auth-callback.html dist/ 2>/dev/null || print_warning "auth-callback.html not found in public/"

# Copy logo with correct name
print_status "Setting up logo..."
if [ -f "dist/assets/logo-filled.png" ]; then
    cp dist/assets/logo-filled.png dist/assets/novitai-logo.png
    print_success "Logo copied as novitai-logo.png"
else
    print_warning "logo-filled.png not found in dist/assets/"
fi

# Verify build
print_status "Verifying build..."
echo "Files in dist/:"
ls -la dist/ | grep -E "(login-dialog|auth-callback|novitai-logo)" || print_warning "Some required files may be missing"

# Check if backend is running
print_status "Checking backend status..."
if curl -s http://localhost:9000/health > /dev/null 2>&1; then
    print_success "Backend is running"
else
    print_warning "Backend is not running. Start it with: docker-compose up -d"
fi

# Check if frontend files are accessible
print_status "Testing frontend files..."
if curl -s -I https://localhost:3000/taskpane.html | grep -q "200 OK"; then
    print_success "Frontend is accessible"
else
    print_warning "Frontend may not be running. Start it with: node https_server.js"
fi

print_success "Build complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Start backend: docker-compose up -d"
echo "2. Start frontend: cd 'Novitai MCP' && node https_server.js"
echo "3. Load add-in in Word: Insert → Add-ins → Upload My Add-in → select manifest.xml"
echo ""
echo "🌐 URLs:"
echo "   Frontend: https://localhost:3000"
echo "   Backend:  http://localhost:9000"
echo "   API Docs: http://localhost:9000/docs"
