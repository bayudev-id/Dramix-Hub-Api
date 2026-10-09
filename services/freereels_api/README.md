# FreeReels API Reverse-Engineering Project

Reconstruksi & analisis API aplikasi streaming short-drama **FreeReels** (DramaWave white-label) via Frida dynamic hook + JADX static decompile.

---

## 📁 Struktur Folder (Rapi)

```
FreeReels/
├── src/                      # Client inti & signer (bibliotested/reusable)
│   ├── freereels_client.py
│   ├── freereels_public_client.py
│   ├── freereels_authenticated.py
│   ├── freereels_complete_client.py
│   ├── freereels_sn_generator.py     # Generator SN (masih placeholder, perlu RE)
│   └── freereels_final.py
│
├── tools/                    # CLI runner & player yang bisa langsung dijalankan
│   ├── main.py                       # [MAIN] Drama Browser + VLC Player interaktif
│   ├── freereels_homepage_bot.py
│   ├── freereels_new_tab_bot.py
│   ├── extract_token.py              # Ekstrak Bearer token dari Frida log
│   └── extract_dramas.py             # Parse daftar drama dari data capture
│
├── experiments/              # Script uji coba signature & endpoint (eksplorasi)
│   ├── fetch_rank_*.py / fetch_homepage_*.py
│   ├── debug_auth_new.py
│   ├── discover_endpoints.py
│   ├── search_endpoint.py
│   ├── quick_test.py
│   └── test_*.py
│
├── data/
│   ├── captures/             # Raw Frida capture (.txt) + dump signature
│   │   ├── data_new.txt, data_rank.txt, data_populer.txt, ...
│   │   └── sig_test.txt, sig_test_2.txt
│   └── samples/              # Response API terformat (JSON) dari eksperimen
│       ├── test_homepage_response.json
│       ├── rank_test_output.json
│       ├── debug_live.json
│       ├── test_dramas_list.json
│       └── rank_real_fixed.json
│
├── js/                       # Frida JavaScript hook scripts (.js)
│   ├── capture_*.js, dump_tokens.js, ssl_bypass.js, frida_hook.js, ...
│
├── docs/                     # Dokumentasi teknis
│   ├── PROJECT_FINDINGS_AND_ANALYSIS.md   # [BARU] Ringkasan temuan lengkap
│   ├── API_ENDPOINTS.md
│   ├── FINAL_AUTH_FOUND.md
│   ├── JADX_ANALYSIS.md
│   ├── REVERSE_ENGINEERING_GUIDE.md
│   └── ...
│
├── New Method/               # (Kosong) Lokasi pengerjaan metode/signature baru
├── requirements.txt
└── __pycache__/
```

---

## 🚀 Cara Menjalankan

**Menjalankan Browser + Player (modus offline capture + live feed):**
```bash
cd D:\BackEnd\Drama\FreeReels
python tools/main.py
```

**Menjalankan Homepage Bot (interaktif):**
```bash
python tools/freereels_homepage_bot.py
```

*Note:* Script `src/` dan `tools/` mungkin mereferensikan path data relatif; pertimbangkan menambahkan `sys.path` bila dipindah.

---

## 🔎 Status Analisis (Ringkas)

| Area | Status |
|---|---|
| Enumerasi host & endpoint | ✅ Selesai |
| Feed homepage (public) | ✅ Berfungsi tanpa auth |
| Streaming HLS & subtitle | ✅ Terbuka (no DRM/token) |
| Skema header OAuth (2-layer) | ✅ Terpetakan |
| Signature statis hasil capture | ✅ Berfungsi (sebelumnya) |
| **Generasi signature dinamis** | ❌ **BELUM** (bottleneck) |
| Endpoint terotentikasi (rank/wallet) | ⚠️ 401 — tergantung signature |

---

## 📌 Catatan Kredensial (jangan commit ke publik)

Kredensial & secret hasil capture ada di `docs/FINAL_AUTH_FOUND.md` dan header `tools/main.py`. Jangan publikasikan ke repository publik. Signature fakultas sudah expired; metode dinamis yang diperlukan ditangani di `New Method/`.

---

## 🧪 Toolchain yang Digunakan

- Python 3.11 + `requests` + `pyperclip`
- Frida (dynamic hook)
- JADX (static decompile)
- (Direncanakan) Burp Suite MCP + Android Reverse IDE untuk intercept & patch signature