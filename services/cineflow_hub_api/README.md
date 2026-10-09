# 🎬 CineFlow API Proxy & Security Testing Project

**Version:** 0.2.7+  
**Status:** 🟢 Production Ready  
**Last Updated:** August 29, 2026

---

## 📋 Project Overview

**CineFlow API Proxy** adalah project untuk reverse engineering dan security testing aplikasi CineFlow. Project ini menyediakan:
- ✅ FastAPI proxy server untuk API backend
- ✅ Frida scripts untuk bypass security checks
- ✅ Burp Suite integration via MCP
- ✅ Comprehensive documentation dan tools

---

## 🚀 Quick Start

### Path 1: API Data Collection (1 minute)
```bash
python main.py
# Open: http://127.0.0.1:8000
```

### Path 2: Full Security Testing (15 minutes)
```bash
# 1. Start Burp Suite (port 9876)
# 2. Start Frida: adb shell /data/local/tmp/frida-server
# 3. Load script: frida -U com.cineflow.app -l frida/frida_bypass_proxy.js
```

**👉 See:** `docs/setup/START_HERE.md` for detailed instructions

---

## 📁 Project Structure

```
d:\10. BackEnd\Drama\Cine Ori\
│
├── 📄 main.py                          # FastAPI proxy server
├── 📄 session_data.json                # Token cache
├── 📄 README.md                        # This file
│
├── 📂 docs/                            # All documentation
│   ├── 📂 setup/                       # Setup guides
│   │   ├── START_HERE.md              # ⭐ Start here
│   │   ├── SETUP_PROXY_192.168.18.200.md
│   │   ├── MCP_BURP_SETUP.md
│   │   └── ...
│   │
│   ├── 📂 api/                         # API documentation
│   │   └── API_DOCUMENTATION.md       # All endpoints
│   │
│   ├── 📂 troubleshooting/             # Troubleshooting guides
│   │   ├── PROXY_BYPASS_GUIDE.md
│   │   ├── PROJECT_VERIFICATION.md
│   │   └── ...
│   │
│   └── 📂 analysis/                    # Reports & analysis
│       ├── BURP_HTTP_HISTORY.md
│       ├── NETWORK_DIAGRAM.txt
│       └── ...
│
├── 📂 frida/                           # Frida scripts
│   ├── frida_bypass_proxy.js          # Proxy bypass
│   └── bypass-ssl-pinning.js          # SSL pinning bypass
│
├── 📂 scripts/                         # Helper scripts
│   ├── QUICK_COMMANDS.bat             # Interactive menu
│   ├── QUICK_SETUP.bat                # Auto setup
│   └── SETUP_PORTFORWARD_ADMIN.bat    # Port forwarding
│
├── 📂 tools/                           # Testing tools
│   ├── test_api.py                    # Quick API tests
│   └── test_all_endpoints.py          # Comprehensive tests
│
├── 📂 apk/                             # APK files
│   └── [24 APK versions]
│
├── 📂 apk_extracted/                   # Extracted APK resources
├── 📂 decompile/                       # Decompiled source
├── 📂 Modifikasi File/                 # Modified APK files
└── 📂 referensi/                       # Reference data

```

---

## 📚 Documentation Index

### 🎯 Getting Started
- **[START_HERE.md](docs/setup/START_HERE.md)** - Quick start guide (read this first!)
- **[DECISION_TREE.md](docs/setup/DECISION_TREE.md)** - Choose your path
- **[QUICKSTART.md](docs/setup/QUICKSTART.md)** - Fast setup

### 🔧 Setup Guides
- **[SETUP_PROXY_192.168.18.200.md](docs/setup/SETUP_PROXY_192.168.18.200.md)** - Proxy setup (8 steps)
- **[MCP_BURP_SETUP.md](docs/setup/MCP_BURP_SETUP.md)** - MCP Burp configuration
- **[MCP_FIX_LOCALHOST.md](docs/setup/MCP_FIX_LOCALHOST.md)** - Fix MCP localhost issue
- **[SETUP_SUMMARY.md](docs/setup/SETUP_SUMMARY.md)** - Complete summary

### 📖 API Reference
- **[API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md)** - All endpoints documentation

### 🐛 Troubleshooting
- **[PROXY_BYPASS_GUIDE.md](docs/troubleshooting/PROXY_BYPASS_GUIDE.md)** - Proxy bypass issues
- **[PROJECT_VERIFICATION.md](docs/troubleshooting/PROJECT_VERIFICATION.md)** - Verification checklist
- **[PERBAIKAN_ERROR.md](docs/troubleshooting/PERBAIKAN_ERROR.md)** - Error fixes
- **[README_PROXY_FIX.md](docs/troubleshooting/README_PROXY_FIX.md)** - Proxy fix details

### 📊 Analysis & Reports
- **[BURP_HTTP_HISTORY.md](docs/analysis/BURP_HTTP_HISTORY.md)** - HTTP history report
- **[NETWORK_DIAGRAM.txt](docs/analysis/NETWORK_DIAGRAM.txt)** - Network flow diagram
- **[SUMMARY.md](docs/analysis/SUMMARY.md)** - Project summary

---

## 🛠️ Tools & Scripts

