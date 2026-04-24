"""
Uses Claude to extract structured apartment data from a Reddit post.
"""
import json
import re
import anthropic
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


EXTRACTION_PROMPT = """\
You are a data extraction assistant for NYC apartment listings scraped from Reddit.

Given the title and body of a Reddit post, extract the following fields as JSON.
Return ONLY valid JSON — no markdown, no explanation.

Fields to extract:
- post_type (string): Either "listing" (someone offering/renting out an apartment or room) or "seeking" (someone looking for an apartment, room, or roommate). This is the most important field — read carefully.
- price (integer): Monthly rent in USD. null if not found.
- bedrooms (number): Number of bedrooms. Use 0 for studio. null if not found.
- bathrooms (number): Number of bathrooms (can be 0.5 increments). null if not found.
- neighborhood (string): The neighborhood name (e.g. "Astoria", "Crown Heights", "LES"). null if not found.
- borough (string): One of "Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island". null if not found.
- amenities (array of strings): List of amenities mentioned (e.g. ["doorman", "gym", "laundry in building", "dishwasher", "pets ok", "outdoor space"]). Empty array if none.
- lease_start (string): Lease start date as mentioned (e.g. "June 1", "2024-06-01", "ASAP"). null if not found.
- lease_end (string): Lease end date as mentioned. null if not found.
- lease_duration_months (integer): Lease duration in months (e.g. 12 for a 1-year lease). null if not found.
- gender_preference (string): Gender preference for the roommate or tenant. Use exactly one of: "female", "male", "non-binary", "any". Default to "any" if not mentioned.
- notes (string): Any important caveats or additional info (broker fee, no-fee, flex rooms, guarantors, budget, etc.). null if none.

Post title: {title}

Post body:
{body}
"""


def extract_listing_data(title: str, body: str) -> dict:
    """
    Call Claude to extract structured apartment data from a post.
    Returns a dict with the extracted fields (all may be None if not found).
    """
    prompt = EXTRACTION_PROMPT.format(title=title, body=body[:4000])

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()

        # Strip any accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        data = json.loads(raw)
        raw_type = _clean_str(data.get("post_type")) or "listing"
        post_type = "seeking" if "seek" in raw_type.lower() else "listing"
        raw_gender = (_clean_str(data.get("gender_preference")) or "any").lower()
        if "female" in raw_gender or "woman" in raw_gender or "women" in raw_gender:
            gender_preference = "female"
        elif "male" in raw_gender or "man" in raw_gender or "men" in raw_gender:
            gender_preference = "male"
        elif "non" in raw_gender or "enby" in raw_gender:
            gender_preference = "non-binary"
        else:
            gender_preference = "any"
        return {
            "post_type": post_type,
            "gender_preference": gender_preference,
            "price": _to_int(data.get("price")),
            "bedrooms": _to_float(data.get("bedrooms")),
            "bathrooms": _to_float(data.get("bathrooms")),
            "neighborhood": _clean_str(data.get("neighborhood")),
            "borough": _clean_str(data.get("borough")),
            "amenities": data.get("amenities") if isinstance(data.get("amenities"), list) else [],
            "lease_start": _clean_str(data.get("lease_start")),
            "lease_end": _clean_str(data.get("lease_end")),
            "lease_duration_months": _to_int(data.get("lease_duration_months")),
            "extraction_notes": _clean_str(data.get("notes")),
        }

    except (json.JSONDecodeError, anthropic.APIError, Exception) as e:
        # Return empty extraction with error note rather than crashing
        return {
            "post_type": "listing",
            "gender_preference": "any",
            "price": None,
            "bedrooms": None,
            "bathrooms": None,
            "neighborhood": None,
            "borough": None,
            "amenities": [],
            "lease_start": None,
            "lease_end": None,
            "lease_duration_months": None,
            "extraction_notes": f"Extraction error: {str(e)[:200]}",
        }


def _to_int(val):
    try:
        return int(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _to_float(val):
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def _clean_str(val):
    if val is None:
        return None
    s = str(val).strip()
    return s if s and s.lower() not in ("null", "none", "n/a", "") else None
