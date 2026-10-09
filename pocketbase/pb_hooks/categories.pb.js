// pb_hooks/categories.pb.js
// Dramix Gateway - Unified Categories Router & Adapter for /api/modelles/categories

routerAdd("GET", "/api/modelles/categories", (e) => {
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

        // Validasi query parameters (strict)
        const queryKeys = Object.keys(info.query || {});
        for (let i = 0; i < queryKeys.length; i++) {
            if (queryKeys[i] !== "model_id") {
                return jsonError(400, "Invalid or missing request parameters");
            }
        }

        const modelId = (info.query.model_id || "").trim();
        if (!modelId) {
            return jsonError(400, "Invalid or missing request parameters");
        }

        // 1. Validasi Provider terhadap database PocketBase
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

        let items = [];

        // 1. KissKH (Port 7403)
        if (normalizedId === "kisskh") {
            const res = $http.send({
                url: "http://127.0.0.1:7403/api/Home",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari KissKH service");
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.opId && String(it.opId) !== "show") {
                    items.push({
                        id: String(it.opId),
                        name: String(it.title || it.opId)
                    });
                }
            }
        }
        // 2. WeTV (Port 7402)
        else if (normalizedId === "wetv") {
            const res = $http.send({
                url: "http://127.0.0.1:7402/api/wetv/categories",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari WeTV service");
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.id) {
                    items.push({
                        id: String(it.id),
                        name: String(it.name)
                    });
                }
            }
        }
        // 3. MovieBox (Port 7404)
        else if (normalizedId === "moviebox") {
            const res = $http.send({
                url: "http://127.0.0.1:7404/categories",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari MovieBox service: " + res.statusCode);
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.opId) {
                    items.push({
                        id: String(it.opId),
                        name: String(it.title || it.opId)
                    });
                }
            }
        }
        // 4. Viu (Port 7405)
        else if (normalizedId === "viu") {
            const res = $http.send({
                url: "http://127.0.0.1:7405/api/category?api_key=912ursfh283fjefw8234u320t9uejf2983048290859032jfej",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari Viu service");
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                const catId = it.category_id || it.opId;
                if (catId) {
                    items.push({
                        id: String(catId),
                        name: String(it.title)
                    });
                }
            }
        }
        // 5. FreeReels (Port 7406)
        else if (normalizedId === "freereels") {
            const res = $http.send({
                url: "http://127.0.0.1:7406/api/tabs/complete",
                method: "GET",
                timeout: 15
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari FreeReels service");
            }
            const raw = (res.json && res.json.data && res.json.data.list) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                const catId = it.module_key || it.tab_key;
                if (catId) {
                    items.push({
                        id: String(catId),
                        name: String(it.name)
                    });
                }
            }
        }
        // 6. iQIYI (Port 7407)
        else if (normalizedId === "iqiyi") {
            const res = $http.send({
                url: "http://127.0.0.1:7407/api/tabs",
                method: "GET",
                timeout: 10
            });
            if (res.statusCode !== 200) {
                return jsonError(502, "Gagal mengambil kategori dari iQIYI service");
            }
            const raw = (res.json && res.json.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                const catId = it.tab_key || it.module_key;
                if (catId) {
                    items.push({
                        id: String(catId),
                        name: String(it.name)
                    });
                }
            }
        }
        // 7. CineFlow Hub Upstream (Port 7401)
        else {
            const cfRes = $http.send({
                url: "http://127.0.0.1:7401/api/modelles/categories?model_id=" + encodeURIComponent(canonicalId),
                method: "GET",
                timeout: 15
            });
            if (cfRes.statusCode !== 200) {
                return jsonError(cfRes.statusCode, "Gagal mengambil kategori dari upstream CineFlow");
            }
            const raw = (cfRes.json && cfRes.json.data && cfRes.json.data.data) || [];
            for (let i = 0; i < raw.length; i++) {
                const it = raw[i];
                if (it && it.id) {
                    items.push({
                        id: String(it.id),
                        name: String(it.name)
                    });
                }
            }
        }

        const catItems = items.map(it => {
            return "{" +
                '"id":' + JSON.stringify(it.id) + "," +
                '"name":' + JSON.stringify(it.name) +
            "}";
        });

        const jsonStr = "{" +
            '"code":200,' +
            '"message":"success",' +
            '"data":{' +
                '"model_id":' + JSON.stringify(canonicalId) + "," +
                '"data":[' + catItems.join(",") + "]" +
            "}" +
        "}";

        return e.blob(200, "application/json", jsonStr);

    } catch (err) {
        return jsonError(500, "Gateway error: " + err);
    }
});
