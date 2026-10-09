const { UPSTREAM_BASE_URL, UPSTREAM_TIMEOUT } = require('../config');
const { generateEpisodeKkey, generateSubKkey } = require('./kkeyGenerator');
const https = require('https');
const { kisskhLookup } = require('./kisskhDns');

/**
 * https.Agent dengan custom lookup yang bypass ISP DNS blocking kisskh.do
 * via dnscrypt-proxy lokal (Cloudflare DOH).
 */
const upstreamAgent = new https.Agent({
  keepAlive: true,
  maxSockets: 16,
  lookup: kisskhLookup,
});

/**
 * Wrapper https.request yang mengembalikan promise dengan auto-redirect support.
 * Mengembalikan { status, body } untuk JSON, atau throw error dengan .type.
 */
function httpsGetJson(urlStr, timeoutMs, depth = 0) {
  return new Promise((resolve, reject) => {
    let timedOut = false;
    const req = https.request(urlStr, {
      method: 'GET',
      agent: upstreamAgent,
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://kisskh.do/',
        'Origin': 'https://kisskh.do',
      },
    }, (res) => {
      // Handle redirects (manual, max 3 hops)
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location && depth < 3) {
        res.resume(); // drain response
        const nextUrl = new URL(res.headers.location, urlStr).toString();
        return resolve(httpsGetJson(nextUrl, timeoutMs, depth + 1));
      }
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (chunk) => (body += chunk));
      res.on('end', () => resolve({ status: res.statusCode, body }));
    });

    const timer = setTimeout(() => {
      timedOut = true;
      req.destroy(new Error('Upstream timeout'));
    }, timeoutMs);

    req.on('error', (err) => {
      clearTimeout(timer);
      if (timedOut || err.message === 'Upstream timeout') {
        const e = new Error('Upstream timeout');
        e.type = 'timeout';
        reject(e);
      } else {
        reject(err);
      }
    });

    req.on('response', () => clearTimeout(timer)); // response arrived, clear timer
    req.end();
  });
}

async function fetchFromKissKH(path, queryParams = {}) {
  // Automatically inject kkey if it's an episode or subtitle request
  const episodeMatch = path.match(/^\/?api\/DramaList\/Episode\/(\d+)\.png/);
  if (episodeMatch) {
    const episodeId = episodeMatch[1];
    queryParams.kkey = generateEpisodeKkey(episodeId);
    if (queryParams.err === undefined) queryParams.err = 'false';
    if (queryParams.ts === undefined) queryParams.ts = '';
    if (queryParams.time === undefined) queryParams.time = '';
  } else {
    const subMatch = path.match(/^\/?api\/Sub\/(\d+)/);
    if (subMatch) {
      const episodeId = subMatch[1];
      queryParams.kkey = generateSubKkey(episodeId);
    }
  }

  // Build URL with query string
  const url = new URL(path, UPSTREAM_BASE_URL);
  Object.entries(queryParams).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.append(key, value);
    }
  });

  console.log(`[Upstream Fetch] ${url.toString()}`);

  try {
    const { status, body } = await httpsGetJson(url.toString(), UPSTREAM_TIMEOUT);

    // Handle non-2xx
    if (status < 200 || status >= 300) {
      const error = new Error(`Upstream error: ${status}`);
      error.type = 'upstream';
      error.statusCode = status;
      try {
        const data = JSON.parse(body);
        error.message = data.message || `Upstream error: ${status}`;
      } catch {}
      throw error;
    }

    // Parse and return JSON
    return JSON.parse(body);
  } catch (err) {
    // Preserve typed errors
    if (err.type) throw err;

    // Network error
    const error = new Error('Gagal terhubung ke upstream');
    error.type = 'network';
    throw error;
  }
}

module.exports = fetchFromKissKH;
