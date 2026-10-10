require('dotenv').config();

module.exports = {
  PORT: process.env.PORT || 6103,
  UPSTREAM_BASE_URL: process.env.UPSTREAM_BASE_URL || 'https://kisskh.do',
  UPSTREAM_TIMEOUT: parseInt(process.env.UPSTREAM_TIMEOUT) || 10000
};
