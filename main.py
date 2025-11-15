import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from typing import List, Optional

app = FastAPI(title="YouTube Lite API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- External sources ---
PIPED_BASE = os.getenv("PIPED_BASE", "https://piped.video")


def fetch_json(url: str, params: Optional[dict] = None):
    try:
        r = requests.get(url, params=params, timeout=12)
        r.raise_for_status()
        return r.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")


@app.get("/")
def read_root():
    return {"message": "YouTube Lite API running", "piped": PIPED_BASE}


@app.get("/api/search")
def search_videos(q: str = Query(..., min_length=1), page: int = 1):
    """Search videos via Piped (no API key required)."""
    data = fetch_json(f"{PIPED_BASE}/api/v1/search", params={"q": q, "page": page})
    # Filter only videos
    items = [i for i in data if i.get("type") == "video"]
    results = []
    for v in items:
        results.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "author": v.get("uploader"),
            "authorUrl": v.get("uploaderUrl"),
            "thumbnail": (v.get("thumbnail") or (v.get("thumbnails") or [{}])[-1].get("url")),
            "duration": v.get("duration"),
            "views": v.get("views"),
            "uploaded": v.get("uploadedDate"),
            "shortDescription": v.get("shortDescription"),
        })
    return {"items": results, "query": q, "page": page}


@app.get("/api/trending")
def trending(region: str = Query("US", min_length=2, max_length=2)):
    data = fetch_json(f"{PIPED_BASE}/api/v1/trending", params={"region": region})
    items = [i for i in data if i.get("type") == "video"]
    results = []
    for v in items:
        results.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "author": v.get("uploader"),
            "authorUrl": v.get("uploaderUrl"),
            "thumbnail": (v.get("thumbnail") or (v.get("thumbnails") or [{}])[-1].get("url")),
            "duration": v.get("duration"),
            "views": v.get("views"),
            "uploaded": v.get("uploadedDate"),
        })
    return {"items": results, "region": region}


@app.get("/api/related")
def related(id: str = Query(..., min_length=5)):
    data = fetch_json(f"{PIPED_BASE}/api/v1/related", params={"id": id})
    items = [i for i in data if i.get("type") == "video"]
    results = []
    for v in items:
        results.append({
            "id": v.get("id"),
            "title": v.get("title"),
            "author": v.get("uploader"),
            "thumbnail": (v.get("thumbnail") or (v.get("thumbnails") or [{}])[-1].get("url")),
            "duration": v.get("duration"),
            "views": v.get("views"),
        })
    return {"items": results, "id": id}


@app.get("/test")
def test_database():
    """Diagnostics endpoint"""
    response = {
        "backend": "✅ Running",
        "piped": PIPED_BASE,
    }
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
