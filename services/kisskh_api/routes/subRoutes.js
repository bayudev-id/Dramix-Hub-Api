const express = require('express');
const router = express.Router();
const { getSubtitle } = require('../controllers/subController');

router.get('/:id', getSubtitle);

router.all('/:id', (req, res) => {
  return res.status(405).json({ message: 'Method tidak diizinkan' });
});

module.exports = router;
