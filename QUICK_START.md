# ⚡ Quick Start Guide

## 🚀 One-Command Build & Run

```bash
# Build everything
./build.sh

# Start backend
docker-compose up -d

# Start frontend
cd "Novitai MCP" && node https_server.js
```

## 🔧 Essential Commands

### Build
```bash
./build.sh                    # Full build with file copying
cd "Novitai MCP" && npm run build  # Frontend only
```

### Run
```bash
# Backend
docker-compose up -d

# Frontend (HTTPS)
cd "Novitai MCP" && node https_server.js

# Frontend (Dev)
cd "Novitai MCP" && npm run start:dev
```

### Test
```bash
# Frontend
curl -I https://localhost:3000/taskpane.html

# Backend
curl -s http://localhost:9000/health

# Auth files
curl -I https://localhost:3000/login-dialog.html
```

## 🚨 Critical Files (Must Copy After Build)

```bash
cp public/login-dialog.html dist/
cp public/auth-callback.html dist/
cp dist/assets/logo-filled.png dist/assets/novitai-logo.png
```

## 📱 Load in Word

1. Open Microsoft Word
2. Insert → Add-ins → My Add-ins
3. Upload My Add-in
4. Select `Novitai MCP/manifest.xml`

## 🔍 Troubleshooting

| Issue | Solution |
|-------|----------|
| `File not found: /login-dialog.html` | `cp public/login-dialog.html dist/` |
| `File not found: /novitai-logo.png` | `cp dist/assets/logo-filled.png dist/assets/novitai-logo.png` |
| CORS errors | Check backend CORS config |
| Port conflicts | `lsof -ti:3000 \| xargs kill -9` |

## 📊 Status Check

```bash
# All services
docker-compose ps

# Frontend
curl -I https://localhost:3000/taskpane.html

# Backend
curl -s http://localhost:9000/health | jq .status
```

---
**Need help?** See `BUILD_GUIDELINES.md` for detailed instructions.
