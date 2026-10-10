// pb_hooks/image-proxy.pb.js
// Dramix Gateway - Image Proxy & Optimizer
// Proxies cover images through moviebox_api for server-side resize + WebP conversion

routerAdd("GET", "/api/modelles/image", (e) => {
    try {
        const info = e.requestInfo();
        const url = (info.query.url || "").trim();
        const width = parseInt(info.query.w || "150", 10);

        if (!url) {
            return e.blob(400, "text/plain", "Missing 'url' parameter");
        }

        // Prevent SSRF: only allow known CDN domains
        const allowedDomains = [
            "puui.wetvinfo.com", "vcover-vt-pic.wetvinfo.com",
            "pbcdnw.aoneroom.com", "hakunaymatata.com",
            "media.themoviedb.org", "image.tmdb.org",
            "ykimg.com", "m.ykimg.com",
            "iqiyipic.com", "piciqiyipic.com",
            "wetvinfo.com"
        ];
        
        let urlObj = null;
        try {
            urlObj = new URL(url);
        } catch (e2) {
            return e.blob(400, "text/plain", "Invalid URL");
        }
        
        const host = urlObj.hostname.toLowerCase();
        let allowed = false;
        for (let i = 0; i < allowedDomains.length; i++) {
            if (host === allowedDomains[i] || host.endsWith("." + allowedDomains[i])) {
                allowed = true;
                break;
            }
        }
        if (!allowed) {
            return e.blob(403, "text/plain", "Domain not allowed");
        }

        // Proxy to moviebox_api image resize service
        const encodedUrl = encodeURIComponent(url);
        const res = $http.send({
            url: "http://127.0.0.1:6104/api/resize-image?url=" + encodedUrl + "&w=" + width,
            method: "GET",
            timeout: 15
        });

        if (res.statusCode !== 200) {
            // Fallback: redirect to original URL
            return e.redirect(302, url);
        }

        // Return the resized image with aggressive cache headers
        const headers = {
            "Cache-Control": "public, max-age=86400, immutable",
            "Content-Type": "image/webp",
            "Access-Control-Allow-Origin": "*",
            "X-Proxy": "Dramix-Image-Proxy"
        };

        return e.blob(200, "image/webp", res.raw, headers);
    } catch (err) {
        // Ultimate fallback
        const info2 = e.requestInfo();
        const url2 = (info2.query.url || "").trim();
        if (url2) {
            return e.redirect(302, url2);
        }
        return e.blob(502, "text/plain", "Image proxy error");
    }
});
