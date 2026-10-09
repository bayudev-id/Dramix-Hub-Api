// pb_hooks/source.pb.js
// Dramix Gateway - Unified Streaming & Playback Source Router for /api/modelles/source

routerAdd("GET", "/api/modelles/source", (e) => {
    try {
        const jsonError = function(statusCode, message) {
            const errStr = "{" +
                '"code":' + statusCode + "," +
                '"message":' + JSON.stringify(message) + "," +
                '"data":null' +
            "}";
            return e.blob(statusCode, "application/json", errStr);
        };

        const info = e.requestInfo();

        // 1. Validasi allowed query parameters (strict, no query parameter leakage)
        const queryKeys = Object.keys(info.query || {});
        const allowedKeys = ["model_id", "episode_id", "id"];
        for (let i = 0; i < queryKeys.length; i++) {
            if (allowedKeys.indexOf(queryKeys[i]) === -1) {
                return jsonError(400, "Invalid or missing request parameters");
            }
        }

        const modelId = (info.query.model_id || "").trim();
        const episodeId = (info.query.episode_id || "").trim();
        const contentId = (info.query.id || "").trim() || episodeId;

        if (!modelId || !episodeId) {
            return jsonError(400, "Invalid or missing request parameters");
        }

        // 2. Validasi Provider terhadap database PocketBase
        const providers = $app.findAllRecords("providers");
        let target = null;
        for (let i = 0; i < providers.length; i++) {
            const pid = providers[i].get("provider_id");
            if (pid && pid.toLowerCase() === modelId.toLowerCase()) {
                target = providers[i];
                break;
            }
        }

        if (!target) {
            return jsonError(404, "Provider '" + modelId + "' tidak terdaftar");
        }

        if (target.get("status") !== "active") {
            return jsonError(403, "Provider '" + target.get("name") + "' sedang nonaktif");
        }

        const canonicalId = target.get("provider_id");
        const normalizedId = canonicalId.toLowerCase();

        let streams = [];
        let subtitles = [];
        let headers = {};
        let durationSeconds = 0;

        // 1. KissKH (Port 7403)
        if (normalizedId === "kisskh") {
            const res = $http.send({
                url: "http://127.0.0.1:7403/api/Stream/" + encodeURIComponent(episodeId),
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari KissKH service");
            }
            const d = (res.json && res.json.data) || res.json || {};
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawSubs = Array.isArray(d.subtitles) ? d.subtitles : [];

            for (let i = 0; i < rawStreams.length; i++) {
                let u = String(rawStreams[i].url || "");
                if (u.indexOf("//") === 0) u = "https:" + u;
                streams.push({
                    quality: String(rawStreams[i].quality || "Auto"),
                    format: String(rawStreams[i].format || "m3u8").toLowerCase(),
                    url: u,
                    is_drm: false,
                    drm: null
                });
            }

            for (let i = 0; i < rawSubs.length; i++) {
                let u = String(rawSubs[i].url || rawSubs[i].src || "");
                if (u.indexOf("//") === 0) u = "https:" + u;
                subtitles.push({
                    lang: String(rawSubs[i].lang || rawSubs[i].land || ""),
                    label: String(rawSubs[i].label || rawSubs[i].lang || rawSubs[i].land || ""),
                    url: u
                });
            }
        }
        // 2. WeTV (Port 7402)
        else if (normalizedId === "wetv") {
            const cid = contentId;
            const vid = episodeId;
            const res = $http.send({
                url: "http://127.0.0.1:7402/api/wetv/play/" + encodeURIComponent(cid) + "/" + encodeURIComponent(vid),
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari WeTV service");
            }
            const d = (res.json && res.json.data) || res.json || {};
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawSubs = Array.isArray(d.subtitles) ? d.subtitles : [];

            for (let i = 0; i < rawStreams.length; i++) {
                streams.push({
                    quality: String(rawStreams[i].quality || "Auto"),
                    format: String(rawStreams[i].format || "hls").toLowerCase(),
                    url: String(rawStreams[i].url || ""),
                    is_drm: false,
                    drm: null,
                    headers: {
                        "Referer": "https://wetv.vip/",
                        "User-Agent": "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
                    }
                });
            }

            for (let i = 0; i < rawSubs.length; i++) {
                subtitles.push({
                    lang: String(rawSubs[i].lang || rawSubs[i].code || ""),
                    label: String(rawSubs[i].label || rawSubs[i].name || rawSubs[i].lang || ""),
                    url: String(rawSubs[i].url || "")
                });
            }
        }
        // 3. MovieBox (Port 7404)
        else if (normalizedId === "moviebox") {
            headers = {
                "Referer": "https://moviebox.ph/"
            };

            let se = "0";
            let ep = "1";
            if (episodeId.indexOf("_") !== -1) {
                const parts = episodeId.split("_");
                se = parts[0] || "0";
                ep = parts[1] || "1";
            } else if (episodeId.indexOf(":") !== -1) {
                const parts = episodeId.split(":");
                se = parts[0] || "0";
                ep = parts[1] || "1";
            } else if (/^[0-9]+$/.test(episodeId)) {
                ep = episodeId;
            }

            if (!/^[0-9]+$/.test(se)) se = "0";
            if (!/^[0-9]+$/.test(ep)) ep = "1";

            let qUrl = "http://127.0.0.1:7404/play?season=" + encodeURIComponent(se + ":" + ep);
            if (/^[0-9]+$/.test(contentId)) {
                qUrl += "&subjectId=" + encodeURIComponent(contentId) + "&detailPath=";
            } else {
                qUrl += "&detailPath=" + encodeURIComponent(contentId) + "&subjectId=";
            }

            const res = $http.send({
                url: qUrl,
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari MovieBox service");
            }

            const d = (res.json && res.json.data) || res.json || {};
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawCaptions = Array.isArray(d.captions) ? d.captions : [];

            for (let i = 0; i < rawStreams.length; i++) {
                const s = rawStreams[i];
                let q = "Auto";
                if (s.resolutions) {
                    q = String(s.resolutions) + "p";
                }
                streams.push({
                    quality: q,
                    format: String(s.format || "mp4").toLowerCase(),
                    url: String(s.url || ""),
                    is_drm: false,
                    drm: null
                });
            }

            for (let i = 0; i < rawCaptions.length; i++) {
                const c = rawCaptions[i];
                subtitles.push({
                    lang: String(c.lan || ""),
                    label: String(c.lan_name || c.lan_desc || c.lan || ""),
                    url: String(c.url || "")
                });
            }
        }
        // 4. Viu (Port 7405)
        else if (normalizedId === "viu") {
            const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
            const res = $http.send({
                url: "http://127.0.0.1:7405/api/drama-api/stream?id=" + encodeURIComponent(contentId) + "&episode_id=" + encodeURIComponent(episodeId) + "&provider=viu&api_key=" + apiKey,
                headers: {
                    "Authorization": "Bearer " + apiKey
                },
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari Viu service");
            }

            const d = (res.json && res.json.data) || res.json || {};
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawSubs = Array.isArray(d.subtitles) ? d.subtitles : [];

            for (let i = 0; i < rawStreams.length; i++) {
                let streamUrl = String(rawStreams[i].url || "");
                
                // Rewrite localhost VIU service URLs untuk network accessibility
                if (streamUrl.indexOf("http://127.0.0.1:7405") === 0) {
                    // Replace dengan LAN IP gateway server (TODO: make configurable)
                    streamUrl = streamUrl.replace("http://127.0.0.1:7405", "http://192.168.18.200:7405");
                }
                
                streams.push({
                    quality: String(rawStreams[i].quality || "Auto"),
                    format: String(rawStreams[i].format || "hls").toLowerCase(),
                    url: streamUrl,
                    is_drm: false,
                    drm: null
                });
            }

            for (let i = 0; i < rawSubs.length; i++) {
                subtitles.push({
                    lang: String(rawSubs[i].lang || ""),
                    label: String(rawSubs[i].label || rawSubs[i].lang || ""),
                    url: String(rawSubs[i].url || "")
                });
            }
        }
        // 5. FreeReels (Port 7406)
        else if (normalizedId === "freereels") {
            const res = $http.send({
                url: "http://127.0.0.1:7406/detail?id=" + encodeURIComponent(contentId) + "&episode_id=" + encodeURIComponent(episodeId),
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari FreeReels service");
            }

            const info = (res.json && res.json.data && res.json.data.info) || {};
            let targetEp = info.episode || null;
            if (!targetEp && Array.isArray(info.episode_list)) {
                for (let i = 0; i < info.episode_list.length; i++) {
                    const ep = info.episode_list[i];
                    if (String(ep.id) === episodeId || String(ep.index) === episodeId) {
                        targetEp = ep;
                        break;
                    }
                }
                if (!targetEp && info.episode_list.length > 0) {
                    targetEp = info.episode_list[0];
                }
            }

            if (targetEp) {
                durationSeconds = parseInt(targetEp.duration, 10) || 0;
                if (targetEp.external_audio_h264_m3u8) {
                    streams.push({
                        quality: "Auto (H264)",
                        format: "m3u8",
                        url: String(targetEp.external_audio_h264_m3u8),
                        is_drm: false,
                        drm: null
                    });
                }
                if (targetEp.external_audio_h265_m3u8) {
                    streams.push({
                        quality: "Auto (H265)",
                        format: "m3u8",
                        url: String(targetEp.external_audio_h265_m3u8),
                        is_drm: false,
                        drm: null
                    });
                }
                if (targetEp.m3u8_url) {
                    streams.push({
                        quality: "Auto",
                        format: "m3u8",
                        url: String(targetEp.m3u8_url),
                        is_drm: false,
                        drm: null
                    });
                }
                if (targetEp.video_url) {
                    streams.push({
                        quality: "Auto",
                        format: "mp4",
                        url: String(targetEp.video_url),
                        is_drm: false,
                        drm: null
                    });
                }
                if (Array.isArray(targetEp.subtitle_list)) {
                    for (let i = 0; i < targetEp.subtitle_list.length; i++) {
                        const sub = targetEp.subtitle_list[i];
                        subtitles.push({
                            lang: String(sub.language || ""),
                            label: String(sub.language || ""),
                            url: String(sub.subtitle || "")
                        });
                    }
                }
            }
        }
        // 6. iQIYI (Port 7407)
        else if (normalizedId === "iqiyi") {
            const res = $http.send({
                url: "http://127.0.0.1:7407/api/play/" + encodeURIComponent(episodeId),
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari iQIYI service");
            }

            const d = (res.json && res.json.data) || res.json || {};
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawSubs = Array.isArray(d.subtitles) ? d.subtitles : [];

            for (let i = 0; i < rawStreams.length; i++) {
                let u = String(rawStreams[i].url || "");
                if (u.indexOf("/") === 0) u = "http://127.0.0.1:7407" + u;
                streams.push({
                    quality: String(rawStreams[i].quality || "Auto"),
                    format: String(rawStreams[i].format || "m3u8").toLowerCase(),
                    url: u,
                    is_drm: Boolean(rawStreams[i].is_drm),
                    drm: rawStreams[i].drm || null
                });
            }

            for (let i = 0; i < rawSubs.length; i++) {
                const s = rawSubs[i];
                subtitles.push({
                    lang: String(s.lang_code || s.language || ""),
                    label: String(s.language || s.lang_code || ""),
                    url: String(s.url || "")
                });
            }
        }
        // 7. CineFlow Hub Upstream (Port 7401 - 18 Provider)
        else {
            let effectiveEpisodeId = episodeId;
            let effectiveContentId = contentId;

            // Handle CineTv bittvd_ base64 encoded IDs automatically
            if (normalizedId === "cinetv" && effectiveEpisodeId.indexOf("bittvd_") === 0) {
                try {
                    const b64 = effectiveEpisodeId.replace("bittvd_", "");
                    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
                    let decodedStr = "";
                    let strClean = String(b64).replace(/=+$/, "");
                    for (let bc = 0, bs, buffer, idx = 0; buffer = strClean.charAt(idx++); ~buffer && (bs = bc % 4 ? bs * 64 + buffer : buffer, bc++ % 4) ? decodedStr += String.fromCharCode(255 & bs >> (-2 * bc & 6)) : 0) {
                        buffer = chars.indexOf(buffer);
                    }
                    const parsed = JSON.parse(decodedStr);
                    if (parsed && parsed.cc && parsed.cid) {
                        effectiveEpisodeId = "bittv:" + parsed.cc + ":" + parsed.cid;
                        effectiveContentId = effectiveEpisodeId;
                    }
                } catch (err) {
                    // Fallback to original
                }
            }

            const res = $http.send({
                url: "http://127.0.0.1:7401/api/modelles/source?model_id=" + encodeURIComponent(canonicalId) + "&id=" + encodeURIComponent(effectiveContentId) + "&episode_id=" + encodeURIComponent(effectiveEpisodeId),
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil stream dari CineFlow upstream");
            }

            const d = (res.json && res.json.data) || res.json || {};
            if (d.headers && typeof d.headers === "object") {
                headers = d.headers;
            }
            durationSeconds = Math.round(d.duration_seconds || (d.duration_ms ? d.duration_ms / 1000 : 0)) || 0;
            const rawStreams = Array.isArray(d.streams) ? d.streams : [];
            const rawSubs = Array.isArray(d.subtitles) ? d.subtitles : [];

            for (let i = 0; i < rawStreams.length; i++) {
                const s = rawStreams[i];
                streams.push({
                    quality: String(s.quality || "Auto"),
                    format: String(s.format || "m3u8").toLowerCase(),
                    url: String(s.url || s.master_url || ""),
                    is_drm: Boolean(s.is_drm),
                    drm: s.drm || null,
                    headers: s.headers || null
                });
            }

            for (let i = 0; i < rawSubs.length; i++) {
                const s = rawSubs[i];
                subtitles.push({
                    lang: String(s.lang || ""),
                    label: String(s.name || s.label || s.lang || ""),
                    url: String(s.url || "")
                });
            }
        }

        // 3. Format JSON secara manual dan deterministik
        const streamStrings = streams.map(s => {
            const sHeaders = s.headers || headers || {};
            return "{" +
                '"quality":' + JSON.stringify(s.quality || "Auto") + "," +
                '"format":' + JSON.stringify(s.format || "m3u8") + "," +
                '"url":' + JSON.stringify(s.url || "") + "," +
                '"is_drm":' + (s.is_drm ? "true" : "false") + "," +
                '"drm":' + (s.drm ? JSON.stringify(s.drm) : "null") + "," +
                '"headers":' + JSON.stringify(sHeaders) +
            "}";
        });

        const subtitleStrings = subtitles.map(sub => {
            return "{" +
                '"lang":' + JSON.stringify(sub.lang || "") + "," +
                '"label":' + JSON.stringify(sub.label || "") + "," +
                '"url":' + JSON.stringify(sub.url || "") +
            "}";
        });

        const jsonStr = "{" +
            '"code":200,' +
            '"message":"success",' +
            '"data":{' +
                '"id":' + JSON.stringify(contentId) + "," +
                '"episode_id":' + JSON.stringify(episodeId) + "," +
                '"duration_seconds":' + durationSeconds + "," +
                '"headers":' + JSON.stringify(headers) + "," +
                '"streams":[' + streamStrings.join(",") + "]," +
                '"subtitles":[' + subtitleStrings.join(",") + "]" +
            "}" +
        "}";

        return e.blob(200, "application/json", jsonStr);

    } catch (err) {
        return jsonError(500, "Gateway error: " + err);
    }
});
