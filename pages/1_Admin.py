"""
Raayna Enterprises - Admin Dashboard
View, add, edit, delete properties. Drag-and-drop media uploads via Cloudinary.
"""
import streamlit as st
import pandas as pd
from sheets_helper import (
    get_all_rentals, get_all_sales, get_all_leads,
    add_property, delete_property, update_status, update_lead_status,
    upload_to_cloudinary,
)

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Raayna Admin",
    page_icon="🔐",
    layout="wide"
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    .admin-header {
        background: linear-gradient(135deg, #0d2137 0%, #1a365d 60%, #2c5282 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(13,33,55,0.18);
    }
    .admin-header h1 { margin: 0; font-size: 26px; font-weight: 700; }
    .admin-header p { margin: 6px 0 0 0; font-size: 14px; opacity: 0.9; }
    .stat-card {
        background: white; border-radius: 12px; padding: 20px;
        text-align: center; box-shadow: 0 4px 12px rgba(13,33,55,0.08);
        border: 1px solid #e2e8f0;
    }
    .stat-number { font-size: 32px; font-weight: 800; color: #1a365d; margin: 0; }
    .stat-label { font-size: 13px; color: #64748b; margin: 4px 0 0 0;
                  text-transform: uppercase; letter-spacing: 0.5px; }
    .stat-icon { font-size: 28px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="admin-header">
    <h1>🔐 Raayna Admin Dashboard</h1>
    <p>View, add, and manage listings, leads, and customer inquiries</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 4])
with col1:
    st.page_link("app.py", label="← Back to Website")

# ============================================================
# LOAD DATA
# ============================================================
try:
    rentals = get_all_rentals()
    sales = get_all_sales()
    leads = get_all_leads()
except Exception as e:
    st.error(f"❌ Failed to load data: {e}")
    st.stop()

# ============================================================
# STAT CARDS
# ============================================================
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="stat-card"><div class="stat-icon">🏠</div>'
                f'<p class="stat-number">{len(rentals)}</p>'
                f'<p class="stat-label">Rental Listings</p></div>',
                unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card"><div class="stat-icon">🏷️</div>'
                f'<p class="stat-number">{len(sales)}</p>'
                f'<p class="stat-label">Sale Listings</p></div>',
                unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card"><div class="stat-icon">👥</div>'
                f'<p class="stat-number">{len(leads)}</p>'
                f'<p class="stat-label">Customer Leads</p></div>',
                unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# PROPERTY CARD
# ============================================================
def render_property_card(row, listing_type):
    pid = str(row.get("property_id", "")).strip()
    title = row.get("title", "Untitled")
    location = row.get("location", "")
    bhk = row.get("bhk", "")
    amount = row.get("rent", "") if listing_type == "rental" else row.get("price", "")
    amount_label = "Rent" if listing_type == "rental" else "Price"
    status = row.get("status", "")
    owner_name = row.get("owner_name", "")
    owner_phone = row.get("owner_phone", "")

    st.markdown(f"### {pid} — {title}")
    st.markdown(f"**📍 {location}** | 🛏️ {bhk} | 💰 ₹{amount} {amount_label} | Status: `{status}`")

    import re
    image_urls = []
    for k in ["img1", "img2", "img3", "img4", "img5"]:
        url = str(row.get(k, "")).strip()
        if not url:
            continue
        if "drive.google.com" in url:
            m = re.search(r'/d/([A-Za-z0-9_-]{20,})', url) or \
                re.search(r'[?&]id=([A-Za-z0-9_-]{20,})', url)
            if m:
                image_urls.append(
                    f"https://drive.google.com/thumbnail?id={m.group(1)}&sz=w1000"
                )
                continue
        image_urls.append(url)

    if image_urls:
        st.markdown("**📸 Images:**")
        cols = st.columns(min(len(image_urls), 3))
        for i, url in enumerate(image_urls):
            with cols[i % 3]:
                try:
                    st.image(url, use_container_width=True)
                except Exception:
                    st.markdown(f"[Image {i+1}]({url})")

    video_urls = [str(row.get(k, "")).strip()
                  for k in ["vid1", "vid2"]
                  if str(row.get(k, "")).strip()]
    if video_urls:
        st.markdown("**🎥 Videos:**")
        for u in video_urls:
            st.markdown(f"- [Video]({u})")

    if owner_name or owner_phone:
        st.markdown(f"**👤 Owner:** {owner_name} · 📞 {owner_phone}")

    b1, b2, _ = st.columns([1, 1, 3])
    with b1:
        if st.button("🗑️ Delete", key=f"del_{listing_type}_{pid}"):
            try:
                delete_property(listing_type, pid)
                st.success(f"Deleted {pid}")
                st.rerun()
            except Exception as e:
                st.error(f"Delete failed: {e}")
    with b2:
        new_status = "Rented" if status.lower() == "available" else "Available"
        if st.button(f"↔️ Mark {new_status}", key=f"upd_{listing_type}_{pid}"):
            try:
                update_status(listing_type, pid, new_status)
                st.success(f"{pid} → {new_status}")
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")

    st.markdown("---")


# ============================================================
# TABS
# ============================================================
tab1, tab2, tab3 = st.tabs(["🏠 Rentals", "🏷️ Sales", "👥 Leads"])


# ------------------------------------------------------------
# TAB 1: RENTALS
# ------------------------------------------------------------
with tab1:
    st.subheader("Rental Listings")

    with st.expander("➕ Add New Rental Property", expanded=False):
        with st.form("add_rental_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pid = st.text_input("Property ID (e.g., P005)")
                title = st.text_input("Title")
                location = st.text_input("Location (e.g., Kothrud)")
                rent = st.text_input("Monthly Rent (₹)")
                bhk = st.text_input("BHK (e.g., 2BHK)")
            with c2:
                owner_name = st.text_input("Owner Name")
                owner_phone = st.text_input("Owner Phone")

            st.markdown("**📸 Upload Images (drag & drop, up to 5)**")
            uploaded_imgs = st.file_uploader(
                "Drag images here",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                key="r_imgs",
                label_visibility="collapsed"
            )

            st.markdown("**🎥 Upload Videos (drag & drop, up to 2)**")
            uploaded_vids = st.file_uploader(
                "Drag videos here",
                type=["mp4", "mov", "webm"],
                accept_multiple_files=True,
                key="r_vids",
                label_visibility="collapsed"
            )

            submitted = st.form_submit_button("✅ Add Rental")

        if submitted:
            if not pid or not title:
                st.error("Property ID and Title are required.")
            else:
                with st.spinner("Uploading media..."):
                    img_urls = []
                    for f in (uploaded_imgs or [])[:5]:
                        try:
                            img_urls.append(upload_to_cloudinary(f, f"{pid}_{f.name}"))
                        except Exception as e:
                            st.warning(f"Image failed: {e}")
                    vid_urls = []
                    for f in (uploaded_vids or [])[:2]:
                        try:
                            vid_urls.append(upload_to_cloudinary(f, f"{pid}_{f.name}"))
                        except Exception as e:
                            st.warning(f"Video failed: {e}")
                    while len(img_urls) < 5:
                        img_urls.append("")
                    while len(vid_urls) < 2:
                        vid_urls.append("")

                try:
                    add_property("rental", {
                        "property_id": pid, "title": title, "location": location,
                        "rent": rent, "bhk": bhk,
                        "img1": img_urls[0], "img2": img_urls[1],
                        "img3": img_urls[2], "img4": img_urls[3], "img5": img_urls[4],
                        "vid1": vid_urls[0], "vid2": vid_urls[1],
                        "owner_name": owner_name, "owner_phone": owner_phone,
                        "status": "Available"
                    })
                    n_i = len([u for u in img_urls if u])
                    n_v = len([u for u in vid_urls if u])
                    st.success(f"✅ Added {pid} with {n_i} images, {n_v} videos")
                    st.rerun()
                except Exception as e:
                    st.error(f"Add failed: {e}")

    show_available_only = st.checkbox("Show only Available", value=False, key="r_filter")
    filtered = rentals
    if show_available_only:
        filtered = [r for r in rentals
                    if str(r.get("status", "")).lower() == "available"]

    if not filtered:
        st.info("No rentals match the filter.")
    else:
        for row in filtered:
            render_property_card(row, "rental")


# ------------------------------------------------------------
# TAB 2: SALES
# ------------------------------------------------------------
with tab2:
    st.subheader("Sale Listings")

    with st.expander("➕ Add New Sale Property", expanded=False):
        with st.form("add_sale_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                pid_s = st.text_input("Property ID (e.g., S002)")
                title_s = st.text_input("Title")
                location_s = st.text_input("Location")
                price_s = st.text_input("Price (₹)")
                bhk_s = st.text_input("BHK")
            with c2:
                owner_name_s = st.text_input("Owner Name")
                owner_phone_s = st.text_input("Owner Phone")

            st.markdown("**📸 Upload Images (drag & drop, up to 5)**")
            uploaded_imgs_s = st.file_uploader(
                "Drag images here",
                type=["jpg", "jpeg", "png", "webp"],
                accept_multiple_files=True,
                key="s_imgs",
                label_visibility="collapsed"
            )

            st.markdown("**🎥 Upload Videos (drag & drop, up to 2)**")
            uploaded_vids_s = st.file_uploader(
                "Drag videos here",
                type=["mp4", "mov", "webm"],
                accept_multiple_files=True,
                key="s_vids",
                label_visibility="collapsed"
            )

            submitted_s = st.form_submit_button("✅ Add Sale")

        if submitted_s:
            if not pid_s or not title_s:
                st.error("Property ID and Title are required.")
            else:
                with st.spinner("Uploading media..."):
                    img_urls = []
                    for f in (uploaded_imgs_s or [])[:5]:
                        try:
                            img_urls.append(upload_to_cloudinary(f, f"{pid_s}_{f.name}"))
                        except Exception as e:
                            st.warning(f"Image failed: {e}")
                    vid_urls = []
                    for f in (uploaded_vids_s or [])[:2]:
                        try:
                            vid_urls.append(upload_to_cloudinary(f, f"{pid_s}_{f.name}"))
                        except Exception as e:
                            st.warning(f"Video failed: {e}")
                    while len(img_urls) < 5:
                        img_urls.append("")
                    while len(vid_urls) < 2:
                        vid_urls.append("")

                try:
                    add_property("sale", {
                        "property_id": pid_s, "title": title_s, "location": location_s,
                        "price": price_s, "bhk": bhk_s,
                        "img1": img_urls[0], "img2": img_urls[1],
                        "img3": img_urls[2], "img4": img_urls[3], "img5": img_urls[4],
                        "vid1": vid_urls[0], "vid2": vid_urls[1],
                        "owner_name": owner_name_s, "owner_phone": owner_phone_s,
                        "status": "Available"
                    })
                    n_i = len([u for u in img_urls if u])
                    n_v = len([u for u in vid_urls if u])
                    st.success(f"✅ Added {pid_s} with {n_i} images, {n_v} videos")
                    st.rerun()
                except Exception as e:
                    st.error(f"Add failed: {e}")

    show_available_only_s = st.checkbox("Show only Available", value=False, key="s_filter")
    filtered_s = sales
    if show_available_only_s:
        filtered_s = [r for r in sales
                      if str(r.get("status", "")).lower() == "available"]

    if not filtered_s:
        st.info("No sales match the filter.")
    else:
        for row in filtered_s:
            render_property_card(row, "sale")


# ------------------------------------------------------------
# TAB 3: LEADS
# ------------------------------------------------------------
with tab3:
    st.subheader("Customer Leads")

    if not leads:
        st.info("No leads yet.")
    else:
        df = pd.DataFrame(leads)
        if "timestamp" in df.columns:
            df = df.sort_values("timestamp", ascending=False)

        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### Update Lead Status")
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            ts_options = [str(r.get("timestamp", "")) for r in leads]
            selected_ts = st.selectbox("Select lead by timestamp", options=ts_options)
        with c2:
            new_lead_status = st.selectbox(
                "New status",
                options=["New", "Contacted", "Interested",
                         "Visit Booked", "Closed", "Not Interested"]
            )
        with c3:
            if st.button("Update"):
                try:
                    update_lead_status(selected_ts, new_lead_status)
                    st.success("Lead updated.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Update failed: {e}")

        st.caption(f"Total: {len(leads)} leads")