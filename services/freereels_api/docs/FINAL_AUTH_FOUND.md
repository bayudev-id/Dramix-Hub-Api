# 🎉 FreeReels API - Authentication FOUND!

## ✅ **Status: AUTHENTICATION METHOD DITEMUKAN!**

**Tanggal**: 2026-02-23  
**Method**: OAuth 1.0 + Request Signature  
**Source**: Frida runtime capture

---

## 🔑 **Authentication Method**

FreeReels menggunakan **2-layer authentication**:

### **Layer 1: OAuth Token (Authorization Header)**

```http
Authorization: oauth_signature=edc1ec44568756ef6a23526dfbd089b1,
               oauth_token=IsSG5rKFz7kfafVlqS8Ubq0JgT4N0a69,
               ts=1771816562579
```

**Components:**
- `oauth_signature` - HMAC signature (per request/session)
- `oauth_token` - Access token (per session)
- `ts` - Timestamp in milliseconds

### **Layer 2: Request Signature (sign Header)**

```http
sign: fkb7tCW63BTpzQcd9+UIY0oL/ZM=
```

- Base64 encoded
- Berubah setiap request
- Kemungkinan SHA1/HMAC of request data

---

## 📋 **Complete Required Headers**

### **Static Headers (tidak berubah):**

```python
{
    "app-name": "com.freereels.app",
    "app-version": "2.2.00",
    "device-version": "33",
    "device-memory": "3.48",
    
    "country": "ID",
    "device-country": "ID",
    "language": "id-ID",
    "device-language": "in-ID",
    "mcc-country": "510",
    "timezone": "+7",
    
    "network-type": "wifi",
    
    "x-device-brand": "Xiaomi",
    "x-device-model": "Redmi 5 Plus",
    "x-device-manufacturer": "Xiaomi",
    "x-device-product": "superior_vince",
    "x-device-fingerprint": "Xiaomi/superior_vince/vince:13/TPM1.230623.090/1768560077:user/release-keys",
    
    "screen-width": "432",
    "screen-height": "840",
    
    "Accept": "application/json"
}
```

### **Dynamic Headers (perlu capture):**

```python
{
    # Device IDs (stabil per device)
    "device-id": "775eddf9b8392d6b",
    "gaid": "784b504c-b5fe-4e4a-b1ba-880c3a78ef61",
    "appsflyer-id": "1771777699791-1023003935210107517",
    "firebase-id": "6c131d64a327919ad79a4bcf3356ec82",
    
    # Session (berubah per session)
    "session-id": "a4676b37-76e6-45b9-824b-2205895afaeb",
    
    # A/B Testing (stabil)
    "Ab-Exps": "901:2991,883:2927,807:2618,...",
    
    # ⚠️ AUTHENTICATION (BERUBAH!)
    "Authorization": "oauth_signature=...,oauth_token=...,ts=...",
    "sign": "..."
}
```

---

## 🛠️ **How to Get Tokens**

### **Step 1: Run Frida Hook**

```bash
cd d:\10. Python\Generator\FreeReels\js

# Capture OAuth token
frida -U FreeReels -l capture_oauth_token.js --no-pause

# Capture full request
frida -U FreeReels -l capture_request_v2.js --no-pause
```

### **Step 2: Login di Aplikasi**

1. Buka FreeReels
2. Login (atau refresh jika sudah login)
3. Lihat output Frida

### **Step 3: Copy Values**

Dari output Frida, copy:

```
Authorization: oauth_signature=EDC1EC44568756EF...,oauth_token=ISG5RKFZ7KFAFVL...,ts=1771816562579
sign: FKB7TCW63BTPZQCD9+UIY0OL/ZM=
device-id: 775EDDF9B8392D6B
gaid: 784B504C-B5FE-4E4A-B1BA-880C3A78EF61
session-id: A4676B37-76E6-45DC-824B-2205895AFAEB
```

### **Step 4: Update Python Client**

Edit `freereels_complete_client.py`:

```python
CAPTURED_VALUES = {
    "device-id": "YOUR_DEVICE_ID",
    "gaid": "YOUR_GAID",
    "appsflyer-id": "YOUR_APPSFLYER_ID",
    "firebase-id": "YOUR_FIREBASE_ID",
    "session-id": "YOUR_SESSION_ID",
    
    "Authorization": "oauth_signature=...,oauth_token=...,ts=...",
    "sign": "YOUR_SIGN_VALUE",
}
```

### **Step 5: Run Client**

```bash
cd d:\10. Python\Generator\FreeReels
python freereels_complete_client.py
```

---

## 📡 **Working Endpoints**

### **Tested & Working:**

| Method | Endpoint | Auth Required |
|--------|----------|---------------|
| GET | `/homepage/v2/tab/index?tab_key={key}` | ✅ Yes |
| GET | `/content/message/unread` | ✅ Yes |
| POST | `/popup/banner/list` | ✅ Yes |
| GET | `/user/risk/check` | ✅ Yes |
| POST | `/b/frv2_client_track` | ✅ Yes |

### **Base URLs:**

```
API:      https://apiv2.free-reels.com
Tracking: https://trace.free-reels.com
Static:   https://static-v1.mydramawave.com
Video:    https://video-v1.mydramawave.com
```

---

## 🔍 **Signature Generation Pattern**

Dari Frida capture, signing string format:

```
{URL}
```

Example:
```
https://apiv2.free-reels.com/frv2-api/homepage/v2/tab/index?tab_key=505&position_index=10000&rec_trigger=1
```

**Algorithm**: Kemungkinan **HMAC-SHA1** (20 bytes = 160 bits → Base64 = 28 chars)

---

## 📁 **Available Tools**

| File | Purpose |
|------|---------|
| `freereels_complete_client.py` | ✅ Complete Python client |
| `js/capture_oauth_token.js` | Capture OAuth tokens |
| `js/capture_request_v2.js` | Capture full requests |
| `js/capture_headers.js` | Capture sign headers |
| `js/capture_full_request.js` | Full request + signature |

---

## 🎯 **Next Steps untuk Full Access**

### **1. Token Refresh Mechanism**

Tokens expire. Perlu hook token refresh:

```bash
frida -U FreeReels -l capture_oauth_token.js --no-pause
# Wait for token refresh (setelah beberapa menit/jam)
```

### **2. Signature Generation**

Untuk generate signature sendiri (tanpa Frida):

**Perlu reverse engineering:**
1. Cari class yang generate `sign` header
2. Extract secret key
3. Implement di Python

**Hook untuk cari signing code:**

```bash
frida -U FreeReels -l hook_house_builder.js --no-pause
```

### **3. Login Flow Automation**

Automate login untuk dapat token baru:

```python
def login(phone, otp):
    # Hook login endpoint
    # Extract token from response
    # Update headers
    pass
```

---

## ⚠️ **Important Notes**

1. **Tokens expire** - Session ID dan OAuth token ada expiry time
2. **Device fingerprinting** - Harus konsisten dengan device info
3. **A/B Testing** - `Ab-Exps` header harus sama per user
4. **Rate limiting** - Jangan spam requests
5. **Signature per request** - `sign` header berubah setiap request

---

## 📚 **References**

- OAuth 1.0 Spec: https://oauth.net/core/1.0/
- HMAC-SHA1: https://en.wikipedia.org/wiki/HMAC
- Frida Docs: https://frida.re/docs/

---

**Last Updated**: 2026-02-23  
**Status**: ✅ Authentication Found, ⚠️ Signature Generation Still Unknown  
**Priority**: Reverse engineer signature generation algorithm
