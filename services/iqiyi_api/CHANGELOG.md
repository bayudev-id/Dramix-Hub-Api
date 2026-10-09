# Changelog

All notable changes to the iQIYI Catalog & VIP Metadata REST API will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-10-06

### Added
- **Direct CDN Video Streaming**: Real-time resolution to iQIYI upstream dispatch (`*.71edge.com` / `meta.video.iqiyi.com`) without local video proxying or storage, eliminating server bandwidth bottlenecks.
- **Playback Endpoints**:
  - `GET /api/play/{tv_id}`: Primary playback endpoint supporting multi-quality streams (240p to 1080p VIP) with optional `bid` bitrate filter.
  - `GET /api/drama/{album_id}/episode/{episode_number}/playback`: Convenience alias mapping drama `album_id` and episode order to `tv_id` automatically.
- **Multi-Language Subtitles**: Automatic WebVTT and SRT subtitle URL resolution mapping upstream `dstl` base URL with standardized ISO language codes (`en`, `id`, `zh-CN`, `zh-TW`, `th`, `vi`, `ms`, etc.).
- **Audio Tracks**: Multi-audio and dubbing track discovery with language codes and default track flags.
- **Pydantic Models**: Complete typed playback models (`StreamQuality`, `SubtitleItem`, `AudioTrackItem`, `PlaybackData`, `PlaybackResponse`).
- **Automatic VIP Inversion**: Upstream requests automatically inject active VIP session cookies (`QC005`, `I00001`, `I00019`) from `data/sessions.json` with fallback for free content.
- **Testing**: 18 new tests across schemas, client resolver, routes, and live E2E integration (total 64 passing tests).

### Changed
- FastAPI service version bumped to `2.0.0` with tag `Playback` added to OpenAPI docs.
- Root endpoint `GET /` updated to report `iQIYI API v2.0.0`.
- `IQIYIClient` expanded with asynchronous `get_playback(tv_id, bid)` and structured `PlaybackError`.

## [1.0.0] - 2026-10-06

### Added
- **Core Architecture**: Standalone FastAPI service running on port 7407 with Direct Client pattern (`IQIYIClient`).
- **Authentication**:
  - `POST /api/auth/login` for username/phone and password authentication.
  - `GET /api/auth/status` to check active session validity and VIP status.
  - RSA password encryption using iQIYI public key.
  - Request signing with `Sign` (MD5) and `Pass-Sign` headers matching Android client (`hx.w0`).
- **Session Management**:
  - Local JSON session persistence (`data/sessions.json`).
  - Automatic `created_at` and `updated_at` timestamps.
  - Validation of mandatory session fields.
- **Catalog Endpoints**:
  - `POST /api/search` with keyword and `pg_num` pagination support.
  - `GET /api/feed` returning curated homepage drama items.
  - `GET /api/tabs` returning available category tabs.
  - `GET /api/drama/{album_id}` returning full drama metadata.
  - `GET /api/drama/{album_id}/episodes` returning drama episode listings.
- **Response Format**: Standardized REST envelope `{code, message, data}` across all endpoints.
- **Testing**: Comprehensive test suite (46 tests: 39 unit tests + 7 live E2E integration tests) covering schemas, crypto, signer, session store, client, all routes, and live iQIYI upstream data validation.
- **Documentation**: Full `README.md` with endpoint documentation, installation guide, and architecture overview.

### Changed
- Replaced FreeReels-style cursor pagination with standard `pg_num` integer pagination for iQIYI API search.
- Decoupled session store from Supabase to local JSON for faster startup and isolated development.
- Fixed server import path issue in `production/run_server.py`.
- Replaced malformed RSA public key with syntactically valid placeholder key in `src/utils/crypto.py`.
- Routed catalog endpoints (`/api/search`, `/api/tabs`, `/api/feed`, `/api/drama/{album_id}`, `/api/drama/{album_id}/episodes`) through verified upstream endpoints (`api/search`, `control/library_nav`, `api/play_data`).

### Known Issues
- **RSA Key Placeholder**: Current `src/utils/crypto.py` uses test RSA key. Real iQIYI public key must be extracted from APK decompilation (`com.iqiyi.i18n` v8.8.5+) for production login. Without real key, login returns `A00006: Signature verification failed`.
- **Single Device ID**: Hardcoded device fingerprint in `Signer` may trigger rate limits or anti-fraud checks on iQIYI side.
- Automated token refresh on 401 (v1.1.0).
- PostgreSQL / Supabase session store migration (v1.1.0).
- Multi-account session support (v1.1.0).
- Video streaming endpoints with m3u8/DRM (v2.0.0).
