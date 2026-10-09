// pb_hooks/search.pb.js
// Dramix Gateway - Unified Search Router & Adapter for /api/modelles/search

const handleSearch = (e) => {
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
            
            // Extract real URL from serveproxy.com wrapper using manual parsing
            if (trimmed.includes("serveproxy.com") && trimmed.includes("?url=")) {
                const urlParamIndex = trimmed.indexOf("?url=");
                if (urlParamIndex !== -1) {
                    const extractedUrl = trimmed.substring(urlParamIndex + 5); // skip "?url="
                    // Check if extracted URL is valid (starts with http)
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

        // 1. Strict validation of query parameters & body keys
        const queryKeys = Object.keys(info.query || {});
        const allowedKeys = ["model_id", "q", "page", "content_type"];
        for (let i = 0; i < queryKeys.length; i++) {
            if (allowedKeys.indexOf(queryKeys[i]) === -1) {
                return jsonError(400, "Invalid or missing request parameters");
            }
        }

        if (info.body && typeof info.body === "object") {
            const bodyKeys = Object.keys(info.body);
            for (let i = 0; i < bodyKeys.length; i++) {
                if (allowedKeys.indexOf(bodyKeys[i]) === -1) {
                    return jsonError(400, "Invalid or missing request parameters");
                }
            }
        }

        let modelId = (info.query && info.query.model_id ? String(info.query.model_id) : "").trim();
        let q = (info.query && info.query.q ? String(info.query.q) : "").trim();
        let pageRaw = (info.query && info.query.page ? String(info.query.page) : "1").trim();
        let contentType = (info.query && info.query.content_type ? String(info.query.content_type) : "").trim();

        // Support JSON request body for POST
        if (info.body) {
            const b = info.body;
            if (!modelId && b.model_id) modelId = String(b.model_id).trim();
            if (!q && b.q) q = String(b.q).trim();
            if (pageRaw === "1" && b.page) pageRaw = String(b.page).trim();
            if (!contentType && b.content_type) contentType = String(b.content_type).trim();
        }

        if (!modelId || !q) {
            return jsonError(400, "Invalid or missing request parameters");
        }

        let pageNum = parseInt(pageRaw, 10);
        if (isNaN(pageNum) || pageNum < 1) {
            pageNum = 1;
        }

        // 2. Validate Provider against PocketBase providers table
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
        const providerContentType = target.get("content_type") || "movie_tv";
        const effectiveContentType = contentType || (providerContentType === "short_drama" ? "short_drama" : "movie_tv");

        let rawItems = [];
        let hasMore = false;

        // 1. KissKH (Port 7403)
        if (normalizedId === "kisskh") {
            const res = $http.send({
                url: "http://127.0.0.1:7403/api/DramaList/Search?q=" + encodeURIComponent(q),
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari drama dari KissKH service");
            }
            const list = Array.isArray(res.json) ? res.json : ((res.json && Array.isArray(res.json.data)) ? res.json.data : []);
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                if (it && it.id) {
                    const epCount = it.episodesCount ? (it.episodesCount + " EP") : "";
                    const tags = [];
                    if (it.label && String(it.label).trim()) tags.push(String(it.label).trim());
                    rawItems.push({
                        id: String(it.id),
                        title: String(it.title || ""),
                        cover: sanitizeCoverUrl(it.thumbnail),
                        type: "drama",
                        source: "KissKH",
                        episode_info: epCount,
                        score: "0",
                        views: "",
                        is_vip: false,
                        tags: tags
                    });
                }
            }
        }
        // 2. WeTV (Port 7402)
        else if (normalizedId === "wetv") {
            const res = $http.send({
                url: "http://127.0.0.1:7402/api/wetv/search?query=" + encodeURIComponent(q) + "&page_no=" + pageNum,
                method: "GET",
                timeout: 12
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari drama dari WeTV service");
            }
            const d = res.json || {};
            const list = Array.isArray(d.data) ? d.data : (Array.isArray(d.result) ? d.result : []);
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                const itemId = it.cid || it.id;
                if (itemId) {
                    const sv = parseScoreAndViews(it.score, "");
                    rawItems.push({
                        id: String(itemId),
                        title: String(it.title || ""),
                        cover: sanitizeCoverUrl(it.cover_v || it.cover || it.cover_h),
                        type: "drama",
                        source: "WeTV",
                        episode_info: String(it.episode_info || ""),
                        score: sv.score,
                        views: sv.views,
                        is_vip: Boolean(it.is_vip),
                        tags: Array.isArray(it.tags) ? it.tags : []
                    });
                }
            }
            // WeTV: calculate has_more from total_results
            const totalResults = d.total_results || 0;
            const pageSize = 10;
            hasMore = (pageNum * pageSize) < totalResults;
        }
        // 3. MovieBox (Port 7404)
        else if (normalizedId === "moviebox") {
            const res = $http.send({
                url: "http://127.0.0.1:7404/search?keyword=" + encodeURIComponent(q) + "&page=" + pageNum + "&perPage=20",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari film dari MovieBox service");
            }
            const list = (res.json && Array.isArray(res.json.data)) ? res.json.data : [];
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                const itemId = it.detail_path || it.subject_id;
                if (itemId) {
                    const itemType = (it.subject_type === 1) ? "movie" : "drama";
                    const sv = parseScoreAndViews(it.imdb_rating, "");
                    rawItems.push({
                        id: String(itemId),
                        title: String(it.title || ""),
                        cover: sanitizeCoverUrl(it.cover),
                        type: itemType,
                        source: "MovieBox",
                        episode_info: String(it.release_date || ""),
                        score: sv.score,
                        views: sv.views,
                        is_vip: false,
                        tags: Array.isArray(it.genre) ? it.genre : []
                    });
                }
            }
            // MovieBox: consume pager.has_more
            if (res.json && res.json.pager && typeof res.json.pager.has_more === "boolean") {
                hasMore = res.json.pager.has_more;
            }
        }
        // 4. Viu (Port 7405)
        else if (normalizedId === "viu") {
            const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
            const res = $http.send({
                url: "http://127.0.0.1:7405/api/drama-api/search?q=" + encodeURIComponent(q) + "&page=" + pageNum + "&api_key=" + apiKey,
                headers: {
                    "Authorization": "Bearer " + apiKey
                },
                method: "GET",
                timeout: 12
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari drama dari Viu service");
            }
            const list = (res.json && Array.isArray(res.json.data)) ? res.json.data : [];
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                const itemId = it.series_id || it.id;
                if (itemId) {
                    const tags = [];
                    if (it.category) tags.push(it.category);
                    const epTotal = it.total_episodes || it.latest_episode;
                    const epInfo = epTotal ? ("Total " + epTotal + " EP") : "";
                    rawItems.push({
                        id: String(itemId),
                        title: String(it.title || ""),
                        cover: sanitizeCoverUrl(it.cover_portrait || it.cover),
                        type: "drama",
                        source: "Viu",
                        episode_info: epInfo,
                        score: "0",
                        views: "",
                        is_vip: false,
                        tags: tags
                    });
                }
            }
            // VIU: heuristic - if items returned, assume has_more (VIU doesn't expose pagination)
            hasMore = list.length > 0;
        }
        // 5. FreeReels (Port 7406)
        else if (normalizedId === "freereels") {
            const res = $http.send({
                url: "http://127.0.0.1:7406/search/drama?keyword=" + encodeURIComponent(q) + "&page=" + pageNum,
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari drama dari FreeReels service");
            }
            const d = (res.json && res.json.data) || {};
            const list = Array.isArray(d.items) ? d.items : (Array.isArray(d) ? d : []);
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                const itemId = it.id || it.drama_id || it.key;
                if (itemId) {
                    let epCount = "";
                    if (it.episode_count || it.total_episode) {
                        epCount = String(it.episode_count || it.total_episode) + " EP";
                    }
                    const sv = parseScoreAndViews("0", it.play_count || it.like_count);
                    rawItems.push({
                        id: String(itemId),
                        title: String(it.name || it.title || ""),
                        cover: sanitizeCoverUrl(it.cover || it.vertical_cover),
                        type: "short_drama",
                        source: "FreeReels",
                        episode_info: epCount,
                        score: sv.score,
                        views: sv.views,
                        is_vip: Boolean(it.is_vip),
                        tags: Array.isArray(it.tags) ? it.tags : []
                    });
                }
            }
            // FreeReels: consume page_info.has_more
            if (res.json && res.json.data && res.json.data.page_info && typeof res.json.data.page_info.has_more === "boolean") {
                hasMore = res.json.data.page_info.has_more;
            }
        }
        // 6. iQIYI (Port 7407)
        else if (normalizedId === "iqiyi") {
            const res = $http.send({
                url: "http://127.0.0.1:7407/api/search",
                method: "POST",
                headers: { "content-type": "application/json" },
                body: JSON.stringify({ keyword: q, pg_num: pageNum }),
                timeout: 12
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mencari drama dari iQIYI service");
            }
            const d = (res.json && res.json.data) || {};
            const list = Array.isArray(d.items) ? d.items : [];
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                if (it && it.id) {
                    const isVip = Boolean(it.vip_status || it.is_vip);
                    let tags = Array.isArray(it.tags) ? it.tags.slice() : [];
                    if (it.genre && tags.indexOf(it.genre) === -1) tags.push(it.genre);
                    if (isVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

                    const epCount = it.total_episodes ? ("Total " + it.total_episodes + " EP") : (it.year ? String(it.year) : "");
                    const sv = parseScoreAndViews(it.score || it.rating, it.score_votes ? String(it.score_votes) : "");

                    rawItems.push({
                        id: String(it.id),
                        title: String(it.name || it.title || ""),
                        cover: sanitizeCoverUrl(it.cover || it.banner),
                        type: "drama",
                        source: "iQIYI",
                        episode_info: epCount,
                        score: sv.score,
                        views: sv.views,
                        is_vip: isVip,
                        tags: tags
                    });
                }
            }
            // iQIYI: consume data.has_more
            if (res.json && res.json.data && typeof res.json.data.has_more === "boolean") {
                hasMore = res.json.data.has_more;
            }
        }
        // 7. CineTv (Live TV Channel Filter)
        else if (normalizedId === "cinetv") {
            const categories = ["ID", "SP", "C3", "C4", "C1", "C2", "C5", "C6", "US", "GB"];
            const lowerQ = q.toLowerCase();
            for (let cIdx = 0; cIdx < categories.length; cIdx++) {
                const cat = categories[cIdx];
                const res = $http.send({
                    url: "http://127.0.0.1:7401/api/modelles/videos?model_id=CineTv&category_id=" + encodeURIComponent(cat) + "&page=1",
                    method: "GET",
                    timeout: 8
                });
                if (res.statusCode === 200 && res.json) {
                    const d = res.json.data || {};
                    const list = Array.isArray(d.items) ? d.items : (Array.isArray(d) ? d : []);
                    for (let i = 0; i < list.length; i++) {
                        const it = list[i];
                        const t = String(it.title || "");
                        if (t.toLowerCase().indexOf(lowerQ) !== -1 || lowerQ === "tv" || lowerQ === "live" || lowerQ === "channel") {
                            rawItems.push({
                                id: String(it.id),
                                title: t,
                                cover: String(it.cover || it.poster || ""),
                                type: "live_tv",
                                source: "CineTv",
                                episode_info: "1 EP",
                                score: "LIVE",
                                views: "",
                                is_vip: Boolean(it.is_vip),
                                tags: Array.isArray(it.tags) ? it.tags : [cat]
                            });
                        }
                    }
                }
                if (rawItems.length >= 20) break;
            }
            // CineTv: no pagination support (category search only)
            hasMore = false;
        }
        // 8. CineFlow Hub Upstream (Port 7401 - 17 Provider)
        else {
            const reqBody = {
                model_id: canonicalId,
                content_type: effectiveContentType,
                page: pageNum,
                q: q
            };

            const res = $http.send({
                url: "http://127.0.0.1:7401/api/modelles/search",
                method: "POST",
                headers: { "content-type": "application/json" },
                body: JSON.stringify(reqBody),
                timeout: 15
            });

            if (res.statusCode === 200 && res.json) {
                const d = res.json.data || {};
                const list = Array.isArray(d.items) ? d.items : (Array.isArray(d) ? d : []);
                for (let i = 0; i < list.length; i++) {
                    const it = list[i];
                    const itemId = it.detailPath || it.id || it.key;
                    if (itemId) {
                        let tags = [];
                        if (Array.isArray(it.tag)) tags = tags.concat(it.tag);
                        if (Array.isArray(it.tags)) tags = tags.concat(it.tags);
                        const isVip = Boolean(it.is_vip || it.is_pay);
                        if (isVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

                        const epCount = it.episode_count ? (it.episode_count + " EP") : (it.year || "");
                        const sv = parseScoreAndViews(it.hot_score || it.score || it.rating, it.follow_count || it.views || it.view_count);

                        rawItems.push({
                            id: String(itemId),
                            title: String(it.title || it.name || ""),
                            cover: sanitizeCoverUrl(it.cover || it.poster),
                            type: String(it.type || effectiveContentType || "drama"),
                            source: String(it.source || canonicalId),
                            episode_info: epCount,
                            score: sv.score,
                            views: sv.views,
                            is_vip: isVip,
                            tags: tags
                        });
                    }
                }
            }

            // CineFlow: consume upstream has_more if available, else default false
            if (res.statusCode === 200 && res.json && res.json.data && typeof res.json.data.has_more === "boolean") {
                hasMore = res.json.data.has_more;
            } else {
                hasMore = false;
            }

            // Fallback jika upstream search mengembalikan 0 hasil: query categories/videos
            if (rawItems.length === 0) {
                const lowerQ = q.toLowerCase();
                const catRes = $http.send({
                    url: "http://127.0.0.1:7401/api/modelles/categories?model_id=" + encodeURIComponent(canonicalId),
                    method: "GET",
                    timeout: 8
                });
                if (catRes.statusCode === 200 && catRes.json) {
                    const cats = (catRes.json.data && Array.isArray(catRes.json.data.data)) ? catRes.json.data.data : [];
                    for (let cIdx = 0; cIdx < Math.min(cats.length, 3); cIdx++) {
                        const catId = cats[cIdx].id;
                        if (!catId) continue;
                        const vRes = $http.send({
                            url: "http://127.0.0.1:7401/api/modelles/videos?model_id=" + encodeURIComponent(canonicalId) + "&category_id=" + encodeURIComponent(catId) + "&page=1",
                            method: "GET",
                            timeout: 8
                        });
                        if (vRes.statusCode === 200 && vRes.json) {
                            const vd = vRes.json.data || {};
                            const vList = Array.isArray(vd.items) ? vd.items : (Array.isArray(vd) ? vd : []);
                            for (let i = 0; i < vList.length; i++) {
                                const it = vList[i];
                                const t = String(it.title || it.name || "");
                                if (t.toLowerCase().indexOf(lowerQ) !== -1) {
                                    const itemId = it.detailPath || it.id || it.key;
                                    const sv = parseScoreAndViews(it.hot_score || it.score, it.views);
                                    rawItems.push({
                                        id: String(itemId),
                                        title: t,
                                        cover: String(it.cover || it.poster || ""),
                                        type: String(it.type || effectiveContentType || "drama"),
                                        source: String(it.source || canonicalId),
                                        episode_info: String(it.episode_count ? it.episode_count + " EP" : ""),
                                        score: sv.score,
                                        views: sv.views,
                                        is_vip: Boolean(it.is_vip),
                                        tags: Array.isArray(it.tags) ? it.tags : []
                                    });
                                }
                            }
                        }
                        if (rawItems.length > 0) break;
                    }
                }
            }
        }

        // De-duplikasi item berdasarkan ID
        const seenIds = {};
        const items = [];
        for (let i = 0; i < rawItems.length; i++) {
            const item = rawItems[i];
            if (item.id && !seenIds[item.id]) {
                seenIds[item.id] = true;
                items.push(item);
            }
        }

        // Format JSON secara deterministik (id -> title -> cover -> type -> source -> episode_info -> score -> views -> is_vip -> tags)
        const itemStrings = items.map(it => {
            return "{" +
                '"id":' + JSON.stringify(it.id) + "," +
                '"title":' + JSON.stringify(it.title) + "," +
                '"cover":' + JSON.stringify(it.cover) + "," +
                '"type":' + JSON.stringify(it.type) + "," +
                '"source":' + JSON.stringify(it.source) + "," +
                '"episode_info":' + JSON.stringify(it.episode_info || "") + "," +
                '"score":' + JSON.stringify(it.score || "0") + "," +
                '"views":' + JSON.stringify(it.views || "") + "," +
                '"is_vip":' + (it.is_vip ? "true" : "false") + "," +
                '"tags":' + JSON.stringify(it.tags || []) +
            "}";
        });

        const jsonStr = "{" +
            '"code":200,' +
            '"message":"success",' +
            '"data":{' +
                '"model_id":' + JSON.stringify(canonicalId) + "," +
                '"q":' + JSON.stringify(q) + "," +
                '"page":' + pageNum + "," +
                '"has_more":' + (hasMore ? "true" : "false") + "," +
                '"items":[' + itemStrings.join(",") + "]" +
            "}" +
        "}";

        return e.blob(200, "application/json", jsonStr);

    } catch (err) {
        return jsonError(500, "Gateway error: " + err);
    }
};

routerAdd("GET", "/api/modelles/search", handleSearch);
routerAdd("POST", "/api/modelles/search", handleSearch);
