const express = require('express');
const router = express.Router();
const { getHomeSections } = require('../controllers/homeController');

router.get('/', getHomeSections);

module.exports = router;
