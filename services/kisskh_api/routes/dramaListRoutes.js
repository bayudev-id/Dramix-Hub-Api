const express = require('express');
const router = express.Router();
const {
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
} = require('../controllers/dramaListController');

// GET routes
router.get('/Show', getShow);
router.get('/LastUpdate', getLastUpdate);
router.get('/MostView', getMostView);
router.get('/MostView1', getMostView1);
router.get('/MostView2', getMostView2);
router.get('/TopRating', getTopRating);
router.get('/Animate', getAnimate);
router.get('/Upcoming', getUpcoming);
router.get('/List/filters', getListFilters); // MUST be before /List to avoid route conflict
router.get('/List', getList);
router.get('/Drama/:id', getDramaDetail);
router.get('/Episode/:id.png', getEpisode);
router.get('/Search', getSearch);

// 405 Method Not Allowed for non-GET methods on each path
router.all('/Show', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/LastUpdate', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/MostView', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/TopRating', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/Animate', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/Upcoming', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/List/filters', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/List', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/Drama/:id', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/Episode/:id.png', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});
router.all('/Search', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});

module.exports = router;
