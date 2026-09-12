"""
Google Sheets helper for Raayna Chatbot.
Handles empty columns, duplicate headers, and flexible Sheet layouts.
"""
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

SHEET_NAME = "Pune_RealEstate_DB"


# ============================================================
# GOOGLE SHEETS CORE
# ============================================================

def _get_client():
    """Connect to Google Sheets (Streamlit secrets first, then local file)."""
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    try:
        import streamlit as st
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    except Exception:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "service_account.json", scope
        )
    return gspread.authorize(creds)


def _open_sheet():
    return _get_client().open(SHEET_NAME)


def _get_records(worksheet):
    """
    Read all rows from a worksheet WITHOUT using get_all_records()
    (which breaks on duplicate/empty headers).

    - Skips blank header columns
    - Renames duplicate headers as name_1, name_2
    - Skips fully empty rows
    """
    all_values = worksheet.get_all_values()
    if not all_values:
        return []

    raw_headers = all_values[0]
    headers = []
    seen = set()

    for h in raw_headers:
        key = str(h).strip()
        if not key:
            headers.append(None)
            continue
        original = key
        counter = 1
        while key in seen:
            key = f"{original}_{counter}"
            counter += 1
        seen.add(key)
        headers.append(key)

    records = []
    for row in all_values[1:]:
        if not any(str(cell).strip() for cell in row):
            continue
        record = {}
        for idx, cell in enumerate(row):
            if idx >= len(headers):
                break
            key = headers[idx]
            if key is None:
                continue
            record[key] = cell
        records.append(record)

    return records


def _normalize_bhk(value):
    text = str(value).lower()
    digits = re.findall(r'\d+', text)
    if digits and "bhk" in text:
        return f"{digits[0]}bhk"
    return text.replace(" ", "").replace("-", "").strip()


def _normalize_location(value):
    text = str(value).lower()
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = text.split(",")[0]
    return text.replace(" ", "").strip()


# ============================================================
# COLUMN DEFINITIONS
# ============================================================

RENTAL_COLS = [
    "property_id", "title", "location", "rent", "bhk",
    "img1", "img2", "img3", "img4", "img5",
    "vid1", "vid2", "owner_name", "owner_phone", "status"
]

SALE_COLS = [
    "property_id", "title", "location", "price", "bhk",
    "img1", "img2", "img3", "img4", "img5",
    "vid1", "vid2", "owner_name", "owner_phone", "status"
]

LEAD_COLS = ["timestamp", "name", "phone", "intent", "details", "status"]


# ============================================================
# SEARCH TOOLS
# ============================================================

def search_rentals(location: str = "", bhk: str = "", max_rent: str = ""):
    """
    Search rental properties by location, BHK, and max rent.
    Returns matching available rentals.
    """
    sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    rows = _get_records(sheet)

    matches = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "available":
            continue
        if location:
            loc_clean = _normalize_location(location)
            row_loc = _normalize_location(row.get("location", ""))
            row_title = _normalize_location(row.get("title", ""))
            if loc_clean not in row_loc and loc_clean not in row_title:
                continue
        if bhk:
            if _normalize_bhk(bhk) not in _normalize_bhk(row.get("bhk", "")):
                continue
        if max_rent:
            try:
                if int(row.get("rent", 0)) > int(str(max_rent).strip()):
                    continue
            except (ValueError, TypeError):
                pass
        matches.append(row)
    return matches


def search_sales(location: str = "", bhk: str = "", max_price: str = ""):
    """
    Search properties for sale by location, BHK, and max price.
    Returns matching available sales.
    """
    sheet = _open_sheet().worksheet("SALE_LISTINGS")
    rows = _get_records(sheet)

    matches = []
    for row in rows:
        if str(row.get("status", "")).strip().lower() != "available":
            continue
        if location:
            loc_clean = _normalize_location(location)
            row_loc = _normalize_location(row.get("location", ""))
            row_title = _normalize_location(row.get("title", ""))
            if loc_clean not in row_loc and loc_clean not in row_title:
                continue
        if bhk:
            if _normalize_bhk(bhk) not in _normalize_bhk(row.get("bhk", "")):
                continue
        if max_price:
            try:
                if int(row.get("price", 0)) > int(str(max_price).strip()):
                    continue
            except (ValueError, TypeError):
                pass
        matches.append(row)
    return matches


def save_lead(name: str = "", phone: str = "", intent: str = "", details: str = ""):
    """Save a customer lead to LEADS tab."""
    sheet = _open_sheet().worksheet("LEADS")
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        name, phone, intent, details, "New"
    ])
    return f"Lead saved for {name} ({phone})."


def get_property_media(property_id: str = ""):
    """
    Get all images and videos for a specific property.
    property_id: 'P001' (rental) or 'S001' (sale).
    """
    pid = str(property_id).strip().upper()
    if not pid:
        return {"error": "No property_id provided."}

    match = None

    sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    for row in _get_records(sheet):
        if str(row.get("property_id", "")).strip().upper() == pid:
            match = row
            break

    if not match:
        sheet = _open_sheet().worksheet("SALE_LISTINGS")
        for row in _get_records(sheet):
            if str(row.get("property_id", "")).strip().upper() == pid:
                match = row
                break

    if not match:
        return {"error": f"No property found with id {pid}"}

    images = [str(match.get(k, "")).strip()
              for k in ["img1", "img2", "img3", "img4", "img5"]
              if str(match.get(k, "")).strip()]
    videos = [str(match.get(k, "")).strip()
              for k in ["vid1", "vid2"]
              if str(match.get(k, "")).strip()]

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


