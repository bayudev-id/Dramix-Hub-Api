#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pair_device.py — Buat sesi CineFlow INDEPENDEN via TV Device-Pairing (auth v2).

Kenapa ini dipakai:
  - refresh_token CineFlow bersifat single-use & rotating. Jika proxy dan HP
    berbagi 1 refresh token, keduanya saling mematikan (yang kalah kena 401
    "rotated" -> app HP logout / proxy basi).
  - Solusi terbaik (Opsi 1): proxy punya sesi sendiri ber-identity "android_tv"
    via alur pairing resmi:
        1. POST /api/app/auth/device/pairing      -> device_code, user_code, url
        2. User buka verification_uri di browser, login Google & Approve
        3. GET  /api/app/auth/device/status       -> poll sampai approved, dapat grant_token
        4. POST /api/app/auth/device/exchange     -> access_token + refresh_token (milik proxy sendiri)
  - Hasilnya proxy & HP 100% independen. Tidak butuh root/ADB/force-stop/sync.

Struktur penyimpanan session mengikuti format main.py (_save_to_cache):
  {
    "access_token": str,
    "refresh_token": str,
    "expires_at": float (epoch, access token),
    "app_instance_id": str (ID baru milik proxy),
    "phone_profile": { user info dari exchange }
  }

Setelah menyimpan ke session_data.json, script OTOMATIS meng-upload ke Supabase
(tabel cineflow_sessions, id=default) selama SUPABASE_URL dan
SUPABASE_SERVICE_ROLE_KEY tersedia di .env / environment. Ini penting karena
main.py memprioritaskan Supabase sebagai storage utama saat start.

Pemakaian:
  python pair_device.py                     # default: tulis session_data.json + sync Supabase
  python pair_device.py --output alt.json   # tulis ke file lain (+ sync Supabase)
  python pair_device.py --no-backup         # tanpa backup file lama
  python pair_device.py --no-supabase       # SKIP sync ke Supabase
