from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Listing(db.Model):
    __tablename__ = "listings"

    id = db.Column(db.Integer, primary_key=True)
    reddit_id = db.Column(db.String(20), unique=True, nullable=False, index=True)
    subreddit = db.Column(db.String(100), nullable=False)
    title = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100))
    post_body = db.Column(db.Text)
    created_utc = db.Column(db.DateTime)
    scraped_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Extracted fields
    post_type = db.Column(db.String(10), default="listing")  # "listing" or "seeking"
    is_new = db.Column(db.Boolean, default=True, nullable=False)
    price = db.Column(db.Integer)              # monthly rent in USD
    bedrooms = db.Column(db.Float)             # 0 = studio
    bathrooms = db.Column(db.Float)
    neighborhood = db.Column(db.String(200))
    borough = db.Column(db.String(50))
    amenities = db.Column(db.Text)             # JSON list
    photos = db.Column(db.Text)               # JSON list of URLs
    lease_start = db.Column(db.String(50))
    lease_end = db.Column(db.String(50))
    lease_duration_months = db.Column(db.Integer)
    extraction_notes = db.Column(db.Text)     # anything the extractor flagged

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "reddit_id": self.reddit_id,
            "subreddit": self.subreddit,
            "title": self.title,
            "url": self.url,
            "author": self.author,
            "created_utc": self.created_utc.isoformat() if self.created_utc else None,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "post_type": self.post_type or "listing",
            "price": self.price,
            "bedrooms": self.bedrooms,
            "bathrooms": self.bathrooms,
            "neighborhood": self.neighborhood,
            "borough": self.borough,
            "amenities": json.loads(self.amenities) if self.amenities else [],
            "photos": json.loads(self.photos) if self.photos else [],
            "lease_start": self.lease_start,
            "lease_end": self.lease_end,
            "lease_duration_months": self.lease_duration_months,
            "extraction_notes": self.extraction_notes,
        }


class ScanLog(db.Model):
    __tablename__ = "scan_logs"

    id = db.Column(db.Integer, primary_key=True)
    subreddit = db.Column(db.String(100))
    scanned_at = db.Column(db.DateTime, default=datetime.utcnow)
    posts_found = db.Column(db.Integer, default=0)
    new_listings = db.Column(db.Integer, default=0)
    error = db.Column(db.Text)
