// pb_hooks/detail.pb.js
// Dramix Gateway - Unified Drama & Episode Detail Router for /api/modelles/detail

routerAdd("GET", "/api/modelles/detail", (e) => {
    try {
        const jsonError = function(statusCode, message) {
            const errStr = "{" +
                '"code":' + statusCode + "," +
                '"message":' + JSON.stringify(message) + "," +
                '"data":null' +
            "}";
            return e.blob(statusCode, "application/json", errStr);
        };

        const parseScoreAndViews = function(rawScore, rawViews) {
            let score = "0";
            let views = "";

            if (rawViews !== undefined && rawViews !== null && String(rawViews).trim() !== "" && String(rawViews).trim() !== "0") {
                views = String(rawViews).trim();
            }

            if (rawScore !== undefined && rawScore !== null && String(rawScore).trim() !== "") {
                const s = String(rawScore).trim();
                if (/[kKmMbB]/.test(s) || (!isNaN(parseFloat(s)) && parseFloat(s) > 50)) {
                    if (!views) {
                        views = s;
                    }
                } else {
                    score = s;
                }
            }

            return { score: score, views: views };
        };

        const sanitizeCoverUrl = function(url) {
            if (!url || typeof url !== "string") return "";
            const trimmed = url.trim();
            if (!trimmed) return "";
            
            // Extract from serveproxy wrapper
            if (trimmed.includes("serveproxy.com") && trimmed.includes("?url=")) {
                const urlParamIndex = trimmed.indexOf("?url=");
                if (urlParamIndex !== -1) {
                    const extractedUrl = trimmed.substring(urlParamIndex + 5);
                    if (extractedUrl.startsWith("http://") || extractedUrl.startsWith("https://")) {
                        return extractedUrl;
                    }
                }
            }
            
            // Convert HTTP → HTTPS for known CDNs
            if (trimmed.startsWith("http://pic") && trimmed.includes("iqiyipic.com")) {
                return trimmed.replace("http://", "https://");
            }
            if (trimmed.startsWith("http://m.ykimg.com")) {
                return trimmed.replace("http://", "https://");
            }
            
            return trimmed;
        };

        const info = e.requestInfo();

        // 1. Validasi allowed query parameters (strict, no query parameter leakage)
        const queryKeys = Object.keys(info.query || {});
        const allowedKeys = ["model_id", "id"];
        for (let i = 0; i < queryKeys.length; i++) {
            if (allowedKeys.indexOf(queryKeys[i]) === -1) {
                return jsonError(400, "Invalid or missing request parameters");
            }
        }

        const modelId = (info.query.model_id || "").trim();
        const contentId = (info.query.id || "").trim();

        if (!modelId || !contentId) {
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

        let detail = null;

        // 1. KissKH (Port 6103)
        if (normalizedId === "kisskh") {
            const res = $http.send({
                url: "http://127.0.0.1:6103/api/Drama/" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil detail drama dari KissKH service");
            }
            const d = (res.json && res.json.data) || res.json || {};
            const rawEps = Array.isArray(d.episodes) ? d.episodes : [];
            const episodes = [];
            for (let i = 0; i < rawEps.length; i++) {
                const ep = rawEps[i];
                episodes.push({
                    id: String(ep.id),
                    title: "Episode " + (ep.number || (i + 1)),
                    number: parseInt(ep.number, 10) || (i + 1),
                    cover: String(d.thumbnail || ""),
                    duration_seconds: 0,
                    is_vip: false,
                    is_express: false,
                    is_trailer: false,
                    label: "",
                    tags: []
                });
            }

            const itemType = (d.type && String(d.type).toLowerCase() === "anime") ? "anime" : "drama";
            const tags = [];
            if (d.country) tags.push(String(d.country));
            if (d.status) tags.push(String(d.status));

            detail = {
                id: String(d.id || contentId),
                title: String(d.title || ""),
                cover: String(d.thumbnail || ""),
                description: String(d.description || ""),
                type: itemType,
                source: "KissKH",
                release_date: String(d.releaseDate || ""),
                score: "0",
                views: "",
                is_vip: false,
                tags: tags,
                total_episodes: episodes.length,
                seasons: [{
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                }],
                cast: []
            };
        }
        // 2. WeTV (Port 6102)
        else if (normalizedId === "wetv") {
            const res = $http.send({
                url: "http://127.0.0.1:6102/api/wetv/album/" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil detail album dari WeTV service");
            }
            const alb = (res.json && res.json.album) || {};
            const rawEps = (res.json && Array.isArray(res.json.episodes)) ? res.json.episodes : [];
            const episodes = [];
            let hasSewa = false;
            let hasVip = Boolean(alb.is_vip);
            let hasFastTrack = false;

            for (let i = 0; i < rawEps.length; i++) {
                const ep = rawEps[i];
                const epNum = parseInt(ep.episode, 10) || (i + 1);
                const epLabel = String(ep.label || "").trim();
                const epIsVip = Boolean(ep.is_vip || epLabel.toUpperCase() === "VIP");
                const epIsExpress = Boolean(ep.is_express || epLabel.toUpperCase() === "FAST TRACK" || epLabel.toUpperCase() === "EXPRESS");
                const epIsTrailer = Boolean(ep.is_trailer || epLabel.toUpperCase() === "TRAILER");
                
                let epTags = Array.isArray(ep.tags) ? ep.tags.slice() : [];
                if (epLabel && epTags.indexOf(epLabel) === -1) {
                    epTags.unshift(epLabel);
                }
                if (epIsVip && epTags.indexOf("VIP") === -1) {
                    epTags.unshift("VIP");
                    hasVip = true;
                }
                const epIsSewa = Boolean(epLabel.toLowerCase() === "sewa" || epTags.some(t => String(t).toLowerCase() === "sewa"));
                if (epIsSewa) {
                    hasSewa = true;
                }
                if (epIsExpress) {
                    hasFastTrack = true;
                }

                episodes.push({
                    id: String(ep.vid || ep.id || (contentId + "_" + (i + 1))),
                    title: String(ep.title || ("Episode " + epNum)),
                    number: epNum,
                    cover: sanitizeCoverUrl(String(ep.cover || alb.cover_h || alb.cover_v || "")),
                    duration_seconds: 0,
                    is_vip: epIsVip,
                    is_sewa: epIsSewa,
                    is_express: epIsExpress,
                    is_trailer: epIsTrailer,
                    label: epLabel,
                    tags: epTags
                });
            }

            const sv = parseScoreAndViews(alb.score, "");
            let dramaTags = Array.isArray(alb.genres) ? alb.genres.slice() : [];
            if (alb.update_info && alb.update_info.toLowerCase().indexOf("berbayar") !== -1) {
                hasSewa = true;
            }

            if (hasFastTrack && dramaTags.indexOf("Fast Track") === -1) {
                dramaTags.unshift("Fast Track");
            }
            if (hasSewa && dramaTags.indexOf("Sewa") === -1) {
                dramaTags.unshift("Sewa");
            }
            if (hasVip && dramaTags.indexOf("VIP") === -1) {
                dramaTags.unshift("VIP");
            }

            // Map WeTV cast (directors + actors with avatars)
            let cast = [];
            if (Array.isArray(alb.cast)) {
                for (let ci = 0; ci < alb.cast.length; ci++) {
                    const person = alb.cast[ci];
                    const rawRole = String(person.role || "actor").trim().toLowerCase();
                    const pName = String(person.name || "").trim();
                    if (!pName) continue;
                    const isDir = rawRole === "director" || rawRole === "sutradara";
                    const label = isDir ? "Director" : (rawRole || "Actor");
                    cast.push({
                        id: String(person.id || ("wetv_" + ci)),
                        name: pName,
                        role: label,
                        cover: String(person.avatar || ""),
                        is_director: isDir
                    });
                }
            }

            detail = {
                id: String(alb.cid || contentId),
                title: String(alb.title || ""),
                cover: String(alb.cover_h || alb.cover_v || ""),
                description: String(alb.description || ""),
                type: (episodes.length <= 1 && alb.total_episodes <= 1) ? "movie" : "drama",
                source: "WeTV",
                release_date: String(alb.year || ""),
                score: sv.score,
                views: sv.views,
                is_vip: hasVip,
                tags: dramaTags,
                total_episodes: episodes.length,
                seasons: [{
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                }],
                cast: cast
            };
        }
        // 3. MovieBox (Port 6104)
        else if (normalizedId === "moviebox") {
            let res = $http.send({
                url: "http://127.0.0.1:6104/detail?detailPath=" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                res = $http.send({
                    url: "http://127.0.0.1:6104/detail?detailPath=&subjectId=" + encodeURIComponent(contentId),
                    method: "GET",
                    timeout: 10
                });
            }
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil detail film dari MovieBox service");
            }

            const d = (res.json && res.json.data) || res.json || {};
            const rawSeasons = Array.isArray(d.seasons) ? d.seasons : [];
            const seasons = [];
            let totalEpsCount = 0;

            for (let sIdx = 0; sIdx < rawSeasons.length; sIdx++) {
                const s = rawSeasons[sIdx];
                const sNum = parseInt(s.season_num, 10) || (sIdx + 1);
                const episodes = [];

                if (s.all_ep && typeof s.all_ep === "string") {
                    const epTokens = s.all_ep.split(",");
                    for (let eIdx = 0; eIdx < epTokens.length; eIdx++) {
                        const token = epTokens[eIdx].trim();
                        if (token) {
                            const epNum = parseInt(token, 10) || (eIdx + 1);
                            episodes.push({
                                id: sNum + "_" + epNum,
                                title: "Episode " + epNum,
                                number: epNum,
                                cover: String(d.cover || ""),
                                duration_seconds: 0,
                                is_vip: false,
                                is_express: false,
                                is_trailer: false,
                                label: "",
                                tags: []
                            });
                        }
                    }
                } else if (s.max_ep && parseInt(s.max_ep, 10) > 0) {
                    const maxEp = parseInt(s.max_ep, 10);
                    for (let epNum = 1; epNum <= maxEp; epNum++) {
                        episodes.push({
                            id: sNum + "_" + epNum,
                            title: "Episode " + epNum,
                            number: epNum,
                            cover: String(d.cover || ""),
                            duration_seconds: 0,
                            is_vip: false,
                            is_express: false,
                            is_trailer: false,
                            label: "",
                            tags: []
                        });
                    }
                }

                totalEpsCount += episodes.length;
                seasons.push({
                    name: "Season " + sNum,
                    index: sNum,
                    total_episodes: episodes.length,
                    episodes: episodes
                });
            }

            let itemType = "movie";
            if (d.subject_type === 2) itemType = "drama";
            else if (d.subject_type === 7) itemType = "short_drama";

            const sv = parseScoreAndViews(d.imdb_rating, "");
            const tags = Array.isArray(d.genre) ? d.genre.slice() : [];

            if (totalEpsCount === 0 || seasons.length === 0 || (seasons.length === 1 && seasons[0].episodes.length === 0)) {
                totalEpsCount = 1;
                seasons.length = 0;
                seasons.push({
                    name: "Full Movie",
                    index: 1,
                    total_episodes: 1,
                    episodes: [{
                        id: "0_1",
                        title: String(d.title || "Full Movie"),
                        number: 1,
                        cover: String(d.cover || ""),
                        duration_seconds: 0,
                        is_vip: false,
                        is_express: false,
                        is_trailer: false,
                        label: "Movie",
                        tags: []
                    }]
                });
            }

            let dubs = [];
            if (Array.isArray(d.dubs)) {
                dubs = d.dubs.map(function(dub) {
                    return {
                        id: String(dub.detail_path || dub.subject_id || ""),
                        title: String(dub.lan_name || ""),
                        lan_code: String(dub.lan_code || ""),
                        is_original: !!dub.is_original
                    };
                });
            }

            // Map cast/stars (actors + directors with roles & avatars)
            let cast = [];
            if (Array.isArray(d.stars)) {
                cast = d.stars.map(function(st) {
                    const rawRole = String(st.character || "").trim();
                    const isDir = rawRole.toLowerCase() === "director" || rawRole.toLowerCase() === "sutradara";
                    return {
                        id: String(st.staff_id || st.detail_path || ""),
                        name: String(st.name || "").trim(),
                        role: rawRole || (isDir ? "Director" : "Actor"),
                        cover: String(st.avatar_url || ""),
                        is_director: isDir
                    };
                }).filter(function(c) { return c.name.length > 0; });
            }

            detail = {
                id: String(d.detail_path || d.subject_id || contentId),
                title: String(d.title || ""),
                cover: String(d.cover || ""),
                description: String(d.description || ""),
                type: itemType,
                source: "MovieBox",
                release_date: String(d.release_date || ""),
                score: sv.score,
                views: sv.views,
                is_vip: false,
                tags: tags,
                total_episodes: totalEpsCount,
                seasons: seasons,
                dubs: dubs,
                cast: cast
            };
        }
        // 4. Viu (Port 6105)
        else if (normalizedId === "viu") {
            const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
            let pListRes = $http.send({
                url: "http://127.0.0.1:6105/api/mobile?r=/vod/product-list&series_id=" + encodeURIComponent(contentId) + "&size=100&sort=ASC&api_key=" + apiKey,
                method: "GET",
                timeout: 10
            });

            let rawProducts = (pListRes.json && pListRes.json.data && Array.isArray(pListRes.json.data.product_list)) ? pListRes.json.data.product_list : [];
            let seriesMeta = {};

            if (rawProducts.length === 0) {
                const detRes = $http.send({
                    url: "http://127.0.0.1:6105/api/mobile?r=/vod/detail&product_id=" + encodeURIComponent(contentId) + "&os_flag_id=1&api_key=" + apiKey,
                    method: "GET",
                    timeout: 10
                });
                if (detRes.statusCode === 200 && detRes.json && detRes.json.data) {
                    seriesMeta = detRes.json.data.series || {};
                    const realSeriesId = seriesMeta.series_id || (detRes.json.data.current_product && detRes.json.data.current_product.series_id);
                    if (realSeriesId) {
                        pListRes = $http.send({
                            url: "http://127.0.0.1:6105/api/mobile?r=/vod/product-list&series_id=" + encodeURIComponent(realSeriesId) + "&size=100&sort=ASC&api_key=" + apiKey,
                            method: "GET",
                            timeout: 10
                        });
                        rawProducts = (pListRes.json && pListRes.json.data && Array.isArray(pListRes.json.data.product_list)) ? pListRes.json.data.product_list : [];
                    }
                }
            } else if (rawProducts.length > 0) {
                const firstEpId = rawProducts[0].product_id;
                if (firstEpId) {
                    const detRes = $http.send({
                        url: "http://127.0.0.1:6105/api/mobile?r=/vod/detail&product_id=" + encodeURIComponent(firstEpId) + "&os_flag_id=1&api_key=" + apiKey,
                        method: "GET",
                        timeout: 10
                    });
                    if (detRes.statusCode === 200 && detRes.json && detRes.json.data) {
                        seriesMeta = detRes.json.data.series || {};
                    }
                }
            }

            if (rawProducts.length === 0 && !seriesMeta.name) {
                return jsonError(404, "Detail drama Viu tidak ditemukan untuk ID '" + contentId + "'");
            }

            let hasVip = Boolean(seriesMeta.is_free_premium_time === 0);
            const episodes = [];
            for (let i = 0; i < rawProducts.length; i++) {
                const ep = rawProducts[i];
                const epNum = parseInt(ep.number, 10) || (i + 1);
                const isEpVip = Boolean(ep.is_free_premium_time === 0 || ep.user_level > 1 || ep.premium_time > 0);
                if (isEpVip) hasVip = true;
                episodes.push({
                    id: String(ep.product_id),
                    title: String(ep.synopsis || ("Episode " + epNum)),
                    number: epNum,
                    cover: String(ep.cover_image_url || seriesMeta.cover_landscape_image_url || ""),
                    duration_seconds: 0,
                    is_vip: isEpVip,
                    is_express: false,
                    is_trailer: false,
                    label: isEpVip ? "VIP" : "",
                    tags: isEpVip ? ["VIP"] : []
                });
            }

            const isMovie = seriesMeta.is_movie === 1 || seriesMeta.is_movie === "1";
            const tags = [];
            if (seriesMeta.category_name) tags.push(seriesMeta.category_name);
            if (hasVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

            detail = {
                id: String(seriesMeta.series_id || contentId),
                title: String(seriesMeta.name || (rawProducts[0] && rawProducts[0].synopsis) || ""),
                cover: sanitizeCoverUrl(String(seriesMeta.cover_landscape_image_url || seriesMeta.cover_portrait_image_url || (rawProducts[0] && rawProducts[0].cover_image_url) || "")),
                description: String(seriesMeta.description || ""),
                type: isMovie ? "movie" : "drama",
                source: "Viu",
                release_date: String(seriesMeta.release_of_year || ""),
                score: "0",
                views: "",
                is_vip: hasVip,
                tags: tags,
                total_episodes: episodes.length,
                seasons: [{
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                }],
                cast: []
            };
        }
        // 5. FreeReels (Port 6106)
        else if (normalizedId === "freereels") {
            const res = $http.send({
                url: "http://127.0.0.1:6106/detail?id=" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil detail video dari FreeReels service");
            }

            const info = (res.json && res.json.data && res.json.data.info) || {};
            const rawEps = Array.isArray(info.episode_list) ? info.episode_list : [];
            const episodes = [];

            for (let i = 0; i < rawEps.length; i++) {
                const ep = rawEps[i];
                const epNum = ep.index || (i + 1);
                const epIsVip = Boolean(ep.video_type !== "free" || ep.free === false || ep.unlock === false);
                const epIsTrailer = Boolean(ep.is_blooper);
                let epLabel = "";
                let epTags = [];

                if (epIsVip) {
                    epLabel = "VIP";
                    epTags.push("VIP");
                } else if (ep.episode_price && ep.episode_price > 0 && !ep.unlock) {
                    epLabel = "Koin";
                    epTags.push("Koin");
                }

                episodes.push({
                    id: String(ep.id || (contentId + "_" + epNum)),
                    title: String(ep.name || ("Episode " + epNum)),
                    number: epNum,
                    cover: String(ep.cover || info.cover || ""),
                    duration_seconds: ep.duration || 0,
                    is_vip: epIsVip,
                    is_express: false,
                    is_trailer: epIsTrailer,
                    label: epLabel,
                    tags: epTags
                });
            }

            let tags = [];
            if (Array.isArray(info.tag)) tags = tags.concat(info.tag);
            if (Array.isArray(info.content_tags)) tags = tags.concat(info.content_tags);
            const isVip = Boolean(info.vip_type !== 0 || info.free === false);
            if (isVip && tags.indexOf("VIP") === -1) {
                tags.unshift("VIP");
            }

            let followFormatted = "";
            const fCount = info.follow_count || info.view_count;
            if (fCount && fCount > 0) {
                if (fCount >= 1000000) {
                    followFormatted = (Math.round(fCount / 100000) / 10) + "M";
                } else if (fCount >= 1000) {
                    followFormatted = (Math.round(fCount / 100) / 10) + "K";
                } else {
                    followFormatted = String(fCount);
                }
            }

            const sv = parseScoreAndViews("0", followFormatted);

            detail = {
                id: String(info.id || contentId),
                title: String(info.name || ""),
                cover: String(info.cover || ""),
                description: String(info.desc || ""),
                type: "short_drama",
                source: "FreeReels",
                release_date: "",
                score: sv.score,
                views: sv.views,
                is_vip: isVip,
                tags: tags,
                total_episodes: episodes.length,
                seasons: [{
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                }],
                cast: []
            };
        }
        // 6. iQIYI (Port 6107)
        else if (normalizedId === "iqiyi") {
            const infoRes = $http.send({
                url: "http://127.0.0.1:6107/api/drama/" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 10
            });
            if (infoRes.statusCode !== 200) {
                return jsonError(infoRes.statusCode === 404 ? 404 : 502, "Gagal mengambil metadata drama dari iQIYI service");
            }
            const info = (infoRes.json && infoRes.json.data) || {};

            const epsRes = $http.send({
                url: "http://127.0.0.1:6107/api/drama/" + encodeURIComponent(contentId) + "/episodes",
                method: "GET",
                timeout: 10
            });
            const rawEps = (epsRes.statusCode === 200 && epsRes.json && Array.isArray(epsRes.json.data)) ? epsRes.json.data : [];
            const episodes = [];
            let hasVip = Boolean(info.vip_status || info.is_vip);

            for (let i = 0; i < rawEps.length; i++) {
                const ep = rawEps[i];
                const epNum = ep.episode_number || (i + 1);
                const epIsVip = Boolean(ep.is_vip);
                if (epIsVip) hasVip = true;
                episodes.push({
                    id: String(ep.video_id || epNum),
                    title: String(ep.title || ("Episode " + epNum)),
                    number: epNum,
                    cover: sanitizeCoverUrl(String(info.cover || info.banner || "")),
                    duration_seconds: ep.duration || 0,
                    is_vip: epIsVip,
                    is_express: false,
                    is_trailer: false,
                    label: epIsVip ? "VIP" : "",
                    tags: epIsVip ? ["VIP"] : []
                });
            }

            const sv = parseScoreAndViews(info.score || info.rating, info.score_votes ? String(info.score_votes) : "");
            let tags = Array.isArray(info.tags) ? info.tags.slice() : [];
            if (info.genre && tags.indexOf(info.genre) === -1) tags.push(info.genre);
            if (hasVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

            // Map iQIYI directors and main actors
            let cast = [];
            if (Array.isArray(info.directors)) {
                for (let di = 0; di < info.directors.length; di++) {
                    const dir = info.directors[di];
                    const dirName = String(dir.name || "").trim();
                    if (dirName) {
                        cast.push({
                            id: String(dir.id || ("dir_" + di)),
                            name: dirName,
                            role: String(dir.role || "Sutradara").trim(),
                            cover: String(dir.image || ""),
                            is_director: true
                        });
                    }
                }
            }
            if (Array.isArray(info.main_actors)) {
                for (let ai = 0; ai < info.main_actors.length; ai++) {
                    const act = info.main_actors[ai];
                    const actName = String(act.name || "").trim();
                    if (actName) {
                        cast.push({
                            id: String(act.id || ("act_" + ai)),
                            name: actName,
                            role: String(act.role || "Pemeran Utama").trim(),
                            cover: String(act.image || ""),
                            is_director: false
                        });
                    }
                }
            }

            detail = {
                id: String(info.id || contentId),
                title: String(info.name || info.title || ""),
                cover: String(info.cover || info.banner || ""),
                description: String(info.desc || ""),
                type: "drama",
                source: "iQIYI",
                release_date: String(info.year || ""),
                score: sv.score,
                views: sv.views,
                is_vip: hasVip,
                tags: tags,
                total_episodes: episodes.length,
                seasons: [{
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                }],
                cast: cast
            };
        }
        // 7. CineFlow Hub Upstream (Port 6101 - 18 Provider)
        else {
            const cfRes = $http.send({
                url: "http://127.0.0.1:6101/api/modelles/detail?model_id=" + encodeURIComponent(canonicalId) + "&id=" + encodeURIComponent(contentId),
                method: "GET",
                timeout: 15
            });
            if (cfRes.statusCode !== 200) {
                return jsonError(cfRes.statusCode === 404 ? 404 : 502, "Gagal mengambil detail konten dari CineFlow upstream");
            }
            const d = (cfRes.json && cfRes.json.data) || {};

            let seasons = [];
            let totalEpsCount = 0;

            if (Array.isArray(d.seasons) && d.seasons.length > 0) {
                for (let sIdx = 0; sIdx < d.seasons.length; sIdx++) {
                    const s = d.seasons[sIdx];
                    const sNum = s.index || (sIdx + 1);
                    const sName = s.name || ("Season " + sNum);
                    const rawEps = Array.isArray(s.episodes) ? s.episodes : [];
                    const episodes = [];

                    for (let eIdx = 0; eIdx < rawEps.length; eIdx++) {
                        const ep = rawEps[eIdx];
                        const epNum = ep.number || (eIdx + 1);
                        const epLabel = String(ep.label || (ep.is_vip ? "VIP" : "")).trim();
                        const epIsVip = Boolean(ep.is_vip || (ep.is_free === false) || epLabel.toUpperCase() === "VIP");
                        const epIsExpress = Boolean(ep.is_express || epLabel.toUpperCase() === "FAST TRACK" || epLabel.toUpperCase() === "EXPRESS");
                        const epIsTrailer = Boolean(ep.is_trailer || epLabel.toUpperCase() === "TRAILER");
                        let epTags = Array.isArray(ep.tags) ? ep.tags.slice() : [];
                        if (epLabel && epTags.indexOf(epLabel) === -1) {
                            epTags.unshift(epLabel);
                        }
                        if (epIsVip && epTags.indexOf("VIP") === -1) {
                            epTags.unshift("VIP");
                        }

                        episodes.push({
                            id: String(ep.id || ep.video_id || (contentId + "_" + sNum + "_" + epNum)),
                            title: String(ep.title || ("Episode " + epNum)),
                            number: epNum,
                            cover: String(ep.thumbnail_url || ep.cover || d.cover_url || d.cover || ""),
                            duration_seconds: ep.duration_seconds || 0,
                            is_vip: epIsVip,
                            is_express: epIsExpress,
                            is_trailer: epIsTrailer,
                            label: epLabel,
                            tags: epTags
                        });
                    }

                    totalEpsCount += episodes.length;
                    seasons.push({
                        name: sName,
                        index: sNum,
                        total_episodes: episodes.length,
                        episodes: episodes
                    });
                }
            } else if (Array.isArray(d.episodes) && d.episodes.length > 0) {
                const episodes = [];
                for (let eIdx = 0; eIdx < d.episodes.length; eIdx++) {
                    const ep = d.episodes[eIdx];
                    const epNum = ep.number || (eIdx + 1);
                    const epLabel = String(ep.label || (ep.is_vip ? "VIP" : "")).trim();
                    const epIsVip = Boolean(ep.is_vip || (ep.is_free === false) || epLabel.toUpperCase() === "VIP");
                    const epIsExpress = Boolean(ep.is_express || epLabel.toUpperCase() === "FAST TRACK" || epLabel.toUpperCase() === "EXPRESS");
                    const epIsTrailer = Boolean(ep.is_trailer || epLabel.toUpperCase() === "TRAILER");
                    let epTags = Array.isArray(ep.tags) ? ep.tags.slice() : [];
                    if (epLabel && epTags.indexOf(epLabel) === -1) {
                        epTags.unshift(epLabel);
                    }
                    if (epIsVip && epTags.indexOf("VIP") === -1) {
                        epTags.unshift("VIP");
                    }

                    episodes.push({
                        id: String(ep.id || ep.video_id || (contentId + "_" + epNum)),
                        title: String(ep.title || ("Episode " + epNum)),
                        number: epNum,
                        cover: String(ep.thumbnail_url || ep.cover || d.cover_url || d.cover || ""),
                        duration_seconds: ep.duration_seconds || 0,
                        is_vip: epIsVip,
                        is_express: epIsExpress,
                        is_trailer: epIsTrailer,
                        label: epLabel,
                        tags: epTags
                    });
                }
                totalEpsCount = episodes.length;
                seasons.push({
                    name: "Season 1",
                    index: 1,
                    total_episodes: episodes.length,
                    episodes: episodes
                });
            } else {
                totalEpsCount = 1;
                seasons.push({
                    name: "Season 1",
                    index: 1,
                    total_episodes: 1,
                    episodes: [{
                        id: String(d.id || contentId),
                        title: "Full Movie",
                        number: 1,
                        cover: sanitizeCoverUrl(String(d.cover_url || d.cover || "")),
                        duration_seconds: d.duration || 0,
                        is_vip: false,
                        is_express: false,
                        is_trailer: false,
                        label: "",
                        tags: []
                    }]
                });
            }

            let tags = [];
            if (Array.isArray(d.genres)) tags = tags.concat(d.genres);
            if (Array.isArray(d.tag)) tags = tags.concat(d.tag);

            const isVip = tags.indexOf("VIP") !== -1 || (d.description && d.description.indexOf("VIP") !== -1);
            if (isVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

            const sv = parseScoreAndViews(d.hot_score || d.rating, d.views || d.view_count);

            detail = {
                id: String(d.id || contentId),
                title: String(d.title || ""),
                cover: sanitizeCoverUrl(String(d.cover_url || d.cover || "")),
                description: String(d.description || ""),
                type: String(d.type || d.content_type || "drama"),
                source: String(d.source || canonicalId),
                release_date: String(d.release_date || d.year || ""),
                score: sv.score,
                views: sv.views,
                is_vip: isVip,
                tags: tags,
                total_episodes: totalEpsCount,
                seasons: seasons,
                cast: []
            };
        }

        if (!detail) {
            return jsonError(404, "Data detail tidak ditemukan");
        }

        // 3. Format JSON secara manual agar urutan parameter 100% konsisten dan deterministik
        const seasonStrings = detail.seasons.map(s => {
            const epStrings = s.episodes.map(ep => {
                return "{" +
                    '"id":' + JSON.stringify(ep.id) + "," +
                    '"title":' + JSON.stringify(ep.title) + "," +
                    '"number":' + ep.number + "," +
                    '"cover":' + JSON.stringify(ep.cover || "") + "," +
                    '"duration_seconds":' + ep.duration_seconds + "," +
                    '"is_vip":' + (ep.is_vip ? "true" : "false") + "," +
                    '"is_express":' + (ep.is_express ? "true" : "false") + "," +
                    '"is_trailer":' + (ep.is_trailer ? "true" : "false") + "," +
                    '"label":' + JSON.stringify(ep.label || "") + "," +
                    '"tags":' + JSON.stringify(ep.tags || []) +
                "}";
            });

            return "{" +
                '"name":' + JSON.stringify(s.name) + "," +
                '"index":' + s.index + "," +
                '"total_episodes":' + s.total_episodes + "," +
                '"episodes":[' + epStrings.join(",") + "]" +
            "}";
        });

        const dubStrings = (detail.dubs || []).map(dub => {
            return "{" +
                '"id":' + JSON.stringify(dub.id) + "," +
                '"title":' + JSON.stringify(dub.title) + "," +
                '"lan_code":' + JSON.stringify(dub.lan_code || "") + "," +
                '"is_original":' + (dub.is_original ? "true" : "false") +
            "}";
        });

        const castStrings = (detail.cast || []).map(c => {
            return "{" +
                '"id":' + JSON.stringify(c.id || "") + "," +
                '"name":' + JSON.stringify(c.name || "") + "," +
                '"role":' + JSON.stringify(c.role || "") + "," +
                '"cover":' + JSON.stringify(c.cover || "") + "," +
                '"is_director":' + (c.is_director ? "true" : "false") +
            "}";
        });

        const jsonStr = "{" +
            '"code":200,' +
            '"message":"success",' +
            '"data":{' +
                '"id":' + JSON.stringify(detail.id) + "," +
                '"title":' + JSON.stringify(detail.title) + "," +
                '"cover":' + JSON.stringify(sanitizeCoverUrl(detail.cover)) + "," +
                '"description":' + JSON.stringify(detail.description || "") + "," +
                '"type":' + JSON.stringify(detail.type || "drama") + "," +
                '"source":' + JSON.stringify(detail.source) + "," +
                '"release_date":' + JSON.stringify(detail.release_date || "") + "," +
                '"score":' + JSON.stringify(detail.score || "0") + "," +
                '"views":' + JSON.stringify(detail.views || "") + "," +
                '"is_vip":' + (detail.is_vip ? "true" : "false") + "," +
                '"tags":' + JSON.stringify(detail.tags || []) + "," +
                '"total_episodes":' + detail.total_episodes + "," +
                '"seasons":[' + seasonStrings.join(",") + "]," +
                '"dubs":[' + dubStrings.join(",") + "]," +
                '"cast":[' + castStrings.join(",") + "]" +
            "}" +
        "}";

        return e.blob(200, "application/json", jsonStr);

    } catch (err) {
        return jsonError(500, "Gateway error: " + err);
    }
});