"""

import argparse
import json
import os
import shutil
import sys
import time
import uuid
from datetime import datetime

import httpx

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE = "https://ngintipya2.cineflow.my.id"
PAIRING_URL = f"{BASE}/api/app/auth/device/pairing"
STATUS_URL = f"{BASE}/api/app/auth/device/status"
EXCHANGE_URL = f"{BASE}/api/app/auth/device/exchange"

UA = "CineFlow/0.2.8 (com.cineflow.app; Android 13; SDK 33)"

# Identitas perangkat TV milik proxy (independen dari HP)
DEVICE_INFO = {
    "android_release": "13",
    "android_sdk_int": 33,
    "app_version_code": 12,
    "app_version_name": "0.2.8",
    "brand": "CineFlow Proxy",
    "device_type": "android_tv",
    "locale": "en-US",
    "manufacturer": "CineFlow",
    "model": "Proxy TV",
    "package_name": "com.cineflow.app",
    "ui_mode": "tv",
}

DEFAULT_OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "session_data.json")


def http_client() -> httpx.Client:
    return httpx.Client(
        headers={
            "accept": "application/json",
            "User-Agent": UA,
            "X-Requested-With": "com.cineflow.app",
            "content-type": "application/json; charset=UTF-8",
        },
        timeout=20.0,
    )


def start_pairing(client: httpx.Client, app_instance_id: str) -> dict:
    body = {
        "app_instance_id": app_instance_id,
        "device_type": DEVICE_INFO["device_type"],
        "ui_mode": DEVICE_INFO["ui_mode"],
    }
    resp = client.post(PAIRING_URL, json=body)
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Pairing gagal: {data.get('message')} (code={data.get('code')})")
    return data["data"]


def poll_status(client: httpx.Client, device_code: str, app_instance_id: str, timeout_s: int) -> dict:
    params = {"device_code": device_code, "app_instance_id": app_instance_id}
    last_interval = 5
    started = time.time()
    while time.time() - started < timeout_s:
        try:
            resp = client.get(STATUS_URL, params=params)
            data = resp.json()
        except (httpx.TransportError, httpx.ReadError, httpx.RemoteProtocolError, ValueError, json.JSONDecodeError) as exc:
            print(f"  [status] kesalahan jaringan ({exc.__class__.__name__}), retry...")
            time.sleep(3)
            continue
        if data.get("code") != 200:
            print(f"  [status] cek gagal: {data.get('message')}")
        else:
            d = data["data"]
            status = d.get("status", "pending")
            print(f"  [status] {status} approved={d.get('approved')} (t={int(time.time() - started)}s)")
            if d.get("approved") and d.get("grant_token"):
                return d
            last_interval = d.get("interval_seconds") or last_interval
        time.sleep(max(3, int(last_interval)))
    raise TimeoutError(f"Pairing tidak di-approve dalam {timeout_s}s. Coba jalankan ulang.")


def exchange(client: httpx.Client, grant_token: str, app_instance_id: str) -> dict:
    body = {
        "grant_token": grant_token,
        "app_instance_id": app_instance_id,
        **{k: v for k, v in DEVICE_INFO.items() if k != "app_version_code" and k != "app_version_name"},
    }
    resp = client.post(EXCHANGE_URL, json=body)
    data = resp.json()
    if data.get("code") != 200:
        raise RuntimeError(f"Exchange gagal: {data.get('message')} (code={data.get('code')})")
    return data["data"]


def save_session(session: dict, output: str, backup: bool) -> str:
    output = os.path.abspath(output)
    os.makedirs(os.path.dirname(output) or ".", exist_ok=True)

    if backup and os.path.exists(output):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bak = f"{output}.bak_{stamp}"
        shutil.copy2(output, bak)
        print(f"  Backup session lama -> {bak}")

    with open(output, "w", encoding="utf-8") as f:
        json.dump(session, f, ensure_ascii=False, indent=2)
    return output


def _load_env():
    """Muat .env dari root proyek (parent dari folder tools/)."""
    if load_dotenv is None:
        return
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_path = os.path.join(root, ".env")
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)


def sync_to_supabase(session: dict) -> bool:
    """Upload sesi ke Supabase (tabel cineflow_sessions, id='default').

    main.py memprioritaskan Supabase saat start, jadi sesi TV ini HARUS ada di
    sana agar proxy langsung memakai sesi mandiri (bukan sesi HP lama).
    Return True bila sukses, False bila dikonfigurasi tapi gagal, None bila
    Supabase tidak dikonfigurasi.
    """
    _load_env()
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
    table = os.environ.get("SUPABASE_TABLE", "cineflow_sessions")

    if not url or not key:
        print("  [supabase] Dilewati: SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY tidak ditemukan.")
        return None

    payload = {
        "id": "default",
        "access_token": session.get("access_token"),
        "refresh_token": session.get("refresh_token"),
        "expires_at": session.get("expires_at"),
        "app_instance_id": session.get("app_instance_id"),
        "phone_profile": session.get("phone_profile"),
    }
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation",
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(f"{url}/rest/v1/{table}", json=payload, headers=headers)
        if resp.status_code in (200, 201):
            print(f"  [supabase] OK: sesi di-upload (app_instance_id={session.get('app_instance_id')}).")
            return True
        print(f"  [supabase] GAGAL status {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as exc:
        print(f"  [supabase] ERROR: {exc}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pairing TV CineFlow -> sesi token independen untuk proxy")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="File session output (default: ../session_data.json)")
    parser.add_argument("--no-backup", action="store_true", help="Jangan backup file session lama")
    parser.add_argument("--no-supabase", action="store_true", help="Skip upload sesi ke Supabase")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout tunggu approve (detik)")
    args = parser.parse_args()

    app_instance_id = str(uuid.uuid4())
    print("=" * 70, flush=True)
    print("CineFlow TV Device Pairing â€” buat sesi proxy independen")
    print("=" * 70, flush=True)
    print(f"app_instance_id baru (milik proxy): {app_instance_id}")
    print()

    with http_client() as client:
        # 1) Mulai pairing
        print("[1/4] Mulai pairing device...")
        pairing = start_pairing(client, app_instance_id)
        print(f"      device_code : {pairing['device_code']}")
        print(f"      user_code   : {pairing['user_code']}")
        print()

        # 2) Minta user approve
        print("[2/4] BUKA LINK BERIKUT DI BROWSER (PC/HP), login Google, lalu klik Approve:")
        print()
        print("      " + pairing.get("verification_uri_complete", pairing["verification_uri"]))
        print()
        print(f"      (berlaku {pairing.get('expires_in_seconds', 900)} detik â€” user_code: {pairing['user_code']})")
        print()

        # 3) Poll status
        print("[3/4] Menunggu approval (poll status)...")
        status = poll_status(client, pairing["device_code"], app_instance_id, args.timeout)
        grant_token = status["grant_token"]
        print(f"      grant_token diperoleh: {grant_token[:24]}...")
        print()

        # 4) Exchange -> token
        print("[4/4] Tukar grant_token -> access/refresh token...")
        ex = exchange(client, grant_token, app_instance_id)

    token_info = ex["token_info"]
    user = ex.get("user") or {}
    expires_at = time.time() + int(token_info.get("expires_in", 600))

    session = {
        "access_token": token_info["access_token"],
        "refresh_token": token_info["refresh_token"],
        "expires_at": expires_at,
        "app_instance_id": app_instance_id,
        "device_type": "android_tv",
        "phone_profile": {
            "user_id": user.get("id"),
            "email": user.get("email"),
            "display_name": user.get("display_name"),
            "google_sub": user.get("google_sub"),
            "device_type": "android_tv",
            "app_instance_id": app_instance_id,
            "provider": user.get("provider", "google"),
            "linked_at": user.get("linked_at"),
            "refresh_token_expires_at_epoch_ms": int(time.time() + int(token_info.get("refresh_expires_in", 2592000))) * 1000,
        },
    }

    out = save_session(session, args.output, backup=not args.no_backup)

    # Sync ke Supabase (storage utama main.py). Skip bila --no-supabase.
    sb_status = None
    if not args.no_supabase:
        print()
        print("Menyinkronkan sesi ke Supabase...", flush=True)
        sb_status = sync_to_supabase(session)

    print()
    print("=" * 70, flush=True)
    print("SUKSES! Sesi proxy independen tersimpan.")
    print("=" * 70, flush=True)
    print(f"  File        : {out}")
    if sb_status is True:
        print("  Supabase    : OK (tersinkron)")
    elif sb_status is False:
        print("  Supabase    : GAGAL (cek .env / koneksi; session_data.json tetap lokal)")
    else:
        print("  Supabase    : dilewati (tidak dikonfigurasi)")
    print(f"  Instance    : {app_instance_id}")
    print(f"  User        : {user.get('email') or user.get('id')} ({user.get('display_name') or '?'})")
    print(f"  Refresh token : {token_info['refresh_token'][:20]}...")
    print(f"  Access token  : {token_info['access_token'][:20]}... (expires {token_info.get('expires_in', 600)}s)")
    print()
    print("Catatan: HP & proxy sekarang punya sesi masing-masing. Tidak ada lagi")
    print("konflik rotasi refresh token. Tokens proxy di-rotate sendiri oleh main.py.")
    print("refresh_expires_in:", token_info.get("refresh_expires_in"))


if __name__ == "__main__":
    sys.exit(main())