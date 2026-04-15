import os
from dotenv import load_dotenv

load_dotenv()

# Subreddits to scan
SUBREDDITS = [
    s.strip()
    for s in os.getenv("SUBREDDITS", "LeaseTakeoverNYC,NYCapartments,NYCroommates").split(",")
    if s.strip()
]

# Scanning
SCAN_INTERVAL_HOURS = int(os.getenv("SCAN_INTERVAL_HOURS", "4"))

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Flask
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nyc_apts.db")
