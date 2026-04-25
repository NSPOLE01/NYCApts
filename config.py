import os
from dotenv import load_dotenv

load_dotenv()

SUBREDDITS = [
    s.strip()
    for s in os.getenv("SUBREDDITS", "LeaseTakeoverNYC,NYCapartments,NYCroommates").split(",")
    if s.strip()
]

SCAN_INTERVAL_HOURS = int(os.getenv("SCAN_INTERVAL_HOURS", "4"))

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nyc_apts.db")
