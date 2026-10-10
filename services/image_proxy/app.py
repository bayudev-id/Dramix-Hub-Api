from fastapi import FastAPI, Query
from fastapi.responses import Response, JSONResponse
import requests
import io

try:
    from PIL import Image
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

app = FastAPI(title="Dramix Image Proxy")


@app.get("/api/resize-image")
def resize_image(url: str = Query(...), w: int = Query(150, ge=50, le=800)):
    """
    Download, resize to thumbnail (max width {w}px), convert to WebP.
    Returns <15KB per image for typical cover thumbnails.
    """
    if not HAS_PILLOW:
        # Fallback: proxy original without resize
        try:
            resp = requests.get(url, timeout=10, stream=True)
            resp.raise_for_status()
            return Response(
                content=resp.content,
                media_type=resp.headers.get("Content-Type", "image/jpeg"),
                headers={
                    "Cache-Control": "public, max-age=86400, immutable",
                    "X-Proxy": "Dramix-Image-Proxy (passthrough - no Pillow)"
                }
            )
        except Exception as e:
            return JSONResponse(status_code=502, content={"error": str(e)})

    try:
        resp = requests.get(url, timeout=10, stream=True)
        resp.raise_for_status()

        img_data = io.BytesIO(resp.content)

        img = Image.open(img_data)
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (0, 0, 0))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")

        # Resize maintaining aspect ratio
        if img.width > w:
            ratio = w / img.width
            new_h = int(img.height * ratio)
            img = img.resize((w, new_h), Image.LANCZOS)

        # Save as WebP quality 80
        output = io.BytesIO()
        img.save(output, format="WEBP", quality=80, method=6)
        output.seek(0)

        return Response(
            content=output.getvalue(),
            media_type="image/webp",
            headers={
                "Cache-Control": "public, max-age=86400, immutable",
                "X-Proxy": "Dramix-Image-Proxy",
                "X-Original-Size": str(resp.headers.get("Content-Length", "unknown")),
                "X-Resized-Size": f"{output.getbuffer().nbytes / 1024:.1f}KB"
            }
        )
    except Exception as e:
        # Ultimate fallback: redirect to original
        try:
            return JSONResponse(status_code=302, headers={"Location": url})
        except:
            return JSONResponse(status_code=502, content={"error": str(e)})


@app.get("/health")
def health():
    return {"status": "ok", "pillow": HAS_PILLOW}
