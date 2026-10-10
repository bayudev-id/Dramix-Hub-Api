// pb_hooks/videos.pb.js
// Dramix Gateway - Unified Videos/Drama List Router & Adapter for /api/modelles/videos

routerAdd("GET", "/api/modelles/videos", (e) => {
    try {
        const jsonError = function(statusCode, message) {
            const errStr = "{" +
                '"code":' + statusCode + "," +
                '"message":' + JSON.stringify(message) + "," +
                '"data":null' +
            "}";
            return e.blob(statusCode, "application/json", errStr);
        };

        const optimizeCoverUrl = function(url, providerSource) {
            if (!url || typeof url !== "string") return url;
            
            // Extract from serveproxy wrapper
            if (url.includes("serveproxy.com") && url.includes("?url=")) {
                const urlParamIndex = url.indexOf("?url=");
                if (urlParamIndex !== -1) {
                    const extractedUrl = url.substring(urlParamIndex + 5);
                    if (extractedUrl.startsWith("http://") || extractedUrl.startsWith("https://")) {
                        url = extractedUrl;
                    }
                }
            }
            
            // Convert HTTP → HTTPS for known CDNs
            if (url.startsWith("http://pic") && url.includes("iqiyipic.com")) {
                url = url.replace("http://", "https://");
            }
            if (url.startsWith("http://m.ykimg.com")) {
                url = url.replace("http://", "https://");
            }
            
            const source = (providerSource || "").toLowerCase();
            
            // MovieBox: Alibaba Cloud OSS CDN - resize to 240px width + WebP format on edge (~10-15KB)
            if (source === "moviebox" || url.indexOf("pbcdnw.aoneroom.com") !== -1) {
                const cleanUrl = url.split("?")[0];
                return cleanUrl + "?x-oss-process=image/resize,w_240,m_lfit/format,webp";
            }
            
            // KissKH/TMDB: downscale backdrop/poster on TMDB edge (~12-16KB)
            if (source === "kisskh" || url.indexOf("media.themoviedb.org") !== -1 || url.indexOf("image.tmdb.org") !== -1) {
                if (url.indexOf("w1000_and_h563_face") !== -1) {
                    return url.replace("w1000_and_h563_face", "w250_and_h141_face");
                }
                return url.replace(/w_\d+_and_h\d+/, "w300");
            }
            
            // WeTV: Tencent Cloud CDN edge optimizer (imageMogr2) -> strict < 15KB WebP
            if (source === "wetv" || url.indexOf("wetvinfo.com") !== -1) {
                // Format 1: puui.wetvinfo.com (Tencent COS) -> downscale + WebP quality 80 (~6-8KB)
                if (url.indexOf("puui.wetvinfo.com") !== -1) {
                    let u = url.replace(/_\d+(\.\w+)$/, "_218304$1");
                    const sep = (u.indexOf("?") === -1) ? "?" : "&";
                    if (u.indexOf("imageMogr2") === -1) {
                        u = u + sep + "imageMogr2/thumbnail/150x/format/webp/quality/80";
                    }
                    return u;
                }
                // Format 2: vcover-vt-pic -> switch to /92 (static pre-rendered thumbnail on Tencent CDN, ~10KB, instant cache hit)
                if (url.indexOf("vcover-vt-pic") !== -1) {
                    return url.replace(/\/\d+$/, "/92");
                }
            }
            
            // FreeReels: already ~430B
            // Viu: Hash-based CDN
            // iQIYI: Already contains dimension tags in URL
            return url;
        };

        const parseScoreAndViews = function(rawScore, rawViews) {
            let score = "0";
            let views = "";

            if (rawViews !== undefined && rawViews !== null && String(rawViews).trim() !== "" && String(rawViews).trim() !== "0") {
                views = String(rawViews).trim();
            }

            if (rawScore !== undefined && rawScore !== null && String(rawScore).trim() !== "") {
                const s = String(rawScore).trim();
                // If string contains K, M, B (e.g. 16.3M, 20.9K) or numeric count > 50 -> views / popularity count
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

        const info = e.requestInfo();

        // 1. Validasi allowed query parameters (strict, no query parameter leakage)
        const queryKeys = Object.keys(info.query || {});
        const allowedKeys = ["model_id", "category_id", "page"];
        for (let i = 0; i < queryKeys.length; i++) {
            if (allowedKeys.indexOf(queryKeys[i]) === -1) {
                return jsonError(400, "Invalid or missing request parameters");
            }
        }

        const modelId = (info.query.model_id || "").trim();
        const categoryId = (info.query.category_id || "").trim();

        if (!modelId || !categoryId) {
            return jsonError(400, "Invalid or missing request parameters");
        }

        // 2. Parse pagination (default: 1)
        const pageRaw = (info.query.page || "1").trim();
        let pageNum = parseInt(pageRaw, 10);
        if (isNaN(pageNum) || pageNum < 1) {
            pageNum = 1;
        }

        // 3. Validasi Provider terhadap database PocketBase
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

        let rawItems = [];
        let hasMore = true;

        // 1. KissKH (Port 6103)
        if (normalizedId === "kisskh") {
            const kissPath = (categoryId.toLowerCase() === "explore") ? "List" : categoryId;
            const res = $http.send({
                url: "http://127.0.0.1:6103/api/DramaList/" + encodeURIComponent(kissPath) + "?page=" + pageNum,
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil daftar drama dari KissKH service");
            }
            if (res.json && typeof res.json.totalCount === "number" && res.json.totalCount > 0) {
                const total = res.json.totalCount;
                const ps = typeof res.json.pageSize === "number" ? res.json.pageSize : 18;
                hasMore = (pageNum * ps) < total;
                if (!hasMore && pageNum > Math.ceil(total / ps)) {
                    rawItems = [];
                }
            } else {
                hasMore = false;
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.id) {
                    let itemType = "drama";
                    if (categoryId.toLowerCase() === "animate") {
                        itemType = "anime";
                    }
                    const epCount = it.episodesCount ? (it.episodesCount + " EP") : "";
                    const tags = [];
                    if (it.label && String(it.label).trim()) {
                        tags.push(String(it.label).trim());
                    }

                    const sv = parseScoreAndViews("0", "");

                    rawItems.push({
                        id: String(it.id),
                        title: String(it.title || ""),
                        cover: optimizeCoverUrl(String(it.thumbnail || ""), "KissKH"),
                        type: itemType,
                        source: "KissKH",
                        episode_info: epCount,
                        score: sv.score,
                        views: sv.views,
                        is_vip: false,
                        tags: tags
                    });
                }
            }
        }
        // 2. WeTV (Port 6102)
        else if (normalizedId === "wetv") {
            const res = $http.send({
                url: "http://127.0.0.1:6102/api/wetv/channel/" + encodeURIComponent(categoryId) + "?page_no=" + pageNum,
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil daftar drama dari WeTV service");
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const mod = raw[i];
                const modTitle = String(mod.module_title || "");
                if (mod && Array.isArray(mod.items)) {
                    for (let j = 0; j < mod.items.length; j++) {
                        const it = mod.items[j];
                        const itemId = it.id || it.cid;
                        if (itemId) {
                            let itemType = "drama";
                            const tags = Array.isArray(it.tags) ? it.tags.slice() : [];
                            const isMovieTag = tags.indexOf("Film") !== -1 || tags.indexOf("Movie") !== -1;
                            const isMovieMod = modTitle.toLowerCase().indexOf("movie") !== -1 || modTitle.toLowerCase().indexOf("film") !== -1;

                            if (categoryId === "10062" || isMovieTag || isMovieMod) {
                                itemType = "movie";
                            } else if (categoryId === "10473") {
                                itemType = "short_drama";
                            } else if (categoryId === "10022") {
                                itemType = "anime";
                            } else if (categoryId === "10096") {
                                itemType = "variety";
                            }

                            const isVip = Boolean(it.is_vip);
                            if (isVip && tags.indexOf("VIP") === -1) {
                                tags.unshift("VIP");
                            }

                            const sv = parseScoreAndViews(it.score, "");

                            rawItems.push({
                                id: String(itemId),
                                title: String(it.title || it.main_title || ""),
                                cover: optimizeCoverUrl(String(it.cover_v || it.cover_h || it.cover || ""), "WeTV"),
                                type: itemType,
                                source: "WeTV",
                                episode_info: String(it.episode_info || ""),
                                score: sv.score,
                                views: sv.views,
                                is_vip: isVip,
                                tags: tags
                            });
                        }
                    }
                } else if (mod && (mod.id || mod.cid)) {
                    let itemType = "drama";
                    if (categoryId === "10062") itemType = "movie";
                    else if (categoryId === "10473") itemType = "short_drama";
                    else if (categoryId === "10022") itemType = "anime";
                    else if (categoryId === "10096") itemType = "variety";

                    const tags = Array.isArray(mod.tags) ? mod.tags.slice() : [];
                    const isVip = Boolean(mod.is_vip);
                    if (isVip && tags.indexOf("VIP") === -1) {
                        tags.unshift("VIP");
                    }

                    const sv = parseScoreAndViews(mod.score, "");

                    rawItems.push({
                        id: String(mod.id || mod.cid),
                        title: String(mod.title || mod.main_title || ""),
                        cover: optimizeCoverUrl(String(mod.cover_v || mod.cover_h || mod.cover || ""), "WeTV"),
                        type: itemType,
                        source: "WeTV",
                        episode_info: String(mod.episode_info || ""),
                        score: sv.score,
                        views: sv.views,
                        is_vip: isVip,
                        tags: tags
                    });
                }
            }
        }
        // 3. MovieBox (Port 6104)
        else if (normalizedId === "moviebox") {
            const isTrending = (String(categoryId) === "3521493905000087296");
            if (!isTrending && pageNum > 1) {
                // Kategori selain Rekomendasi tidak memiliki pagination; kembalikan kosong jika page > 1
                hasMore = false;
                rawItems = [];
            } else {
                const mbPage = Math.max(0, pageNum - 1);
                const res = $http.send({
                    url: "http://127.0.0.1:6104/content?opId=" + encodeURIComponent(categoryId) + "&page=" + mbPage + "&perPage=18",
                    method: "GET",
                    timeout: 10
                });
                if (res.statusCode !== 200) {
                    return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil konten dari MovieBox service: " + res.statusCode);
                }
                if (isTrending && res.json && res.json.pager && typeof res.json.pager.has_more === "boolean") {
                    hasMore = res.json.pager.has_more;
                } else {
                    hasMore = false;
                }
                const raw = (res.json && res.json.data) || [];
                for (let i = 0; i < raw.length; i++) {
                    const it = raw[i];
                    const itemId = it.detail_path || it.subject_id || it.id;
                    if (itemId) {
                        let itemType = "movie";
                        if (it.subject_type === 2) {
                            itemType = "drama";
                        } else if (it.subject_type === 7) {
                            itemType = "short_drama";
                        } else if (it.subject_type === 1) {
                            itemType = "movie";
                        }

                        const tags = Array.isArray(it.genre) ? it.genre.slice() : [];
                        const isVip = Boolean(it.corner && it.corner.toLowerCase().indexOf("vip") !== -1);
                        if (isVip && tags.indexOf("VIP") === -1) {
                            tags.unshift("VIP");
                        }

                        const sv = parseScoreAndViews(it.imdb_rating, "");

                        rawItems.push({
                            id: String(itemId),
                            title: String(it.title || ""),
                            cover: optimizeCoverUrl(String(it.cover || ""), "MovieBox"),
                            type: itemType,
                            source: "MovieBox",
                            episode_info: "",
                            score: sv.score,
                            views: sv.views,
                            is_vip: isVip,
                            tags: tags
                        });
                    }
                }
            }
        }
        // 4. Viu (Port 6105)
        else if (normalizedId === "viu") {
            const res = $http.send({
                url: "http://127.0.0.1:6105/api/mobile?r=/category/series&category_id=" + encodeURIComponent(categoryId) + "&page=" + pageNum + "&api_key=912ursfh283fjefw8234u320t9uejf2983048290859032jfej",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil daftar drama dari Viu service");
            }
            const seriesList = (res.json && res.json.data && res.json.data.series) || [];
            if (!Array.isArray(seriesList) || seriesList.length === 0 || seriesList.length < 20) {
                hasMore = false;
            }
            for (let i = 0; i < seriesList.length; i++) {
                const it = seriesList[i];
                const itemId = it.series_id || it.product_id || it.id;
                if (itemId) {
                    let itemType = "drama";
                    if (it.is_movie === 1 || it.is_movie === "1" || String(it.content_type || "").toLowerCase() === "movie") {
                        itemType = "movie";
                    }

                    const isVip = Boolean(it.is_free_premium_time === 0 || it.user_level > 1 || it.premium_time > 0);
                    const tags = [];
                    if (it.category_name) tags.push(it.category_name);
                    if (isVip) tags.unshift("VIP");

                    const epTotal = it.product_total || it.released_product_total;
                    const epInfo = epTotal ? ("Total " + epTotal + " EP") : "";
                    const sv = parseScoreAndViews("0", "");

                    rawItems.push({
                        id: String(itemId),
                        title: String(it.name || it.title || ""),
                        cover: optimizeCoverUrl(String(it.cover_portrait_image_url || it.cover_landscape_image_url || it.cover_image_url || ""), "Viu"),
                        type: itemType,
                        source: "Viu",
                        episode_info: epInfo,
                        score: sv.score,
                        views: sv.views,
                        is_vip: isVip,
                        tags: tags
                    });
                }
            }
        }
        // 5. FreeReels (Port 6106)
        else if (normalizedId === "freereels") {
            const res = $http.send({
                url: "http://127.0.0.1:6106/videos?module_key=" + encodeURIComponent(categoryId) + "&page=" + pageNum,
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil video dari FreeReels service");
            }
            if (res.json && typeof res.json.has_more === "boolean") {
                hasMore = res.json.has_more;
            } else if (res.json && res.json.data && res.json.data.page_info && typeof res.json.data.page_info.has_more === "boolean") {
                hasMore = res.json.data.page_info.has_more;
            } else {
                hasMore = false;
            }
            let list = [];
            if (res.json) {
                if (res.json.data && Array.isArray(res.json.data.items)) {
                    list = res.json.data.items;
                } else if (Array.isArray(res.json.items)) {
                    list = res.json.items;
                } else if (Array.isArray(res.json.data)) {
                    list = res.json.data;
                }
            }
            for (let i = 0; i < list.length; i++) {
                const it = list[i];
                const itemId = it.key || it.id || it.drama_id;
                if (itemId) {
                    const isVip = Boolean(it.vip_type !== 0 || it.free === false);
                    let tags = [];
                    if (Array.isArray(it.tag)) tags = tags.concat(it.tag);
                    if (Array.isArray(it.content_tags)) tags = tags.concat(it.content_tags);
                    if (isVip && tags.indexOf("VIP") === -1) {
                        tags.unshift("VIP");
                    }

                    // De-duplicate tags
                    const uniqueTags = [];
                    for (let t = 0; t < tags.length; t++) {
                        if (uniqueTags.indexOf(tags[t]) === -1) uniqueTags.push(tags[t]);
                    }

                    const epCount = it.episode_count ? ("Total " + it.episode_count + " EP") : "";
                    let followFormatted = "";
                    if (it.follow_count && it.follow_count > 0) {
                        if (it.follow_count >= 1000000) {
                            followFormatted = (Math.round(it.follow_count / 100000) / 10) + "M";
                        } else if (it.follow_count >= 1000) {
                            followFormatted = (Math.round(it.follow_count / 100) / 10) + "K";
                        } else {
                            followFormatted = String(it.follow_count);
                        }
                    }
                    const sv = parseScoreAndViews(it.hot_score, followFormatted);

                    rawItems.push({
                        id: String(itemId),
                        title: String(it.title || it.name || ""),
                        cover: optimizeCoverUrl(String(it.cover || it.cover_url || ""), "FreeReels"),
                        type: "short_drama",
                        source: "FreeReels",
                        episode_info: epCount,
                        score: sv.score,
                        views: sv.views,
                        is_vip: isVip,
                        tags: uniqueTags
                    });
                }
            }
        }
        // 6. iQIYI (Port 6107)
        else if (normalizedId === "iqiyi") {
            const lowerCat = categoryId.toLowerCase();
            let res = null;

            if (lowerCat === "feed" || lowerCat === "home") {
                if (pageNum > 1) {
                    hasMore = false;
                    rawItems = [];
                } else {
                    res = $http.send({
                        url: "http://127.0.0.1:6107/api/feed",
                        method: "GET",
                        timeout: 10
                    });
                    hasMore = false;
                }
            } else {
                let kw = categoryId;
                if (categoryId === "2") kw = "drama";
                else if (categoryId === "4") kw = "anime";
                else if (categoryId === "6") kw = "variety";
                else if (categoryId === "1") kw = "movie";

                res = $http.send({
                    url: "http://127.0.0.1:6107/api/search",
                    method: "POST",
                    headers: { "content-type": "application/json" },
                    body: JSON.stringify({ keyword: kw, pg_num: pageNum }),
                    timeout: 10
                });
            }

            if (res) {
                if (res.statusCode !== 200) {
                    return jsonError(res.statusCode === 404 ? 404 : 502, "Gagal mengambil drama dari iQIYI service");
                }

                const rawList = (res.json && res.json.data && res.json.data.items) ||
                                (res.json && Array.isArray(res.json.data) ? res.json.data : []);
                if (rawList.length < 25) {
                    hasMore = false;
                }
                for (let i = 0; i < rawList.length; i++) {
                    const it = rawList[i];
                    if (it && it.id) {
                        let itemType = "drama";
                        if (categoryId === "1") itemType = "movie";
                        else if (categoryId === "4") itemType = "anime";
                        else if (categoryId === "6") itemType = "variety";

                        const isVip = Boolean(it.vip_status || it.is_vip);
                        let tags = Array.isArray(it.tags) ? it.tags.slice() : [];
                        if (it.genre && tags.indexOf(it.genre) === -1) tags.push(it.genre);
                        if (it.badge && tags.indexOf(it.badge) === -1) tags.push(it.badge);
                        if (isVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

                        const epCount = it.total_episodes ? ("Total " + it.total_episodes + " EP") : "";
                        const sv = parseScoreAndViews(it.score || it.rating, it.score_votes ? String(it.score_votes) : "");

                        rawItems.push({
                            id: String(it.id),
                            title: String(it.name || it.title || ""),
                            cover: optimizeCoverUrl(String(it.cover || it.banner || ""), "iQIYI"),
                            type: itemType,
                            source: "iQIYI",
                            episode_info: epCount,
                            score: sv.score,
                            views: sv.views,
                            is_vip: isVip,
                            tags: tags
                        });
                    }
                }
            }
        }
        // 7. CineFlow Hub Upstream (Port 6101)
        else {
            const cfRes = $http.send({
                url: "http://127.0.0.1:6101/api/modelles/videos?model_id=" + encodeURIComponent(canonicalId) + "&category_id=" + encodeURIComponent(categoryId) + "&page=" + pageNum,
                method: "GET",
                timeout: 15
            });
            if (cfRes.statusCode !== 200) {
                return jsonError(cfRes.statusCode, "Gagal mengambil video dari upstream CineFlow");
            }
            if (cfRes.json && cfRes.json.data && typeof cfRes.json.data.has_more === "boolean") {
                hasMore = cfRes.json.data.has_more;
            } else if (cfRes.json && typeof cfRes.json.has_more === "boolean") {
                hasMore = cfRes.json.has_more;
            } else {
                hasMore = false;
            }
            const raw = (cfRes.json && cfRes.json.data && cfRes.json.data.items) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.id) {
                    const ep = it.total_episodes || it.episode_count;
                    const epInfo = ep ? (ep + " EP") : (it.desc && it.desc.indexOf("Ep") !== -1 ? String(it.desc).trim() : "");
                    let tags = [];
                    if (Array.isArray(it.tag)) tags = it.tag.slice();
                    else if (Array.isArray(it.tags)) tags = it.tags.slice();

                    const isVip = tags.indexOf("VIP") !== -1 || (it.desc && it.desc.indexOf("VIP") !== -1);
                    if (isVip && tags.indexOf("VIP") === -1) tags.unshift("VIP");

                    const sv = parseScoreAndViews(it.hot_score, it.views || it.view_count);

                    rawItems.push({
                        id: String(it.id),
                        title: String(it.title || ""),
                        cover: optimizeCoverUrl(String(it.cover || ""), String(it.source || canonicalId)),
                        type: String(it.type || "drama"),
                        source: String(it.source || canonicalId),
                        episode_info: epInfo,
                        score: sv.score,
                        views: sv.views,
                        is_vip: isVip,
                        tags: tags
                    });
                }
            }
        }

        // De-duplikasi item berdasarkan id
        const seenIds = {};
        const items = [];
        for (let i = 0; i < rawItems.length; i++) {
            const item = rawItems[i];
            if (!seenIds[item.id]) {
                seenIds[item.id] = true;
                items.push(item);
            }
        }

        // Format JSON secara manual agar urutan parameter/field 100% konsisten dan tidak diacak oleh Go map serializer
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

        if (items.length === 0) {
            hasMore = false;
        }

        const jsonStr = "{" +
            '"code":200,' +
            '"message":"success",' +
            '"data":{' +
                '"model_id":' + JSON.stringify(canonicalId) + "," +
                '"category_id":' + JSON.stringify(categoryId) + "," +
                '"page":' + pageNum + "," +
                '"has_more":' + (hasMore ? "true" : "false") + "," +
                '"items":[' + itemStrings.join(",") + "]" +
            "}" +
        "}";

        return e.blob(200, "application/json", jsonStr);

    } catch (err) {
        return jsonError(500, "Gateway error: " + err);
    }
});
