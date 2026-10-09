const fs = require('fs');
const path = require('path');

// Read the original common.js that contains the _0x54b991 generator
const commonJsPath = path.resolve(__dirname, '..', 'common.js');
const code = fs.readFileSync(commonJsPath, 'utf-8');

// Mock window to provide the necessary globals without errors
// It doesn't actually use these for the final kkey generation when passed 11 arguments,
// but they are required to not throw errors during initialization of common.js.
const mockWindow = {
  document: { 
    URL: 'https://kisskh.do/',
    referrer: 'https://kisskh.do/'
  },
  navigator: {
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    platform: 'Win32',
    appName: 'Netscape',
    appCodeName: 'Mozilla'
  },
  MediaMetadata: class {}
};

// Evaluate common.js in a function scope and return the _0x54b991 function
const getGenerator = new Function('window', code + '; return _0x54b991;');
const _0x54b991 = getGenerator(mockWindow);

/**
 * Generate a kkey for an Episode URL.
 * Extracted from Angular chunk 502.
 * @param {string|number} episodeId 
 * @returns {string} The 256 hex character kkey
 */
function generateEpisodeKkey(episodeId) {
    return _0x54b991(
        episodeId.toString(),  // S
        null,                  // u
        '2.8.10',              // h (appVer)
        '62f176f3bb1b5b8e70e39932ad34a0c7', // T (viGuid)
        4830201,               // g (platformVer)
        'kisskh',              // m (appName)
        'kisskh',              // o (appName)
        'kisskh',              // t (appName)
        'kisskh',              // r (appName)
        'kisskh',              // s (appName)
        'kisskh'               // l (appName)
    );
}

/**
 * Generate a kkey for a Subtitle URL.
 * Extracted from Angular chunk 502.
 * @param {string|number} episodeId 
 * @returns {string} The 256 hex character kkey
 */
function generateSubKkey(episodeId) {
    return _0x54b991(
        episodeId.toString(),  // S
        null,                  // u
        '2.8.10',              // h (appVer)
        'VgV52sWhwvBSf8BsM3BRY9weWiiCbtGp', // T (subGuid)
        4830201,               // g (platformVer)
        'kisskh',              // m (appName)
        'kisskh',              // o (appName)
        'kisskh',              // t (appName)
        'kisskh',              // r (appName)
        'kisskh',              // s (appName)
        'kisskh'               // l (appName)
    );
}

module.exports = {
    generateEpisodeKkey,
    generateSubKkey,
    _0x54b991 // export the raw generator just in case
};
