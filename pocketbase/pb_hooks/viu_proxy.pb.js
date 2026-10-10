// pb_hooks/viu_proxy.pb.js
// Dramix Gateway - Secure VIU HLS Manifest & AES-128 DRM Key Proxy
// Keeps viu_api bound to 127.0.0.1 (localhost only) while serving streaming via Gateway (:8090)

routerAdd("GET", "/api/modelles/viu/vuclip_vod.m3u8", (e) => {
    try {
        const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
        const rawQ = (e.request && e.request.url && e.request.url.rawQuery) || "";
        const sep = rawQ ? "&" : "";
        const targetUrl = "http://127.0.0.1:7405/vod/vuclip_vod.m3u8" + (rawQ ? "?" + rawQ : "") + sep + "api_key=" + apiKey;

        const info = e.requestInfo();
        const clientUa = (info.headers && (info.headers["user-agent"] || info.headers["User-Agent"])) || "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36";

        const res = $http.send({
            url: targetUrl,
            method: "GET",
            headers: {
                "User-Agent": clientUa,
                "Authorization": "Bearer " + apiKey
            },
            timeout: 15
        });

        if (res.statusCode !== 200) {
            return e.json(res.statusCode, { error: "Upstream error", code: res.statusCode });
        }

        const host = (e.request && e.request.host) || (info.headers && (info.headers["host"] || info.headers["Host"])) || "127.0.0.1:8090";
        let content = String(res.raw || "");

        // Rewrite DRM key endpoint so ExoPlayer fetches AES key via Gateway (:8090)
        content = content.replace(/http:\/\/127\.0\.0\.1:7405\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");
        content = content.replace(/https:\/\/prod-in\.viu\.com\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");
        content = content.replace(/http:\/\/192\.168\.18\.200:7405\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");

        return e.blob(200, "application/vnd.apple.mpegurl", content);
    } catch (err) {
        return e.json(500, { error: String(err) });
    }
});

routerAdd("GET", "/api/modelles/viu/vuclip_airplay.m3u8", (e) => {
    try {
        const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
        const rawQ = (e.request && e.request.url && e.request.url.rawQuery) || "";
        const sep = rawQ ? "&" : "";
        const targetUrl = "http://127.0.0.1:7405/vod/vuclip_airplay.m3u8" + (rawQ ? "?" + rawQ : "") + sep + "api_key=" + apiKey;

        const info = e.requestInfo();
        const clientUa = (info.headers && (info.headers["user-agent"] || info.headers["User-Agent"])) || "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36";

        const res = $http.send({
            url: targetUrl,
            method: "GET",
            headers: {
                "User-Agent": clientUa,
                "Authorization": "Bearer " + apiKey
            },
            timeout: 15
        });

        if (res.statusCode !== 200) {
            return e.json(res.statusCode, { error: "Upstream error", code: res.statusCode });
        }

        const host = (e.request && e.request.host) || (info.headers && (info.headers["host"] || info.headers["Host"])) || "127.0.0.1:8090";
        let content = String(res.raw || "");

        // Rewrite DRM key endpoint so ExoPlayer fetches AES key via Gateway (:8090)
        content = content.replace(/http:\/\/127\.0\.0\.1:7405\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");
        content = content.replace(/https:\/\/prod-in\.viu\.com\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");
        content = content.replace(/http:\/\/192\.168\.18\.200:7405\/api\/appsdrm\/getkey/g, "http://" + host + "/api/modelles/viu/getkey");

        return e.blob(200, "application/vnd.apple.mpegurl", content);
    } catch (err) {
        return e.json(500, { error: String(err) });
    }
});

routerAdd("GET", "/api/modelles/viu/getkey", (e) => {
    try {
        const apiKey = "912ursfh283fjefw8234u320t9uejf2983048290859032jfej";
        const rawQ = (e.request && e.request.url && e.request.url.rawQuery) || "";
        const sep = rawQ ? "&" : "";
        const targetUrl = "http://127.0.0.1:7405/api/appsdrm/getkey" + (rawQ ? "?" + rawQ : "") + sep + "api_key=" + apiKey;

        const info = e.requestInfo();
        const clientUa = (info.headers && (info.headers["user-agent"] || info.headers["User-Agent"])) || "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36";

        const res = $http.send({
            url: targetUrl,
            method: "GET",
            headers: {
                "User-Agent": clientUa,
                "Authorization": "Bearer " + apiKey
            },
            timeout: 15
        });

        if (res.statusCode !== 200) {
            return e.json(res.statusCode, { error: "Failed to fetch VIU DRM key: " + String(res.raw || ""), code: res.statusCode });
        }

        return e.blob(200, "application/octet-stream", res.body);
    } catch (err) {
        return e.json(500, { error: String(err) });
    }
});