# ============================================================
# ADMIN: READ
# ============================================================

def get_all_rentals():
    sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    return _get_records(sheet)


def get_all_sales():
    sheet = _open_sheet().worksheet("SALE_LISTINGS")
    return _get_records(sheet)


def get_all_leads():
    sheet = _open_sheet().worksheet("LEADS")
    return _get_records(sheet)


# ============================================================
# ADMIN: WRITE
# ============================================================

def add_property(listing_type: str, data: dict):
    """Add a new property to RENTAL_LISTINGS or SALE_LISTINGS."""
    if listing_type == "rental":
        sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
        cols = RENTAL_COLS
    else:
        sheet = _open_sheet().worksheet("SALE_LISTINGS")
        cols = SALE_COLS

    row = [str(data.get(col, "")) for col in cols]
    sheet.append_row(row)
    return f"Added {data.get('property_id', '')}."


def delete_property(listing_type: str, property_id: str):
    """Delete a property row by property_id."""
    pid = str(property_id).strip().upper()
    if listing_type == "rental":
        sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    else:
        sheet = _open_sheet().worksheet("SALE_LISTINGS")

    all_values = sheet.get_all_values()
    for idx, row in enumerate(all_values):
        if idx == 0:
            continue
        if row and str(row[0]).strip().upper() == pid:
            sheet.delete_rows(idx + 1)
            return f"Deleted {pid}."
    return f"{pid} not found."


def update_status(listing_type: str, property_id: str, new_status: str):
    """Update the status column of a property."""
    pid = str(property_id).strip().upper()
    if listing_type == "rental":
        sheet = _open_sheet().worksheet("RENTAL_LISTINGS")
    else:
        sheet = _open_sheet().worksheet("SALE_LISTINGS")

    all_values = sheet.get_all_values()
    header = [str(h).strip() for h in all_values[0]]
    try:
        status_col = header.index("status") + 1
    except ValueError:
        return "Status column not found."

    for idx, row in enumerate(all_values):
        if idx == 0:
            continue
        if row and str(row[0]).strip().upper() == pid:
            sheet.update_cell(idx + 1, status_col, new_status)
            return f"{pid} -> {new_status}."
    return f"{pid} not found."


def update_lead_status(timestamp: str, new_status: str):
    """Update a lead's status."""
    sheet = _open_sheet().worksheet("LEADS")
    all_values = sheet.get_all_values()
    header = [str(h).strip() for h in all_values[0]]
    try:
        status_col = header.index("status") + 1
    except ValueError:
        return "Status column not found."

    for idx, row in enumerate(all_values):
        if idx == 0:
            continue
        if row and str(row[0]).strip() == str(timestamp).strip():
            sheet.update_cell(idx + 1, status_col, new_status)
            return "Lead updated."
    return "Lead not found."


# ============================================================
# CLOUDINARY UPLOAD
# ============================================================
import cloudinary
import cloudinary.uploader

_cloudinary_configured = False


def _configure_cloudinary():
    global _cloudinary_configured
    if _cloudinary_configured:
        return

    cloud_name = api_key = api_secret = None

    try:
        import streamlit as st
        cloud_name = st.secrets.get("CLOUDINARY_CLOUD_NAME")
        api_key = st.secrets.get("CLOUDINARY_API_KEY")
        api_secret = st.secrets.get("CLOUDINARY_API_SECRET")
    except Exception:
        pass

    if not cloud_name:
        import os
        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
        api_key = os.getenv("CLOUDINARY_API_KEY")
        api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not cloud_name or not api_key or not api_secret:
        raise RuntimeError(
            "Cloudinary credentials missing. Add CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET to .env or secrets."
        )

    cloudinary.config(
        cloud_name=cloud_name, api_key=api_key, api_secret=api_secret, secure=True,
    )
    _cloudinary_configured = True


def upload_to_cloudinary(file_obj, filename: str, folder: str = "raayna/properties"):
    """Upload a file from st.file_uploader to Cloudinary. Returns secure URL."""
    _configure_cloudinary()
    safe_name = re.sub(r'[^A-Za-z0-9_.-]', '_', str(filename))
    result = cloudinary.uploader.upload(
        file_obj, folder=folder, public_id=safe_name,
        resource_type="auto", overwrite=True,
    )
    return result.get("secure_url", "")


# ---- Quick test ----
if __name__ == "__main__":
    print("Testing connection...\n")
    r = get_all_rentals()
    s = get_all_sales()
    l = get_all_leads()
    print(f"Rentals: {len(r)}")
    for row in r[:3]:
        print(f"  - {row.get('property_id')}: {row.get('title')} ({row.get('location')}) - Rs {row.get('rent')}")
    print(f"\nSales: {len(s)}")
    for row in s[:3]:
        print(f"  - {row.get('property_id')}: {row.get('title')}")
    print(f"\nLeads: {len(l)}")