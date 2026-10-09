/**
 * Health-checked DNS lookup untuk kisskh.do
 *
 * Latar belakang:
 * - kisskh.do diblokir pemerintah/ISP (Biznet) via DNS poisoning:
 *   resolver sistem (8.8.8.8 via /etc/resolv.conf) sering mengembalikan
 *   IP mati (mis. 202.169.44.80) yang menghasilkan EHOSTUNREACH.
 * - dnscrypt-proxy (DOH/Cloudflare) sudah berjalan lokal di 127.0.0.1:5053
 *   dan mengembalikan IP Cloudflare yang sehat (104.21.x / 172.67.x).
 * - Catatan: fetch() undici TIDAK menghormati dns.setServers() — ia memakai
 *   dns.lookup (getaddrinfo). Karena itu lookup kustom ini dipasang sebagai
 *   opsi `lookup` pada https.Agent, bukan via setServers.
 *
 * Perilaku:
 * - Host selain kisskh.do -> dns.lookup standar (tidak terpengaruh).
 * - kisskh.do -> resolve via dnscrypt, probe TCP 443 tiap kandidat,
 *   pilih yang pertama bisa dihubungi, cache 5 menit.
 * - Fallback: jika semua kandidat gagal probe, pakai dns.lookup IPv4 standar.
 */
const dns = require('dns');
const net = require('net');

const TARGET_HOSTS = new Set(['kisskh.do', 'www.kisskh.do']);
const DNSCRYPT_SERVER = '127.0.0.1:5053'; // dnscrypt-proxy (upstream Cloudflare DOH)
const PROBE_PORT = 443;
const PROBE_TIMEOUT_MS = 1500;
const CACHE_TTL_MS = 5 * 60 * 1000;

const resolver = new dns.Resolver();
resolver.setServers([DNSCRYPT_SERVER]);

let cached = null; // { ip, ts }

function probeTcp(ip, cb) {
  const sock = net.connect({ host: ip, port: PROBE_PORT });
  let settled = false;
  const done = (ok) => {
    if (settled) return;
    settled = true;
    sock.destroy();
    cb(ok);
  };
  sock.setTimeout(PROBE_TIMEOUT_MS, () => done(false));
  sock.once('connect', () => done(true));
  sock.once('error', () => done(false));
}

/**
 * Signature kompatibel dns.lookup(hostname[, options], callback)
 * Dipasang sebagai opsi `lookup` pada https.Agent.
 */
function kisskhLookup(hostname, options, callback) {
  if (typeof options === 'function') {
    callback = options;
    options = {};
  }
  const all = !!(options && options.all);

  // Siapkan callback hasil sesuai mode `all` yang diminta Node's net/tls.
  const done = (err, ip) => {
    if (err) return callback(err);
    if (all) {
      return callback(null, [{ address: ip, family: 4 }]);
    }
    return callback(null, ip, 4);
  };

  if (!TARGET_HOSTS.has(hostname)) {
    return dns.lookup(hostname, options || {}, callback);
  }

  const now = Date.now();
  if (cached && now - cached.ts < CACHE_TTL_MS) {
    return process.nextTick(() => done(null, cached.ip));
  }

  resolver.resolve4(hostname, (err, addresses) => {
    const list = (addresses || []).slice().sort();
    if (!list.length) {
      // dnscrypt gagal/tidak menjawab -> fallback lookup sistem (IPv4)
      return dns.lookup(hostname, options || {}, (e, a, f) => callback(e, a, f));
    }
    let i = 0;
    const tryNext = () => {
      if (i >= list.length) {
        // Semua kandidat gagal probe -> fallback lookup sistem (IPv4)
        return dns.lookup(hostname, options || {}, (e, a, f) => callback(e, a, f));
      }
      const ip = list[i++];
      probeTcp(ip, (ok) => {
        if (ok) {
          cached = { ip, ts: Date.now() };
          return done(null, ip);
        }
        tryNext();
      });
    };
    tryNext();
  });
}

module.exports = { kisskhLookup };
