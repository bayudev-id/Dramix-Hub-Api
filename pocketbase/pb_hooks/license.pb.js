/// <reference path="../pb_data/types.d.ts" />

// POST /api/license/activate - Activate license with device binding
routerAdd("POST", "/api/license/activate", (e) => {
    try {
        const info = e.requestInfo();
        const body = info.body || {};
        const licenseKey = body.license_key;
        const deviceId = body.device_id;

        if (!licenseKey || !deviceId) {
            return e.json(400, {
                "code": 400,
                "message": "Missing license_key or device_id",
                "data": null
            });
        }

        // Find license by key
        const records = $app.findRecordsByFilter("licenses", `license_key = "${licenseKey}"`, "", 1);
        if (records.length === 0) {
            return e.json(404, {
                "code": 404,
                "message": "Invalid license key",
                "data": null
            });
        }

        const license = records[0];
        const status = license.get("status");
        const boundDeviceId = license.get("device_id") || "";
        const now = Math.floor(Date.now() / 1000);

        // Check if license is expired
        const expiresAt = license.get("expires_at");
        if (expiresAt && expiresAt < now) {
            license.set("status", "expired");
            $app.save(license);
            return e.json(410, {
                "code": 410,
                "message": "License expired",
                "data": null
            });
        }

        // Check status
        if (status === "revoked") {
            return e.json(403, {
                "code": 403,
                "message": "License revoked",
                "data": null
            });
        }

        if (status === "expired") {
            return e.json(410, {
                "code": 410,
                "message": "License expired",
                "data": null
            });
        }

        // Check device binding
        if (status === "active" && boundDeviceId && boundDeviceId !== deviceId) {
            return e.json(409, {
                "code": 409,
                "message": "License already activated on another device",
                "data": null
            });
        }

        // Activate license
        if (status === "unused") {
            const durationDays = license.get("duration_days") || 30;
            const activatedAt = now;
            const expiresAtNew = activatedAt + (durationDays * 86400);
            const charsToken = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
            let sessionToken = "";
            for (let i = 0; i < 64; i++) {
                sessionToken += charsToken[Math.floor(Math.random() * charsToken.length)];
            }

            license.set("status", "active");
            license.set("device_id", deviceId);
            license.set("activated_at", activatedAt);
            license.set("expires_at", expiresAtNew);
            license.set("session_token", sessionToken);
            $app.save(license);

            return e.json(200, {
                "code": 200,
                "message": "License activated successfully",
                "data": {
                    "is_vip": true,
                    "license_key": licenseKey,
                    "token": sessionToken,
                    "expires_at": expiresAtNew,
                    "plan_name": license.get("plan_name") || "VIP"
                }
            });
        }

        // Already active on this device - return current status
        return e.json(200, {
            "code": 200,
            "message": "License already active",
            "data": {
                "is_vip": true,
                "license_key": licenseKey,
                "token": license.get("session_token") || "",
                "expires_at": license.get("expires_at") || 0,
                "plan_name": license.get("plan_name") || "VIP"
            }
        });

    } catch (error) {
        return e.json(500, {
            "code": 500,
            "message": "Internal server error: " + error.message,
            "data": null
        });
    }
});

// GET /api/license/status - Check license status by device_id
routerAdd("GET", "/api/license/status", (e) => {
    try {
        const deviceId = e.request.url.query().get("device_id");
        
        if (!deviceId) {
            return e.json(400, {
                "code": 400,
                "message": "Missing device_id parameter",
                "data": null
            });
        }

        // Find active license for this device
        const records = $app.findRecordsByFilter("licenses", `device_id = "${deviceId}" && status = "active"`, "", 1);
        
        if (records.length === 0) {
            return e.json(200, {
                "code": 200,
                "message": "No active license found",
                "data": {
                    "is_vip": false,
                    "license_key": null,
                    "token": null,
                    "expires_at": null,
                    "plan_name": null
                }
            });
        }

        const license = records[0];
        const now = Math.floor(Date.now() / 1000);
        const expiresAt = license.get("expires_at");

        // Check expiry
        if (expiresAt && expiresAt < now) {
            license.set("status", "expired");
            $app.save(license);
            return e.json(200, {
                "code": 200,
                "message": "License expired",
                "data": {
                    "is_vip": false,
                    "license_key": license.get("license_key"),
                    "token": null,
                    "expires_at": expiresAt,
                    "plan_name": license.get("plan_name") || "VIP"
                }
            });
        }

        return e.json(200, {
            "code": 200,
            "message": "License active",
            "data": {
                "is_vip": true,
                "license_key": license.get("license_key"),
                "token": license.get("session_token") || "",
                "expires_at": expiresAt,
                "plan_name": license.get("plan_name") || "VIP"
            }
        });

    } catch (error) {
        return e.json(500, {
            "code": 500,
            "message": "Internal server error: " + error.message,
            "data": null
        });
    }
});

