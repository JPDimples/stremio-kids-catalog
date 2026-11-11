# Kids Only — kids-safe Stremio catalogs

A Stremio addon with four kids-safe catalogs, built from TMDB data. No adult
content, no config, no accounts needed to use it.

## Install

In Stremio, open this link (or paste the manifest URL into Addons):

    stremio://raw.githubusercontent.com/JPDimples/stremio-kids-catalog/main/manifest.json

Manifest: `https://raw.githubusercontent.com/JPDimples/stremio-kids-catalog/main/manifest.json`

## Catalogs

| Catalog | Type | Rule (US ratings — the most complete in TMDB) |
|---|---|---|
| Kids Movies | movie | Certified G |
| Family Movies | movie | Certified PG |
| Kids Shows | series | TV-Y / TV-Y7 / TV-G |
| Family Shows | series | TV-PG |

Each catalog holds the 100 most popular matching titles with IMDb ids, so
Stremio resolves posters/details through Cinemeta and streams through
whatever stream addons you already have. This addon serves catalogs only —
it provides no meta and no streams itself.

## Honest limits

- **This is a safe shelf, not parental controls.** Stremio addons cannot
  PIN-lock anything or hide your other addons/catalogs. A child can still
  open other catalogs in Stremio. For real locking, use a dedicated kids
  profile in your streaming apps or device-level controls.
- Ratings are US (G/PG/TV-Y/TV-G/TV-PG). Canadian ratings differ slightly;
  the titles are the same family films and shows.
- Stream availability depends on your own Stremio addons — this addon only
  lists what to watch, it does not provide the video.

## How it stays fresh

`scripts/build_catalogs.py` rebuilds the catalogs from TMDB weekly
(Sundays 06:00 EST) via GitHub Actions, plus on demand from the Actions tab.
It uses only the Python standard library.

## Setup (for the repo owner)

The build needs a free TMDB API key — TMDB data is free, the key just
identifies the app:

1. Create a free account at https://www.themoviedb.org/signup, then open
   https://www.themoviedb.org/settings/api and copy the **API Key (v3 auth)**.
2. In this repo: **Settings → Secrets and variables → Actions → New
   repository secret**, name `TMDB_API_KEY`, value the key from step 1.
3. **Actions → Rebuild catalogs → Run workflow** to build the catalogs the
   first time. After that it rebuilds itself weekly.

To build locally instead: `TMDB_API_KEY=... python3 scripts/build_catalogs.py`.
