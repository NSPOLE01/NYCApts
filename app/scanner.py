"""
Core scanning logic: fetch new Reddit posts, extract data, save to DB.
"""
import json
import logging
from datetime import datetime, timezone

from .reddit_client import fetch_new_posts
from .extractor import extract_listing_data
from .storage import db, Listing, ScanLog

logger = logging.getLogger(__name__)


def scan_subreddit(subreddit_name: str, max_age_hours: int | None = None) -> dict:
    """
    Scan a subreddit for new apartment listings.
    max_age_hours: if set, skip posts older than this many hours.
    Returns a summary dict with posts_found and new_listings counts.
    """
    log = ScanLog(subreddit=subreddit_name)
    posts_found = 0
    new_listings = 0
    cutoff = None
    if max_age_hours is not None:
        from datetime import timedelta
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    try:
        posts = fetch_new_posts(subreddit_name, limit=100)
        posts_found = len(posts)

        for post in posts:
            # Skip posts outside the requested time window
            if cutoff is not None:
                post_time = datetime.fromtimestamp(post["created_utc"], tz=timezone.utc)
                if post_time < cutoff:
                    continue

            # Skip if we've already seen this post
            if Listing.query.filter_by(reddit_id=post["reddit_id"]).first():
                continue

            # Extract structured data via Claude
            extracted = extract_listing_data(post["title"], post["post_body"])

            listing = Listing(
                reddit_id=post["reddit_id"],
                subreddit=post["subreddit"],
                title=post["title"],
                url=post["url"],
                author=post["author"],
                post_body=post["post_body"],
                created_utc=datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).replace(tzinfo=None),
                photos=json.dumps(post["photos"]),
                price=extracted["price"],
                bedrooms=extracted["bedrooms"],
                bathrooms=extracted["bathrooms"],
                neighborhood=extracted["neighborhood"],
                borough=extracted["borough"],
                amenities=json.dumps(extracted["amenities"]),
                lease_start=extracted["lease_start"],
                lease_end=extracted["lease_end"],
                lease_duration_months=extracted["lease_duration_months"],
                extraction_notes=extracted["extraction_notes"],
            )

            db.session.add(listing)
            new_listings += 1
            logger.info(f"New listing saved: {post['title'][:60]}...")

        db.session.commit()

        log.posts_found = posts_found
        log.new_listings = new_listings

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error scanning r/{subreddit_name}: {e}")
        log.error = str(e)[:500]

    db.session.add(log)
    db.session.commit()

    return {"subreddit": subreddit_name, "posts_found": posts_found, "new_listings": new_listings}


def scan_all(subreddits: list[str], max_age_hours: int | None = None) -> list[dict]:
    """Scan all configured subreddits."""
    results = []
    for subreddit in subreddits:
        logger.info(f"Scanning r/{subreddit} (max_age={max_age_hours}h)...")
        result = scan_subreddit(subreddit, max_age_hours=max_age_hours)
        results.append(result)
        logger.info(f"r/{subreddit}: {result['new_listings']} new listings from {result['posts_found']} posts")
    return results
