# KissKH API Node.JS 🎭

A premium, high-performance REST API for KissKH drama metadata. Built with Node.js and Express, featuring automated kkey generation and a unified streaming/subtitle endpoint.

## 🚀 Features

- **Unified Stream API**: Get video links and subtitles in one request.
- **Auto kkey Generation**: No need to worry about KissKH's security keys.
- **Dynamic Home Sections**: Structured metadata for your app's home screen.
- **Premium Documentation**: Built-in dashboard at the root path.
- **Vercel Ready**: Optimized for deployment on Vercel (Singapore region).
- **Self-Host Ready**: Works with Docker, Proxmox, and bare-metal servers.

## 🛠️ Tech Stack

- **Runtime**: Node.js
- **Framework**: Express.js
- **Deployment**: Vercel / Linux Self-Host
- **Styling (Docs)**: Glassmorphism CSS

## 📖 API Documentation

Once deployed, visit the root URL (`/`) to see the interactive documentation dashboard.

### Main Endpoints

- `GET /api/Home`: Homepage sections.
- `GET /api/Explore`: Advanced filtering and search.
- `GET /api/Drama/:id`: Drama details and episode list.
- `GET /api/Stream/:id`: Combined stream and subtitle links.
- `GET /api/Search?q=...`: Search by title.
- `GET /api/DramaList/MostView`: Most viewed dramas.
- `GET /api/DramaList/LastUpdate`: Recently updated dramas.
- `GET /api/listFilters`: Available filters for search and categories.

## 📦 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/bayudev-id/KissKH-API-Node.JS.git
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Setup environment variables (create `.env`):
   ```env
   PORT=7403
   HOST=127.0.0.1
   UPSTREAM_BASE_URL=https://kisskh.do
   UPSTREAM_TIMEOUT=15000
   ```
4. Run the server:
   ```bash
   npm start
   ```

## 🔧 Troubleshooting

If you encounter upstream connection issues or ISP blocking (especially in Indonesia):

👉 **See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** for detailed guide on:
- Fixing ISP/Biznet IP blocks using Cloudflare IPs
- Host configuration in Linux `/etc/hosts`
- Testing connectivity with curl, ping, and nc
- DoH (DNS-over-HTTPS) alternatives

## 🌐 Deployment

### Vercel
Simply connect your GitHub repository to Vercel, and it will automatically deploy to the Singapore (`sin1`) region.

### Linux Self-Host (Systemd)
Create a systemd service at `/etc/systemd/system/kisskh-api.service`:
```ini
[Unit]
Description=KissKH API Node.js Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kisskh-api
ExecStart=/usr/bin/node /opt/kisskh-api/server.js
Restart=always
RestartSec=5
Environment=NODE_ENV=production

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now kisskh-api
```

---
Built with ❤️ for the Drama Community.
