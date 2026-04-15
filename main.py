"""
NYC Apt Scanner — entry point.
Scans only when triggered manually via the UI or `python main.py scan`.
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

from app import create_app

app = create_app()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "scan":
        import config
        from app.scanner import scan_all
        with app.app_context():
            print(f"\nScanning: {', '.join(config.SUBREDDITS)}\n")
            results = scan_all(config.SUBREDDITS)
            for r in results:
                print(f"  r/{r['subreddit']}: {r['new_listings']} new / {r['posts_found']} seen")
            total = sum(r["new_listings"] for r in results)
            print(f"\nDone. {total} new listings saved.\n")
    else:
        print("\nNYC Apt Scanner running at http://localhost:5000")
        print("Use the 'Scan Now' button in the UI to fetch new listings.\n")
        app.run(debug=False, port=5000, use_reloader=False)