// POST /api/license/admin/generate - Generate new license (admin only)
routerAdd("POST", "/api/license/admin/generate", (e) => {
    try {
        // Verify admin token
        const authHeader = e.request.header.get("Authorization");
        const expectedToken = "Bearer pb_master_token_2026"; // In production, use env var
        
        if (!authHeader || authHeader !== expectedToken) {
            return e.json(401, {
                "code": 401,
                "message": "Unauthorized - invalid admin token",
                "data": null
            });
        }

        const body = e.requestInfo().body || {};
        const durationDays = body.duration_days || 30;
        const planName = body.plan_name || "VIP";
        const count = body.count || 1;

        if (count > 100) {
            return e.json(400, {
                "code": 400,
                "message": "Cannot generate more than 100 keys at once",
                "data": null
            });
        }

        const generated = [];
        const collection = $app.findCollectionByNameOrId("licenses");

        for (let i = 0; i < count; i++) {
            const charsKey = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
            let licenseKey = "LCN-";
            for (let j = 0; j < 12; j++) {
                if (j > 0 && j % 4 === 0) licenseKey += "-";
                licenseKey += charsKey[Math.floor(Math.random() * charsKey.length)];
            }
            const record = new Record(collection);
            
            record.set("license_key", licenseKey);
            record.set("status", "unused");
            record.set("plan_name", planName);
            record.set("duration_days", durationDays);
            
            $app.save(record);
            
            generated.push({
                "license_key": licenseKey,
                "duration_days": durationDays,
                "plan_name": planName,
                "status": "unused"
            });
        }

        return e.json(200, {
            "code": 200,
            "message": `Generated ${count} license key(s)`,
            "data": {
                "licenses": generated
            }
        });

    } catch (error) {
        return e.json(500, {
            "code": 500,
            "message": "Internal server error: " + error.message,
            "data": null
        });
    }
});

// GET /api/license/admin/list - List all licenses (admin only)
routerAdd("GET", "/api/license/admin/list", (e) => {
    try {
        const authHeader = e.request.header.get("Authorization");
        const expectedToken = "Bearer pb_master_token_2026";
        
        if (!authHeader || authHeader !== expectedToken) {
            return e.json(401, {
                "code": 401,
                "message": "Unauthorized - invalid admin token",
                "data": null
            });
        }

        const status = e.request.url.query().get("status") || "";
        const page = parseInt(e.request.url.query().get("page") || "1");
        const perPage = parseInt(e.request.url.query().get("per_page") || "20");

        let filter = "";
        if (status) {
            filter = `status = "${status}"`;
        }

        const records = $app.findRecordsByFilter("licenses", filter, "-created", perPage, (page - 1) * perPage);
        
        const items = records.map(record => {
            return {
                "id": record.id,
                "license_key": record.get("license_key"),
                "device_id": record.get("device_id") || null,
                "status": record.get("status"),
                "plan_name": record.get("plan_name") || "VIP",
                "duration_days": record.get("duration_days") || 30,
                "activated_at": record.get("activated_at") || null,
                "expires_at": record.get("expires_at") || null,
                "created": record.created,
                "updated": record.updated
            };
        });

        return e.json(200, {
            "code": 200,
            "message": "Success",
            "data": {
                "licenses": items,
                "page": page,
                "per_page": perPage,
                "total": items.length
            }
        });

    } catch (error) {
        return e.json(500, {
            "code": 500,
            "message": "Internal server error: " + error.message,
            "data": null
        });
    }
});
