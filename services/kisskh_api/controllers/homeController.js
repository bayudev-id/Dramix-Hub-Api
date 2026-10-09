const fetchFromKissKH = require('../helpers/fetchFromKissKH');

/**
 * GET /api/Home/Sections
 * Returns the section metadata for the homepage layout OR the data for a specific section
 */
async function getHomeSections(req, res) {
  const { opId } = req.query;
  const timestamp = new Date().toISOString();
  const randomId = Math.random().toString(36).substring(2, 8);

  // If opId is provided, act as a proxy/mapper
  if (opId) {
    try {
      let data;
      switch (opId) {
        case 'show':
          data = await fetchFromKissKH('/api/DramaList/Show', req.query);
          break;
        case 'lastUpdate':
          data = await fetchFromKissKH('/api/DramaList/LastUpdate', req.query);
          break;
        case 'mostView1':
          data = await fetchFromKissKH('/api/DramaList/MostView', { ...req.query, ispc: true, c: 1 });
          break;
        case 'mostView2':
          data = await fetchFromKissKH('/api/DramaList/MostView', { ...req.query, ispc: true, c: 2 });
          break;
        case 'topRating':
          data = await fetchFromKissKH('/api/DramaList/TopRating', req.query);
          break;
        case 'animate':
          data = await fetchFromKissKH('/api/DramaList/Animate', req.query);
          break;
        case 'upcoming':
          data = await fetchFromKissKH('/api/DramaList/Upcoming', req.query);
          break;
        default:
          return res.status(404).json({ message: 'Section opId tidak ditemukan' });
      }
      return res.status(200).json(data);
    } catch (error) {
      console.error(`Error fetching section ${opId}:`, error);
      return res.status(500).json({ message: 'Gagal mengambil data section' });
    }
  }

  // Otherwise return the static section list
  const sections = [
    {
      "title": "Home Banner",
      "type": "BANNER",
      "opId": "show"
    },
    {
      "title": "Last Update",
      "type": "SUBJECTS_MOVIE",
      "opId": "lastUpdate"
    },
    {
      "title": "Top C-Drama",
      "type": "SUBJECTS_MOVIE",
      "opId": "mostView1"
    },
    {
      "title": "Top K-Drama",
      "type": "SUBJECTS_MOVIE",
      "opId": "mostView2"
    },
    {
      "title": "Hollywood",
      "type": "SUBJECTS_MOVIE",
      "opId": "topRating"
    },
    {
      "title": "Anime",
      "type": "SUBJECTS_MOVIE",
      "opId": "animate"
    },
    {
      "title": "Upcoming",
      "type": "SUBJECTS_MOVIE",
      "opId": "upcoming"
    },
    {
      "title": "Explore",
      "type": "SUBJECTS_MOVIE",
      "opId": "explore"
    }
  ];

  return res.status(200).json({
    code: 200,
    message: "Success",
    provider: "kisskh",
    timestamp: `${timestamp} [${randomId}]`,
    data: sections
  });
}

module.exports = { getHomeSections };
