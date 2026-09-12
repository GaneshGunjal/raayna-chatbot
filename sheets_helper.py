"""
Google Sheets helper for Raayna Chatbot.
Reads properties from RENTAL_LISTINGS / SALE_LISTINGS tabs.
Writes leads to LEADS tab.
"""
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SHEET_NAME = "Pune_RealEstate_DB"


def _get_client():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "service_account.json", scope
    )
    return gspread.authorize(creds)


def _open_sheet():
    return _get_client().open(SHEET_NAME)


def _clean_headers(rows):
    """Strip leading/trailing spaces from all header keys."""
    return [
        {str(k).strip(): v for k, v in row.items()}
        for row in rows
    ]


def _normalize_bhk(value):
    text = str(value).lower()
    digits = re.findall(r'\d+', text)
    has_bhk = "bhk" in text
    if digits and has_bhk:
        return f"{digits[0]}bhk"
    return text.replace(" ", "").replace("-", "").strip()


def _normalize_location(value):
    text = str(value).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = text.split(",")[0]
    return text.replace(" ", "").strip()


# ---- TOOL 1: Search rentals ----
def search_rentals(location: str = "", bhk: str = "", max_rent: str = ""):
    """
    Search rental properties in Pune by location, BHK, and maximum rent.
    Returns matching available rental properties with title, location, rent,
    BHK, amenities, and image links. Use this whenever a customer asks about
    rentals or says "show me properties for rent".
    """
    sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    rows = _clean_headers(sheet.get_all_records())

    matches = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "available":
            continue

        if location:
            loc_clean = _normalize_location(location)
            row_loc_clean = _normalize_location(row.get("location", ""))
            if loc_clean not in row_loc_clean:
                continue

        if bhk:
            bhk_clean = _normalize_bhk(bhk)
            row_bhk_clean = _normalize_bhk(row.get("bhk", ""))
            if bhk_clean not in row_bhk_clean:
                continue

        if max_rent:
            try:
                rent = int(row.get("rent", 0))
                if rent > int(str(max_rent).strip()):
                    continue
            except (ValueError, TypeError):
                pass

        matches.append(row)

    return matches


# ---- TOOL 2: Search sales ----
def search_sales(location: str = "", bhk: str = "", max_price: str = ""):
    """
    Search properties for sale in Pune by location, BHK, and maximum price.
    Returns matching available sale properties with title, location, price,
    BHK, amenities, and image links.
    """
    sheet = _open_sheet().worksheet("SALE_LISTINGS")
    rows = _clean_headers(sheet.get_all_records())

    matches = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "available":
            continue

        if location:
            loc_clean = _normalize_location(location)
            row_loc_clean = _normalize_location(row.get("location", ""))
            if loc_clean not in row_loc_clean:
                continue

        if bhk:
            bhk_clean = _normalize_bhk(bhk)
            row_bhk_clean = _normalize_bhk(row.get("bhk", ""))
            if bhk_clean not in row_bhk_clean:
                continue

        if max_price:
            try:
                price = int(row.get("price", 0))
                if price > int(str(max_price).strip()):
                    continue
            except (ValueError, TypeError):
                pass

        matches.append(row)

    return matches


# ---- TOOL 3: Save lead ----
def save_lead(name: str = "", phone: str = "", intent: str = "", details: str = ""):
    """
    Save a customer lead to the LEADS tab.
    intent: 'rental_inquiry', 'sale_inquiry', 'owner_inquiry',
    'nri_inquiry', or 'consultation_request'.
    Call this when a customer shares their name AND phone number.
    """
    sheet = _open_sheet().worksheet("LEADS")
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        name,
        phone,
        intent,
        details,
        "New"
    ])
    return f"Lead saved for {name} ({phone})."


# ---- TOOL 4: Get property media (images + videos) ----
def get_property_media(property_id: str = ""):
    """
    Get all images and videos for a specific property by property_id.
    Returns title, location, bhk, rent/price, image URLs, and video URLs.
    property_id format: 'P001' for rentals or 'S001' for sales.
    Call this whenever a customer asks for photos, images, or videos.
    """
    pid = str(property_id).strip().upper()
    if not pid:
        return {"error": "No property_id provided. Ask the customer which property they mean."}

    match = None

    # Try rentals first
    sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    for row in _clean_headers(sheet.get_all_records()):
        if str(row.get("property_id", "")).strip().upper() == pid:
            match = row
            break

    # If not found, try sales
    if not match:
        sheet = _open_sheet().worksheet("SALE_LISTINGS")
        for row in _clean_headers(sheet.get_all_records()):
            if str(row.get("property_id", "")).strip().upper() == pid:
                match = row
                break

    if not match:
        return {"error": f"No property found with id {pid}"}

    images = []
    for key in ["img1", "img2", "img3", "img4", "img5"]:
        url = str(match.get(key, "")).strip()
        if url:
            images.append(url)

    videos = []
    for key in ["vid1", "vid2"]:
        url = str(match.get(key, "")).strip()
        if url:
            videos.append(url)

    return {
        "property_id": pid,
        "title": match.get("title", ""),
        "location": match.get("location", ""),
        "bhk": match.get("bhk", ""),
        "rent": match.get("rent", ""),
        "price": match.get("price", ""),
        "images": images,
        "videos": videos,
    }


# ---- Quick test ----
if __name__ == "__main__":
    print("Testing Google Sheets connection...\n")

    print("All rentals:")
    for p in search_rentals():
        print(f"  - {p['title']} ({p['location']}) - Rs {p['rent']}")

    print("\nRentals in Kothrud 2BHK:")
    for p in search_rentals(location="Kothrud", bhk="2 BHK"):
        print(f"  - {p['title']} ({p['location']}) - Rs {p['rent']}")

    print("\nMedia for P001:")
    media = get_property_media("P001")
    print(f"  Title: {media.get('title')}")
    print(f"  Images: {len(media.get('images', []))}")
    print(f"  Videos: {len(media.get('videos', []))}")