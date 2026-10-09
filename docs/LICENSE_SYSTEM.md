# Dramix License System Documentation

Sistem lisensi VIP freemium untuk aplikasi Dramix Android (`com.dramix.app`).

## Arsitektur

```
[Android App] 
     │
     │ 1. POST /api/license/activate { license_key, device_id }
     │ 2. GET  /api/license/status?device_id=...
     ▼
[PocketBase Gateway :8090]
  ├── pb_hooks/license.pb.js
  └── pb_migrations/..._licenses.js  (table `licenses`)
     ▲
     │ 3. POST /api/license/admin/generate  (Bearer Token: pb_master_token_2026)
     │ 4. GET  /api/license/admin/list
     │
[Admin CLI Tool: license-admin.ps1]
```

## Keamanan (Anti-Bobol)

1. **Admin Endpoint Terisolasi**:
   - `/api/license/admin/generate` & `/api/license/admin/list` **hanya bisa diakses dengan Bearer Token server-side**.
   - Android App **tidak punya** token admin dan tidak bisa generate key sendiri.

2. **Hardware Device Binding**:
   - 1 license key hanya bisa di-bind ke 1 `device_id` (SHA-256 dari `ANDROID_ID`).
   - Jika device lain mencoba mengaktifkan key yang sama → `409 Conflict: License already activated on another device`.

3. **Status Key Lifecycle**:
   - `unused` → key baru belum di-bind
   - `active` → sudah di-bind ke device tertentu, berlaku sampai `expires_at`
   - `expired` → durasi habis (server otomatis tolak)
   - `revoked` → diblokir manual oleh admin

4. **Entropi Key**:
   - Format: `LCN-XXXX-XXXX-XXXX` (12 karakter alfanumerik acak, 36^12 kombinasi).
   - Hampir mustahil di-brute force.

---

## Cara Generate Lisensi Baru

Gunakan script CLI di folder `Dramix_Gateway`:

```powershell
# Generate 1 key default (30 hari, plan VIP)
.\license-admin.ps1 generate

# Generate 5 key untuk 30 hari
.\license-admin.ps1 generate --count 5 --duration 30

# Generate key paket 1 tahun (365 hari)
.\license-admin.ps1 generate --count 10 --duration 365 --plan "VIP 1 Tahun"
```

Contoh output:
```
Generating 3 license key(s) (60 days, plan: VIP)...
Generated successfully

License Key: LCN-0BVP-4Y2N-UZ1V
  Status: unused
  Plan: VIP
  Duration: 60 days
```

---

## Cara Melihat Lisensi

```powershell
# List semua lisensi (halaman 1)
.\license-admin.ps1 list

# Filter hanya yang aktif
.\license-admin.ps1 list --status active

# Filter hanya yang belum dipakai (siap jual/bagikan)
.\license-admin.ps1 list --status unused
```

---

## Cara Cek Status Device Tertentu

```powershell
.\license-admin.ps1 status --device-id "android_test_device_001"
```

---

## Testing di Android App

1. Buka aplikasi Dramix di Android
2. Masuk ke tab **Profil**
3. Di kartu **Aktivasi Lisensi VIP**, masukkan salah satu key yang berstatus `unused`:
   - Contoh key yang tersedia: `LCN-467A-3FXN-10Z6` atau `LCN-HAX6-A2BX-NE97`
4. Tekan tombol **Aktivasi Sekarang**
5. Status akan berubah menjadi **VIP Aktif** dan episode 4+ di semua drama/anime langsung terbuka!
