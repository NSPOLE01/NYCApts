"""
Reddit client using the public JSON API — no app registration or OAuth required.
Reddit exposes /r/<subreddit>/new.json publicly for any subreddit.
"""
import time
import requests

# Reddit requires a descriptive User-Agent to avoid 429s
HEADERS = {
    "User-Agent": "NYCAptScanner/1.0 (personal apartment search tool)"
}

_session = requests.Session()
_session.headers.update(HEADERS)

REDDIT_BASE = "https://www.reddit.com"


def fetch_new_posts(subreddit_name: str, limit: int = 100) -> list[dict]:
    """
    Fetch the newest posts from a subreddit using Reddit's public JSON API.
    Returns a list of normalized post dicts.
    """
    posts = []
    after = None
    page_size = min(limit, 100)  # Reddit max per request is 100

    while len(posts) < limit:
        params = {"limit": page_size, "raw_json": 1}
        if after:
            params["after"] = after

        url = f"{REDDIT_BASE}/r/{subreddit_name}/new.json"
        resp = _session.get(url, params=params, timeout=15)

        if resp.status_code == 429:
            # Rate limited — back off and retry once
            time.sleep(5)
            resp = _session.get(url, params=params, timeout=15)

        resp.raise_for_status()
        data = resp.json()

        children = data.get("data", {}).get("children", [])
        if not children:
            break

        for child in children:
            post = child.get("data", {})
            photos = _extract_photos(post)

            posts.append({
                "reddit_id": post.get("id"),
                "subreddit": subreddit_name,
                "title": post.get("title", ""),
                "url": f"{REDDIT_BASE}{post.get('permalink', '')}",
                "author": post.get("author", "[deleted]"),
                "post_body": post.get("selftext", ""),
                "created_utc": post.get("created_utc", 0),
                "photos": photos,
            })

        after = data.get("data", {}).get("after")
        if not after or len(posts) >= limit:
            break

        # Polite crawl delay between pages
        time.sleep(1)

    return posts[:limit]


def _extract_photos(post: dict) -> list[str]:
    """Pull image URLs from a post — handles galleries, direct images, and previews."""
    photos = []

    # Gallery posts (multiple images)
    media_metadata = post.get("media_metadata")
    if media_metadata:
        for item in media_metadata.values():
            if item.get("e") == "Image" and "s" in item:
                url = item["s"].get("u", "").replace("&amp;", "&")
                if url:
                    photos.append(url)
        return photos

    # Single direct image URL
    post_url = post.get("url", "")
    if any(post_url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")):
        return [post_url]

    # Reddit-hosted preview image (most self-posts with images)
    preview = post.get("preview", {})
    images = preview.get("images", [])
    if images:
        source = images[0].get("source", {})
        url = source.get("url", "").replace("&amp;", "&")
        if url:
            photos.append(url)

    return photos
