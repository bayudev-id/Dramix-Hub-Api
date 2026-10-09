# FreeReels Anonymous (Guest) Login Specification

## Overview
Aplikasi FreeReels menggunakan anonymous/guest login saat pertama kali dibuka pada perangkat baru. Endpoint ini menghasilkan credential OAuth lengkap tanpa memerlukan registrasi atau interaksi pengguna.

Dengan mengimplementasikan flow ini, sistem backend/client kita **sepenuhnya independen dari perangkat fisik (HP)**.

---

## Endpoint Details

- **Method:** `POST`
- **URL:** `https://apiv2.free-reels.com/frv2-api/anonymous/login`
- **Authentication:** ❌ **TIDAK ADA** (satu-satunya endpoint yang dikecualikan dari `Authorization` header)

### Headers Wajib:
```http
User-Agent: FreeReels/2.4.91 (Android 13; Redmi 5 Plus)
Content-Type: application/json
Accept: application/json
Accept-Language: id-ID
app-version: 2.4.91
app-name: com.freereels.app
device: android
device-version: 33
device-id: {device_id}
country: ID
language: id-ID
app-display-lang: id
locale: id_ID
prefer_country: ID
app-language: id
timezone: +7
X-Timezone: Asia/Jakarta
network-type: wifi
screen-width: 432
screen-height: 840
x-device-model: Redmi 5 Plus
x-device-manufacturer: Xiaomi
x-device-brand: Xiaomi
x-device-product: vince
device-language: id-ID
device-country: ID
is-mainland: false
```

### Request Body:
```json
{
  "device_id": "18f6d36e64154485",
  "device_name": "Xiaomi Redmi 5 Plus",
  "sign": "0c833ee6ae844e86ea6e811ac2ad55c8"
}
```

### Signature Algorithm (`sign`):
```python
import hashlib

LOGIN_SECRET_PREFIX = "8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv"  # Note: NO trailing '&'
raw = f"{LOGIN_SECRET_PREFIX}{device_id}"
sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
```

> **Perbedaan Kritis:**  
> - **Header Authorization:** `"8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv&" + oauth_secret` (ada `&`)  
> - **Anonymous Login `sign`:** `"8IAcbWyCsVhYv82S2eofRqK1DF3nNDAv" + device_id` (TANPA `&`)

---

## Response

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "success": true,
    "user_id": 75896942591,
    "name": "Tamu",
    "icon": "https://static-v1.mydramawave.com/avatar/fr_default_guest_dark.png",
    "user_type": 0,
    "auth_key": "JWNuesI4SWaBZJePeQhLoMpiB7Ke4nUd",
    "auth_secret": "6UceA6sw5Oh9yqFHESEMRLntEUaBvopJ"
  }
}
```

### Mapping Field ke OAuth Client:
| Response Field | Digunakan Sebagai | Deskripsi |
|---|---|---|
| `auth_key` | `oauth_token` | Token otorisasi untuk semua API request |
| `auth_secret` | `oauth_secret` | Secret untuk menghitung OAuth MD5 signature |
| `user_id` | `user_id` | Unique ID akun pengguna |
| `user_type` | `account_type` | `0` = Guest/Anonymous |

---

## Source Code Reference

| File Decompiled | Lokasi | Peran |
|---|---|---|
| `Laa/x;` | `aa.x` | Request body model: `deviceId`, `deviceName`, `sign` |
| `Ly9/a;` | `y9.a` | Retrofit interface: `l(aa.x)` -> `POST /anonymous/login` |
| `Lcom/dramawave/feature/login/viewmodel/d;` | `AccountViewModel.anonymousLogin$1` | Menghitung `sign = MD5(PREFIX + deviceId)` |
| `Lcom/dramawave/core/common/toolkit/b0;` | `b0.a(String)` | Fungsi MD5 digest standard (lowercase hex) |
| `Lcom/dramawave/core/devicelocale/g;` | `DeviceUtils.a()` | Menghasilkan `device_name` (Brand + Model) |
