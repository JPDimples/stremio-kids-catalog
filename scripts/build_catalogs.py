#!/usr/bin/env python3
"""Build the Kids Only Stremio addon catalogs from TMDB (free API key required).

Catalogs (US ratings — the most complete in TMDB):
  movie  kids-movies    certification G       (100 most popular)
  movie  family-movies  certification PG      (100 most popular)
  series kids-shows     TV-Y / TV-Y7 / TV-G   (100 most popular)
  series family-shows   TV-PG                 (100 most popular)

Only items with an IMDb id (tt...) and a poster are kept, so Stremio can
resolve meta through Cinemeta and streams through the user's own addons.
This addon serves catalogs ONLY (resources: ["catalog"]) — no meta, no streams.

Pagination: Stremio keeps requesting pages while they come back non-empty,
advancing skip by the number received; a short page is NOT the last one and
a 404 is not an empty page. So every catalog also ships skip=0 (full page)
and skip=100 (empty array) files.

Usage:  TMDB_API_KEY=... python3 scripts/build_catalogs.py
Output: catalog/{type}/{id}.json + skip variants, under the repo root.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://api.themoviedb.org/3"
IMG = "https://image.tmdb.org/t/p/w500"
OUT = Path(__file__).resolve().parent.parent
KEY = os.environ.get("TMDB_API_KEY", "")
PER_PAGE = 20
TARGET = 100

MOVIE_CATALOGS = [
    ("kids-movies", "G"),
    ("family-movies", "PG"),
]
TV_CATALOGS = [
    ("kids-shows", "10762", {"TV-Y", "TV-Y7", "TV-G"}),
    ("family-shows", "10751", {"TV-PG"}),
]


def get_json(path, params):
    params = dict(params)
    params["api_key"] = KEY
    params["language"] = "en-US"
    url = BASE + path + "?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 2:
                time.sleep(5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"GET {path} failed after retries")


def rate_limited():
    time.sleep(0.25)


def poster(path):
    return IMG + path if path else None


def movie_meta(d):
    if not d.get("imdb_id") or not d.get("poster_path"):
        return None
    return {
        "id": d["imdb_id"],
        "type": "movie",
        "name": d.get("title") or d.get("original_title"),
        "poster": poster(d["poster_path"]),
        "posterShape": "poster",
        "releaseInfo": (d.get("release_date") or "")[:4],
        "genres": [g["name"] for g in d.get("genres", [])][:3],
    }


def tv_meta(d):
    ext = d.get("external_ids") or {}
    if not ext.get("imdb_id") or not d.get("poster_path"):
        return None
    return {
        "id": ext["imdb_id"],
        "type": "series",
        "name": d.get("name") or d.get("original_name"),
        "poster": poster(d["poster_path"]),
        "posterShape": "poster",
        "releaseInfo": (d.get("first_air_date") or "")[:4],
        "genres": [g["name"] for g in d.get("genres", [])][:3],
    }


def us_tv_rating(d):
    ratings = (d.get("content_ratings") or {}).get("results", [])
    for r in ratings:
        if r.get("iso_3166_1") == "US":
            return r.get("rating")
    return None


def build_movies(catalog_id, certification):
    metas, seen = [], set()
    page = 1
    while len(metas) < TARGET and page <= 8:
        res = get_json("/discover/movie", {
            "certification_country": "US",
            "certification": certification,
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "vote_count.gte": 50,
            "page": page,
        })
        rate_limited()
        for item in res.get("results", []):
            if len(metas) >= TARGET:
                break
            d = get_json(f"/movie/{item['id']}", {})
            rate_limited()
            m = movie_meta(d)
            if m and m["id"] not in seen:
                seen.add(m["id"])
                metas.append(m)
        page += 1
    return metas


def build_tv(catalog_id, genre_id, allowed_ratings):
    metas, seen = [], set()
    page = 1
    while len(metas) < TARGET and page <= 10:
        res = get_json("/discover/tv", {
            "with_genres": genre_id,
            "sort_by": "popularity.desc",
            "include_adult": "false",
            "page": page,
        })
        rate_limited()
        for item in res.get("results", []):
            if len(metas) >= TARGET:
                break
            d = get_json(f"/tv/{item['id']}", {
                "append_to_response": "external_ids,content_ratings",
            })
            rate_limited()
            if us_tv_rating(d) not in allowed_ratings:
                continue
            m = tv_meta(d)
            if m and m["id"] not in seen:
                seen.add(m["id"])
                metas.append(m)
        page += 1
    return metas


def write_catalog(ctype, catalog_id, metas):
    d = OUT / "catalog" / ctype
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{catalog_id}.json").write_text(json.dumps({"metas": metas}, indent=1))
    sub = d / catalog_id
    sub.mkdir(parents=True, exist_ok=True)
    (sub / "skip=0.json").write_text(json.dumps({"metas": metas}, indent=1))
    (sub / "skip=100.json").write_text(json.dumps({"metas": []}, indent=1))
    print(f"  {ctype}/{catalog_id}: {len(metas)} items")


def main():
    if not KEY:
        print("TMDB_API_KEY is not set. Get a free key at https://www.themoviedb.org/settings/api")
        return 1
    print("Building Kids Only catalogs from TMDB...")
    for catalog_id, cert in MOVIE_CATALOGS:
        write_catalog("movie", catalog_id, build_movies(catalog_id, cert))
    for catalog_id, genre_id, ratings in TV_CATALOGS:
        write_catalog("series", catalog_id, build_tv(catalog_id, genre_id, ratings))
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
