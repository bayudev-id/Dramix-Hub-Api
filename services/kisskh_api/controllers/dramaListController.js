const fetchFromKissKH = require('../helpers/fetchFromKissKH');
const { generateEpisodeKkey } = require('../helpers/kkeyGenerator');

/**
 * GET /api/DramaList/Show
 * Mengembalikan array of Show_Item (featured/carousel)
 */
async function getShow(req, res) {
  try {
    const data = await fetchFromKissKH('/api/DramaList/Show');
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * Fetch section content via Explore/List endpoint — mendukung infinite scroll.
 * defaults = filter tetap per section (order/type/sub/country/status).
 * page/pageSize diteruskan dari request.
 */
async function fetchSection(req, defaults) {
  const query = {
    type: req.query.type || defaults.type,
    sub: req.query.sub || defaults.sub,
    country: req.query.country || defaults.country,
    status: req.query.status || defaults.status,
    order: req.query.order || defaults.order,
    page: req.query.page || '1',
    pageSize: req.query.pageSize || '18',
  };
  return fetchFromKissKH('/api/DramaList/List', query);
}

/**
 * GET /api/DramaList/LastUpdate
 * Explore: order=2 (Last Update), semua filter All.
 */
async function getLastUpdate(req, res) {
  try {
    const data = await fetchSection(req, { type: '0', sub: '0', country: '0', status: '0', order: '2' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/MostView (dengan ?c=1 atau ?c=2)
 * Explore: order=1 (Popular), country = c (1=Chinese, 2=South Korea).
 */
async function getMostView(req, res) {
  try {
    const data = await fetchSection(req, { type: '0', sub: '0', country: req.query.c || '1', status: '0', order: '1' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/** GET /api/DramaList/MostView1 — Explore order=1, country=1 (Chinese). */
async function getMostView1(req, res) {
  try {
    const data = await fetchSection(req, { type: '0', sub: '0', country: '1', status: '0', order: '1' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/** GET /api/DramaList/MostView2 — Explore order=1, country=2 (South Korea). */
async function getMostView2(req, res) {
  try {
    const data = await fetchSection(req, { type: '0', sub: '0', country: '2', status: '0', order: '1' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/TopRating
 * Explore: order=1 (Popular), type=4 (Hollywood).
 */
async function getTopRating(req, res) {
  try {
    const data = await fetchSection(req, { type: '4', sub: '0', country: '0', status: '0', order: '1' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/Animate
 * Explore: order=1 (Popular), type=3 (Anime).
 */
async function getAnimate(req, res) {
  try {
    const data = await fetchSection(req, { type: '3', sub: '0', country: '0', status: '0', order: '1' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/Upcoming
 * Explore: order=3 (Release Date), status=3 (Upcoming).
 */
async function getUpcoming(req, res) {
  try {
    const data = await fetchSection(req, { type: '0', sub: '0', country: '0', status: '3', order: '3' });
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/List
 * Mengembalikan daftar drama dengan filter
 * Query params: page, type, sub, country, status, order — forwarded to upstream
 */
async function getList(req, res) {
  try {
    // Default filter: All (type=0, sub=0, country=0, status=0) + Last Update (order=2)
    const query = {
      type: req.query.type || '0',
      sub: req.query.sub || '0',
      country: req.query.country || '0',
      status: req.query.status || '0',
      order: req.query.order || '2',
      page: req.query.page || '1',
      pageSize: req.query.pageSize || '10',
    };
    const data = await fetchFromKissKH('/api/DramaList/List', query);
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/List/filters
 * Mengembalikan metadata filter statis untuk UI Explore
 */
function getListFilters(req, res) {
  return res.status(200).json({
    type: { "0": "All", "1": "TV Series", "2": "Movie", "3": "Anime", "4": "Hollywood" },
    sub: { "0": "All Subtitles", "1": "English", "2": "Khmer", "3": "Indonesian", "4": "Malay", "5": "Thai", "10": "Arabic" },
    country: { "0": "All Regions", "1": "Chinese", "2": "South Korea", "3": "Japanese", "4": "Hong Kong", "5": "Thailand", "6": "United States", "7": "Taiwan", "8": "Philippines" },
    status: { "0": "All", "1": "Ongoing", "2": "Completed", "3": "Upcoming" },
    order: { "1": "Popular", "2": "Last Update", "3": "Release Date" }
  });
}

/**
 * GET /api/DramaList/Drama/:id
 * Mengembalikan detail drama termasuk daftar episode
 * Query params: forwarded to upstream
 */
async function getDramaDetail(req, res) {
  try {
    const data = await fetchFromKissKH(`/api/DramaList/Drama/${req.params.id}`, req.query);
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/Episode/:id.png
 * Mengembalikan URL streaming episode
 * Query params: err, ts, time, kkey — forwarded to upstream
 */
async function getEpisode(req, res) {
  try {
    const query = { ...req.query };
    
    // Auto-generate kkey if not provided
    if (!query.kkey) {
      query.kkey = generateEpisodeKkey(req.params.id);
    }

    const data = await fetchFromKissKH(`/api/DramaList/Episode/${req.params.id}.png`, query);
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

/**
 * GET /api/DramaList/Search
 * Mencari drama berdasarkan keyword
 * Query params: q (keyword), type — forwarded to upstream
 */
async function getSearch(req, res) {
  try {
    const data = await fetchFromKissKH('/api/DramaList/Search', req.query);
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

module.exports = {
  getShow,
  getLastUpdate,
  getMostView,
  getMostView1,
  getMostView2,
  getTopRating,
  getAnimate,
  getUpcoming,
  getList,
  getListFilters,
  getDramaDetail,
  getEpisode,
  getSearch
};
