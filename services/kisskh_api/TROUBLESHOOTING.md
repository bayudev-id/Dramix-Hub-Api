# Troubleshooting Guide

## ISP/Biznet IP Block Issue

### Problem

Service gagal terhubung ke KissKH upstream dengan error:
```
ERROR: [TypeError: fetch failed] {
  [cause]: AggregateError [EHOSTUNREACH]:
    Error: connect EHOSTUNREACH 202.169.44.80:443
}
```

Atau saat test curl:
```
curl: (7) Failed to connect to kisskh.do port 443 after 33 ms: Couldn't connect to server
```

### Root Cause

IP asli KissKH (`202.169.44.80` - Biznet Networks) diblokir oleh ISP. Beberapa ISP Indonesia (terutama Biznet, Indosat, Telkom) melakukan blocking pada IP tertentu untuk keperluan QoS atau policy.

### Solution

KissKH sudah di-proxy oleh **Cloudflare** dan tersedia melalui IP Cloudflare:
- `172.67.170.119`
- `104.21.95.144`

Tambahkan entry `/etc/hosts` pada server Linux untuk redirect `kisskh.do` ke Cloudflare IP:

```bash
sudo bash -c 'cat >> /etc/hosts << EOF
172.67.170.119 kisskh.do
104.21.95.144 kisskh.do
EOF
'
```

Verifikasi:
```bash
ping kisskh.do
# Output: PING kisskh.do (172.67.170.119) ...

nc -v kisskh.do 443
# Output: Connection to kisskh.do (172.67.170.119) 443 port [tcp/https] succeeded!
```

### Why This Works

1. **Ping & DNS Query** bypass `/etc/hosts` — mereka tanya DNS server langsung
2. **Applications** (curl, Node.js fetch, nc) membaca `/etc/hosts` lebih dulu sebelum DNS lookup
3. Dengan IP Cloudflare, koneksi bypass Biznet gateway yang memblokir IP asli `202.169.44.80`
4. Cloudflare sebagai CDN/proxy meforward request ke origin server KissKH

### Verification

Setelah edit `/etc/hosts`, test semua endpoints:

```bash
# Test local service
curl http://127.0.0.1:6103/api/Home
curl http://127.0.0.1:6103/api/DramaList/MostView

# Test via Cloudflare Tunnel (jika ada)
curl https://kisskh.dramix.biz.id/api/Home
curl https://kisskh.dramix.biz.id/api/DramaList/MostView

# Test via main Dramix gateway
curl http://127.0.0.1:7400/api/kisskh/Home
curl http://127.0.0.1:7400/api/kisskh/DramaList/MostView
```

### Alternative Solutions (If Above Doesn't Work)

#### Option 1: VPN/Proxy
Setup VPN atau HTTP proxy yang bisa bypass ISP blocking.

#### Option 2: Cloudflare WARP
Install Cloudflare WARP untuk bypass ISP restriction:
```bash
curl https://pkg.cloudflareclient.com/install.sh | sudo bash
sudo systemctl start warp-svc
```

#### Option 3: DNS-over-HTTPS (DoH)
Setup `dnsproxy` atau `dnscrypt-proxy` untuk DoH agar DNS query tidak di-intercept ISP:
```bash
# Install dnsproxy
wget https://github.com/AdguardTeam/dnsproxy/releases/latest/download/dnsproxy-linux-amd64
sudo mv dnsproxy-linux-amd64 /usr/local/bin/dnsproxy
sudo chmod +x /usr/local/bin/dnsproxy

# Setup systemd service (future enhancement)
```

---

## Other Known Issues

### Issue: Service binds to `0.0.0.0` instead of specific IP

**Solution**: Edit `.env` to specify HOST:
```env
PORT=6103
HOST=192.168.18.104
```

### Issue: .env not loaded by server.js

**Solution**: Ensure `config/index.js` calls `require('dotenv').config()`:
```javascript
require('dotenv').config();

module.exports = {
  PORT: process.env.PORT || 3000,
  UPSTREAM_BASE_URL: process.env.UPSTREAM_BASE_URL || 'https://kisskh.do',
  UPSTREAM_TIMEOUT: parseInt(process.env.UPSTREAM_TIMEOUT) || 10000
};
```

And install dotenv if missing:
```bash
npm install dotenv
```

---

## Testing Checklist

- [ ] `/etc/hosts` contains Cloudflare IPs for `kisskh.do`
- [ ] `ping kisskh.do` returns Cloudflare IP (172.67.170.119 or 104.21.95.144)
- [ ] `nc -v kisskh.do 443` shows successful connection
- [ ] Service logs show successful `[Upstream Fetch]` requests
- [ ] `/api/Home` returns 200 OK
- [ ] `/api/DramaList/MostView` returns 200 OK with drama data
- [ ] Frontend Dramix loads KissKH provider without errors