### Helper Scripts (in `scripts/`)
```bash
# Interactive menu with 14 options
scripts\QUICK_COMMANDS.bat

# Auto setup helper
scripts\QUICK_SETUP.bat

# Port forwarding setup (run as admin)
scripts\SETUP_PORTFORWARD_ADMIN.bat
```

### Testing Tools (in `tools/`)
```bash
# Quick API test
python tools\test_api.py

# Comprehensive endpoint test
python tools\test_all_endpoints.py
```

---

## 🔐 Security Testing Setup

### Your Configuration
```
Device IP:       192.168.18.200
Burp Proxy:      localhost:9876 (forwarded to device)
Network:         192.168.18.0/24
Backend API:     ngintipya2.cineflow.my.id
App Package:     com.cineflow.app
```

### MCP Burp Suite
```json
{
  "mcpServers": {
    "burp-suite": {
      "type": "remote",
      "url": "http://localhost:9876",
      "enabled": true
    }
  }
}
```
Location: `C:\Users\DIMOMEN.ID\.kiro\settings\mcp.json`

---

## 🎯 Common Tasks

### Start API Server
```bash
python main.py
# Open: http://127.0.0.1:8000
```

### Check Burp HTTP History
```bash
# Via MCP in Kiro IDE (already setup)
# Or manually in Burp: Proxy → HTTP history
```

### Load Frida Bypass
```bash
# Terminal 1: Start Frida server
adb shell /data/local/tmp/frida-server

# Terminal 2: Load script
frida -U com.cineflow.app -l frida/frida_bypass_proxy.js
```

### Monitor Device Logs
```bash
adb logcat | findstr "cineflow"
```

---

## 📊 Project Stats

```
Documentation:     15+ comprehensive guides
API Endpoints:     50+ documented endpoints
APK Versions:      24 test/patched versions
Frida Scripts:     2 bypass scripts
Helper Tools:      8+ automation tools
Test Scripts:      2 comprehensive test suites
```

---

## ✅ Features

### API Proxy Server
- ✅ Automatic token refresh
- ✅ Token caching (persistent)
- ✅ Dual proxy endpoints support
- ✅ Web dashboard with token management
- ✅ Error handling with retry logic

### Security Testing
- ✅ Frida proxy bypass
- ✅ SSL pinning bypass
- ✅ Burp Suite integration via MCP
- ✅ Request interception & modification
- ✅ Traffic analysis tools

### Documentation
- ✅ Step-by-step setup guides
- ✅ Complete API reference
- ✅ Troubleshooting guides
- ✅ Network diagrams
- ✅ Analysis reports

---

## 🔄 Workflow

### Development Workflow
```
1. Start API Server (main.py)
   ↓
2. Test endpoints (test_api.py)
   ↓
3. Analyze results
   ↓
4. Document findings
```

### Security Testing Workflow
```
1. Start Burp Suite
   ↓
2. Configure device proxy
   ↓
3. Start Frida server
   ↓
4. Load bypass script
   ↓
5. Open CineFlow app
   ↓
6. Monitor & analyze in Burp
```

---

## 🎓 Learning Resources

### For Beginners
1. Read `docs/setup/START_HERE.md`
2. Choose your path in `docs/setup/DECISION_TREE.md`
3. Follow setup guide step-by-step

### For Advanced Users
1. API reference: `docs/api/API_DOCUMENTATION.md`
2. Network analysis: `docs/analysis/NETWORK_DIAGRAM.txt`
3. Custom scripting with MCP tools

---

## 🚨 Important Notes

⚠️ **Security Warning:**
- This project is for educational and security research purposes only
- Only test on apps/systems you have permission to test
- Do not use for malicious purposes

⚠️ **Network Warning:**
- Keep proxy on local network only (192.168.18.0/24)
- Do not expose ports to internet
- Use responsibly

---

## 💡 Tips & Tricks

### Tip 1: Use Helper Menu
```bash
scripts\QUICK_COMMANDS.bat
# Interactive menu with common tasks
```

### Tip 2: Monitor Multiple Terminals
```
Terminal 1: Frida server
Terminal 2: Frida script
Terminal 3: ADB logcat
Terminal 4: API server (optional)
```

### Tip 3: Quick Connection Test
```bash
ping 192.168.18.200
adb devices
python tools\test_api.py
```

---

## 📞 Support & Contact

For issues or questions:
1. Check `docs/troubleshooting/` first
2. Review `docs/setup/PROJECT_VERIFICATION.md`
3. See specific error guides in troubleshooting folder

---

## 🏆 Credits

- **FastAPI** - API server framework
- **Frida** - Dynamic instrumentation toolkit
- **Burp Suite** - Web security testing
- **MCP** - Model Context Protocol for tool integration

---

## 📝 Version History

- **v0.2.7+** - Current version
  - MCP Burp Suite integration
  - Organized documentation structure
  - Complete setup automation
  - Comprehensive testing tools

---

## 🔮 Future Enhancements

- [ ] Automated testing pipeline
- [ ] Enhanced logging system
- [ ] GUI dashboard for monitoring
- [ ] Advanced traffic analysis tools
- [ ] CI/CD integration

---

**Status:** 🟢 Production Ready  
**Maintained:** Active  
**License:** Educational/Research Use Only

---

**Happy Testing!** 🎬🔐

