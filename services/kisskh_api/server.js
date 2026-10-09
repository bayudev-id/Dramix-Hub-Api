const express = require('express');
const cors = require('cors');
const https = require('https');
const http = require('http');
const { PORT } = require('./config');
const path = require('path');
const dramaListRouter = require('./routes/dramaListRoutes');
const { getDramaDetail, getSearch, getList, getListFilters } = require('./controllers/dramaListController');
const subRouter = require('./routes/subRoutes');
const streamRouter = require('./routes/streamRoutes');
const homeRouter = require('./routes/homeRoutes');
const { kisskhLookup } = require('./helpers/kisskhDns');

// Connection pooling dengan custom lookup untuk bypass ISP DNS blocking
const httpsAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 64,
  keepAliveMsecs: 15000,
  lookup: kisskhLookup
});

const httpAgent = new http.Agent({
  keepAlive: true,
  maxSockets: 64,
  keepAliveMsecs: 15000,
  lookup: kisskhLookup
});

const app = express();

// Middleware
app.use(cors());
app.use(express.json({ limit: '1mb' }));

// Documentation Route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// Routes
app.use('/api/DramaList', dramaListRouter);
app.get('/api/Drama/:id', getDramaDetail);
app.get('/api/Search', getSearch);
app.get('/api/Explore', getList);
app.get('/api/listFilters', getListFilters);
app.use('/api/Sub', subRouter);

app.use('/api/Stream', streamRouter);
app.use('/api/Home', homeRouter);

// Dedicated Streaming Proxy for KissKH (Bypass CF Worker IP Block)
app.get('/api/proxy', (req, res) => {
  let { url, referer } = req.query;
  if (!url) return res.status(400).send('Missing URL');

  // Normalisasi protocol-relative URL (dimulai dengan //)
  if (url.startsWith('//')) {
    url = 'https:' + url;
  }

  const targetUrl = new URL(url);
  const agent = url.startsWith('https') ? httpsAgent : httpAgent;
  const options = {
    method: 'GET',
    headers: {
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
      'Referer': referer || 'https://kisskh.do/',
      'Accept': '*/*'
    },
    agent: agent
  };

  if (req.headers.range) options.headers['Range'] = req.headers.range;

  const protocol = url.startsWith('https') ? https : http;
  const proxyReq = protocol.request(url, options, (proxyRes) => {
    // Set base CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, HEAD, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', '*');

    if (url.includes('.m3u8')) {
      let body = '';
      proxyRes.on('data', (chunk) => body += chunk);
      proxyRes.on('end', () => {
        const proxyPrefix = `${req.protocol}://${req.get('host')}/api/proxy?referer=${encodeURIComponent(referer || 'https://kisskh.do/')}&url=`;
        const targetUrlObj = new URL(url);
        
        const rewrittenBody = body.split('\n').map(line => {
          if (line.startsWith('#') || line.trim() === '') return line;
          const absoluteUrl = line.startsWith('http') ? line : new URL(line, targetUrlObj.href).href;
          return `${proxyPrefix}${encodeURIComponent(absoluteUrl)}`;
        }).join('\n');
        
        res.setHeader('Content-Type', 'application/vnd.apple.mpegurl');
        res.send(rewrittenBody);
      });
    } else {
      // Clean headers from upstream
      const responseHeaders = { ...proxyRes.headers };
      delete responseHeaders['content-security-policy'];
      delete responseHeaders['x-frame-options'];
      delete responseHeaders['access-control-allow-origin'];

      res.writeHead(proxyRes.statusCode, responseHeaders);
      proxyRes.pipe(res, { end: true });
    }
  });

  // Hentikan request upstream ke CDN ketika klien membatalkan/seek video
  req.on('close', () => {
    if (!proxyReq.destroyed) {
      proxyReq.destroy();
    }
  });

  proxyReq.on('error', (e) => {
    if (!res.headersSent) {
      res.status(500).send(e.message);
    }
  });

  proxyReq.end();
});

// 404 handler - endpoint tidak ditemukan
app.use((req, res) => {
  res.status(404).json({ message: 'Resource tidak ditemukan' });
});

// Global error handler - 500 internal server error
app.use((err, req, res, next) => {
  res.status(500).json({ message: 'Terjadi kesalahan pada server' });
});

// Export app for testing
module.exports = app;

// Start server only when run directly (not imported by tests)
if (require.main === module) {
  const HOST = process.env.HOST || '127.0.0.1';
  app.listen(PORT, HOST, () => {
    console.log(`Server running on port ${PORT}`);
  });
}
