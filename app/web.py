"""
Flask routes for the NYC Apartments web UI.
"""
from flask import Blueprint, render_template, request, jsonify, current_app
from .storage import db, Listing, ScanLog
import config

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # Filters from query params
    borough = request.args.get("borough", "")
    min_price = request.args.get("min_price", type=int)
    max_price = request.args.get("max_price", type=int)
    min_beds = request.args.get("min_beds", type=float)
    max_beds = request.args.get("max_beds", type=float)
    subreddit = request.args.get("subreddit", "")
    sort = request.args.get("sort", "newest")

    def apply_filters(query):
        if borough:
            query = query.filter(Listing.borough == borough)
        if min_price is not None:
            query = query.filter(Listing.price >= min_price)
        if max_price is not None:
            query = query.filter(Listing.price <= max_price)
        if min_beds is not None:
            query = query.filter(Listing.bedrooms >= min_beds)
        if max_beds is not None:
            query = query.filter(Listing.bedrooms <= max_beds)
        if subreddit:
            query = query.filter(Listing.subreddit == subreddit)
        if sort == "price_asc":
            query = query.order_by(Listing.price.asc().nulls_last())
        elif sort == "price_desc":
            query = query.order_by(Listing.price.desc().nulls_last())
        else:
            query = query.order_by(Listing.scraped_at.desc())
        return query

    listings = apply_filters(
        Listing.query.filter(Listing.post_type == "listing")
    ).limit(200).all()

    seekers = apply_filters(
        Listing.query.filter(Listing.post_type == "seeking")
    ).limit(200).all()

    # Stats
    total = Listing.query.count()
    last_scan = ScanLog.query.order_by(ScanLog.scanned_at.desc()).first()

    return render_template(
        "index.html",
        listings=listings,
        seekers=seekers,
        total=total,
        last_scan=last_scan,
        subreddits=config.SUBREDDITS,
        boroughs=["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"],
        filters={
            "borough": borough,
            "min_price": min_price,
            "max_price": max_price,
            "min_beds": min_beds,
            "max_beds": max_beds,
            "subreddit": subreddit,
            "sort": sort,
        },
    )


@bp.route("/listing/<int:listing_id>")
def listing_detail(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    return render_template("listing.html", listing=listing.to_dict())


@bp.route("/api/scan", methods=["POST"])
def trigger_scan():
    """Manually trigger a scan (called from the UI).
    Optional JSON body: {"max_age_hours": 24}
    """
    from .scanner import scan_all
    try:
        body = request.get_json(silent=True) or {}
        max_age_hours = body.get("max_age_hours")  # None means no time filter
        results = scan_all(config.SUBREDDITS, max_age_hours=max_age_hours)
        total_new = sum(r["new_listings"] for r in results)
        return jsonify({"ok": True, "results": results, "total_new": total_new})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@bp.route("/api/listings")
def api_listings():
    listings = Listing.query.order_by(Listing.scraped_at.desc()).limit(100).all()
    return jsonify([l.to_dict() for l in listings])


@bp.route("/api/stats")
def api_stats():
    total = Listing.query.count()
    last_scan = ScanLog.query.order_by(ScanLog.scanned_at.desc()).first()
    return jsonify({
        "total_listings": total,
        "last_scan": last_scan.scanned_at.isoformat() if last_scan else None,
        "subreddits": config.SUBREDDITS,
        "scan_interval_hours": config.SCAN_INTERVAL_HOURS,
    })
