const fetchFromKissKH = require('../helpers/fetchFromKissKH');

/**
 * GET /api/Stream/:id
 * Unified endpoint for streams and subtitles
 */
async function getUnifiedStream(req, res) {
  const { id } = req.params;
  const timestamp = new Date().toISOString();
  const randomId = Math.random().toString(36).substring(2, 8);

  try {
    // Fetch both stream and subtitles in parallel
    const [streamData, subData] = await Promise.all([
      fetchFromKissKH(`/api/DramaList/Episode/${id}.png`, req.query),
      fetchFromKissKH(`/api/Sub/${id}`, req.query)
    ]);

    // Format streams (KissKH usually provides one m3u8)
    const streams = [];
    if (streamData && streamData.Video) {
      streams.push({
        url: streamData.Video,
        quality: "Auto",
        format: "m3u8"
      });
    }

    // Format subtitles
    const subtitles = (Array.isArray(subData) ? subData : []).map(sub => ({

      url: sub.src,

      lang: sub.land,
      label: sub.label,
      default: sub.default || false
    }));

    // Construct response
    const response = {
      code: 200,
      message: "Success",
      provider: "kisskh",
      timestamp: `${timestamp} [${randomId}]`,
      data: {
        streams,
        subtitles,
        dubs: [] // KissKH doesn't separate dubs in this endpoint
      }
    };

    return res.status(200).json(response);
  } catch (error) {
    console.error('Unified Stream Error:', error);
    
    let statusCode = 500;
    let message = 'Terjadi kesalahan pada server';

    if (error.type === 'timeout') {
      statusCode = 504;
      message = 'Upstream timeout';
    } else if (error.type === 'network') {
      statusCode = 502;
      message = 'Gagal terhubung ke upstream';
    } else if (error.type === 'upstream') {
      statusCode = error.statusCode;
      message = error.message;
    }

    return res.status(statusCode).json({
      code: statusCode,
      message,
      provider: "kisskh",
      timestamp: `${timestamp} [${randomId}]`,
      data: null
    });
  }
}

module.exports = { getUnifiedStream };
