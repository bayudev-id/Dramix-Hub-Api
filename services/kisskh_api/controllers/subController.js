const fetchFromKissKH = require('../helpers/fetchFromKissKH');
const { generateSubKkey } = require('../helpers/kkeyGenerator');

/**
 * GET /api/Sub/:id
 * Meneruskan request subtitle ke upstream dengan query parameter kkey
 */
async function getSubtitle(req, res) {
  try {
    const query = { ...req.query };

    // Auto-generate kkey if not provided
    if (!query.kkey) {
      query.kkey = generateSubKkey(req.params.id);
    }

    const data = await fetchFromKissKH(`/api/Sub/${req.params.id}`, query);
    return res.status(200).json(data);
  } catch (error) {
    if (error.type === 'timeout') return res.status(504).json({ message: 'Upstream timeout' });
    if (error.type === 'network') return res.status(502).json({ message: 'Gagal terhubung ke upstream' });
    if (error.type === 'upstream') return res.status(error.statusCode).json({ message: error.message });
    return res.status(500).json({ message: 'Terjadi kesalahan pada server' });
  }
}

module.exports = { getSubtitle };
