const express = require('express');
const router = express.Router();
const { getUnifiedStream } = require('../controllers/streamController');

router.get('/:id', getUnifiedStream);

module.exports = router;
