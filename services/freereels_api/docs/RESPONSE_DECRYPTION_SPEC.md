# FreeReels API Response Decryption Specification

## Overview
Beberapa endpoint API FreeReels mengembalikan response body terenkripsi.  
Server menandai response terenkripsi dengan header `x-decry: 1`.  
Response dienkripsi oleh server dan didekripsi di client via native library `libdwguard.so`.

## Detection
Response header `x-decry` menentukan status enkripsi:
- `"0"` atau tidak ada → **plaintext** (langsung parse JSON)
- `"1"` → **terenkripsi** (perlu decrypt)

## Cipher Details
| Parameter | Value |
|-----------|-------|
| Algorithm | AES-128-CBC |
| Key Length | 16 bytes |
| Block Size | 16 bytes |
| Padding | PKCS7 |
| IV | Prepended (first 16 bytes of ciphertext) |
| Encoding | Base64 |

## Format
```
HTTP Response Body = Base64Encode(IV || AES-CBC-Encrypt(plaintext || PKCS7-padding))
```

## Keys (Extracted from libdwguard.so)
```python
# Flavor 1 (primary — used for most responses)
KEY_FLAVOR_1 = b"3sa9Kx7mQu3Ls8Wd"    # 16 bytes, offset 0x13c0

# Flavor 2 (alternative)
KEY_FLAVOR_2 = b"79psatnvfgktswba"     # 16 bytes, offset 0x13d0
```

Flavor ditentukan oleh validasi APK signature hash di runtime.  
Untuk `com.freereels.app` yang sah, flavor = 1.

## Decryption Python
```python
import base64
from Crypto.Cipher import AES

def decrypt_response(base64_cipher: str) -> str:
    raw = base64.b64decode(base64_cipher)
    iv = raw[:16]
    ciphertext = raw[16:]
    
    key = b"3sa9Kx7mQu3Ls8Wd"
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(ciphertext)
    
    # Remove PKCS7 padding
    pad_len = decrypted[-1]
    plaintext = decrypted[:-pad_len]
    
    return plaintext.decode("utf-8")
```

## Anti-Tampering
`libdwguard.so` melakukan pemeriksaan anti-debug:
1. **TracerPid check**: Membaca `/proc/self/status` dan membunuh proses jika `TracerPid != 0` (mendeteksi Frida attach)
2. **APK signature validation**: SHA-256 hash dari APK signing certificate dibandingkan dengan 8 whitelist hash hardcoded (untuk package: `com.freereels.app`, `com.hotdrama.app`, `com.dramawave.app`)
3. **AES self-test**: Memverifikasi AES implementasi benar sebelum digunakan

## Source Reference
| Component | Location |
|-----------|----------|
| Native library | `lib/arm64-v8a/libdwguard.so` (20 KB) |
| JNI bridge | `CryptoNative.decryptResponse(String, int[])` |
| OkHttp interceptor | `ResponseDecryptInterceptor` |
| Key selection | Function at `0x3974` in `libdwguard.so` |
| Flavor detection | Function at `0x3fb4` in `libdwguard.so` |
| AES S-Box | Offset `0x11b1` in `libdwguard.so` |
