"""
Raayna Enterprises - Complete Website + Embedded Chatbot
Single-page: hero, services, why-us, embedded chatbot, contact.
"""
import re
import streamlit as st
from chatbot import chat

# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="Raayna Enterprises | Property Management Pune",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# CUSTOM CSS
# ============================================================
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .block-container {
        padding-top: 0.5rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }

    /* TOP NAV */
    .topnav {
        background: linear-gradient(135deg, #0d2137 0%, #1a365d 60%, #2c5282 100%);
        padding: 14px 28px;
        border-radius: 12px;
        color: white;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(13,33,55,0.18);
    }
    .topnav .brand { font-size: 20px; font-weight: 700; letter-spacing: 0.3px; }
    .topnav .brand span { color: #d4a843; }
    .topnav .nav-links { font-size: 14px; opacity: 0.9; }

    /* HERO */
    .hero {
        background: linear-gradient(135deg, rgba(13,33,55,0.9) 0%, rgba(44,82,130,0.85) 100%),
                    url("https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=1600&q=80");
        background-size: cover;
        background-position: center;
        padding: 70px 40px;
        border-radius: 16px;
        text-align: center;
        color: white;
        margin-bottom: 36px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    .hero h1 {
        font-size: 44px; font-weight: 800; margin: 0 0 16px 0;
        line-height: 1.15; letter-spacing: -0.5px;
    }
    .hero .subtitle { font-size: 19px; opacity: 0.95; margin-bottom: 10px; }
    .hero .tagline {
        font-size: 15px; color: #d4a843; font-weight: 600;
        letter-spacing: 1.2px; margin-bottom: 0;
    }

    /* SECTION HEADINGS */
    .section-title {
        font-size: 30px; font-weight: 700; color: #0d2137;
        text-align: center; margin: 40px 0 6px 0;
    }
    .section-subtitle {
        font-size: 15px; color: #64748b; text-align: center;
        margin-bottom: 30px;
    }

    /* SERVICE CARDS */
    .service-card {
        background: white; border-radius: 14px; padding: 24px 20px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(13,33,55,0.08);
        border: 1px solid #e2e8f0;
        transition: all 0.25s ease;
        height: 190px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .service-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 28px rgba(13,33,55,0.14);
        border-color: #d4a843;
    }
    .service-icon { font-size: 36px; margin-bottom: 10px; }
    .service-title {
        font-size: 15px; font-weight: 700; color: #1a365d;
        margin: 0 0 6px 0;
    }
    .service-desc { font-size: 13px; color: #64748b; margin: 0; line-height: 1.5; }

    /* TRUST CARDS */
    .trust-card {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-left: 4px solid #d4a843;
        padding: 18px 22px; border-radius: 10px; margin-bottom: 14px;
    }
    .trust-card strong { color: #0d2137; font-size: 15px; }
    .trust-card p { margin: 4px 0 0 0; color: #4a5568; font-size: 13.5px; }

    /* CHAT SECTION */
    .chat-section {
        background: linear-gradient(135deg, #0d2137 0%, #1a365d 60%, #2c5282 100%);
        border-radius: 16px;
        padding: 28px 24px;
        margin-top: 40px;
        box-shadow: 0 8px 24px rgba(13,33,55,0.18);
        text-align: center;
    }
    .chat-title {
        font-size: 26px; font-weight: 700; color: #ffffff !important;
        text-align: center; margin: 0 0 6px 0;
    }
    .chat-sub {
        text-align: center; color: #d4a843 !important;
        font-size: 14px; font-weight: 500; margin: 0;
    }

    /* Chat bubbles */
    .stChatMessage {
        border-radius: 14px !important;
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    .stChatMessage p, .stChatMessage div, .stChatMessage span {
        color: #1a365d !important;
    }

    /* Buttons */
    .stButton button {
        border-radius: 20px !important;
        border: 1.5px solid #2c5282 !important;
        background: white !important;
        color: #1a365d !important;
        font-weight: 500 !important;
        padding: 6px 14px !important;
    }
    .stButton button:hover {
        background: #2c5282 !important;
        color: white !important;
    }

    /* Chat input */
    .stChatInput input {
        border-radius: 24px !important;
        border: 1.5px solid #cbd5e0 !important;
        padding: 12px 18px !important;
        background-color: #ffffff !important;
        color: #1a365d !important;
    }
    .stChatInput input::placeholder { color: #94a3b8 !important; }

    /* CONTACT */
    .contact-card {
        background: linear-gradient(135deg, #0d2137 0%, #1a365d 100%);
        border-radius: 16px; padding: 36px 30px;
        color: white; text-align: center; margin-top: 40px;
    }
    .contact-card h2 { margin: 0 0 10px 0; font-size: 26px; }
    .contact-item { font-size: 16px; margin: 10px 0; color: #e2e8f0; }
    .contact-item a { color: #d4a843; text-decoration: none; font-weight: 600; }
    .contact-item a:hover { text-decoration: underline; }

    /* FOOTER */
    .footer {
        text-align: center; padding: 28px 0 10px 0;
        color: #94a3b8; font-size: 13px;
        border-top: 1px solid #e2e8f0; margin-top: 40px;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# TOP NAV
# ============================================================
st.markdown("""
<div class="topnav">
    <div class="brand">🏢 Raayna <span>Enterprises</span></div>
    <div class="nav-links">Property Management • Pune</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================
st.markdown("""
<div class="hero">
    <h1>Professional Property Management<br>in Pune</h1>
    <p class="subtitle">We manage your property — so you don't have to.</p>
    <p class="tagline">YOUR PROPERTY, OUR PRIORITY</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SERVICES
# ============================================================
st.markdown('<h2 class="section-title">Our Services</h2>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">End-to-end property management, handled professionally</p>', unsafe_allow_html=True)

row1 = st.columns(3)
services_row1 = [
    ("🏠", "Property Marketing", "We market your property to the right tenants & buyers."),
    ("👥", "Tenant Management", "Background checks, agreements, and ongoing support."),
    ("🔧", "Maintenance & Repairs", "Trusted vendors, quality work, fair pricing."),
]
for col, (icon, title, desc) in zip(row1, services_row1):
    with col:
        st.markdown(f"""
        <div class="service-card">
            <div class="service-icon">{icon}</div>
            <div class="service-title">{title}</div>
            <p class="service-desc">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

row2 = st.columns(3)
services_row2 = [
    ("💰", "Rent Collection", "On-time collection with transparent accounting."),
    ("🔍", "Property Inspection", "Regular checks with photo & video reports."),
    ("🎁", "Free Consultation", "Talk to us — no obligation, no cost."),
]
for col, (icon, title, desc) in zip(row2, services_row2):
    with col:
        st.markdown(f"""
        <div class="service-card">
            <div class="service-icon">{icon}</div>
            <div class="service-title">{title}</div>
            <p class="service-desc">{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# WHY CHOOSE US
# ============================================================
st.markdown('<h2 class="section-title">Why Choose Raayna?</h2>', unsafe_allow_html=True)
st.markdown('<p class="section-subtitle">Trusted by owners in Pune and abroad</p>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)
with col_left:
    st.markdown("""
    <div class="trust-card">
        <strong>✅ Local Pune Expertise</strong>
        <p>Deep knowledge of Kothrud, Baner, Wakad, Hadapsar, Aundh, Hinjewadi and more.</p>
    </div>
    <div class="trust-card">
        <strong>🌍 NRI-Friendly Service</strong>
        <p>Remote owners get regular updates, reports, and video walkthroughs.</p>
    </div>
    """, unsafe_allow_html=True)
with col_right:
    st.markdown("""
    <div class="trust-card">
        <strong>📊 Transparent Reporting</strong>
        <p>Clear records of every rupee collected, spent, and deposited.</p>
    </div>
    <div class="trust-card">
        <strong>🤝 End-to-End Management</strong>
        <p>From finding tenants to handling repairs — we do it all.</p>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# EMBEDDED CHATBOT
# ============================================================
st.markdown("""
<div class="chat-section">
    <h2 class="chat-title">💬 Chat With Raayna Assistant</h2>
    <p class="chat-sub">Ask about properties, book a consultation, or list your property — instantly.</p>
</div>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Welcome + quick replies
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="🏢"):
        st.markdown(
            "**Namaste! 🙏 Welcome to Raayna Enterprises.**\n\n"
            "I help property owners in Pune manage their properties "
            "hassle-free — whether you're local or abroad.\n\n"
            "How can I help you today?"
        )

    st.markdown("##### Quick options:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 I own a property", use_container_width=True, key="q1"):
            st.session_state.messages.append({
                "role": "user",
                "content": "I own a property and want property management services"
            })
            st.rerun()
        if st.button("🌍 I'm an NRI owner", use_container_width=True, key="q2"):
            st.session_state.messages.append({
                "role": "user",
                "content": "I am an NRI owner living abroad and need help managing my Pune property"
            })
            st.rerun()
    with col2:
        if st.button("🔍 Looking for rental", use_container_width=True, key="q3"):
            st.session_state.messages.append({
                "role": "user",
                "content": "I am looking for a rental property in Pune"
            })
            st.rerun()
        if st.button("📞 Free consultation", use_container_width=True, key="q4"):
            st.session_state.messages.append({
                "role": "user",
                "content": "I want to book a free consultation"
            })
            st.rerun()

# Chat history
for message in st.session_state.messages:
    avatar = "🏢" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🏢"):
        with st.spinner("Thinking..."):
            history_for_bot = st.session_state.messages[:-1]
            response = chat(prompt, history_for_bot)
            st.markdown(response)

            # ---- Detect Google Drive image URLs and render as thumbnails ----
            img_pattern = r'https://drive\.google\.com/(?:file/d/|uc\?export=view&id=|thumbnail\?id=)([A-Za-z0-9_-]{20,})'
            found_ids = re.findall(img_pattern, response)

            # Remove duplicates, keep order
            seen = set()
            unique_ids = []
            for fid in found_ids:
                if fid not in seen:
                    seen.add(fid)
                    unique_ids.append(fid)

            if unique_ids:
                st.markdown("### 📸 Property Images")
                num_cols = 3
                for row_start in range(0, len(unique_ids[:5]), num_cols):
                    cols = st.columns(num_cols)
                    for i, file_id in enumerate(unique_ids[row_start:row_start + num_cols]):
                        thumb_url = f"https://drive.google.com/thumbnail?id={file_id}&sz=w1000"
                        with cols[i]:
                            st.image(thumb_url, use_container_width=True)

    st.session_state.messages.append({"role": "assistant", "content": response})

# ============================================================
# CONTACT
# ============================================================
st.markdown("""
<div class="contact-card">
    <h2>Get In Touch</h2>
    <p style="opacity:0.85; margin-bottom:20px;">We respond within 24 hours</p>
    <p class="contact-item">📞 <a href="tel:+917773933417">7773933417</a> &nbsp;|&nbsp; <a href="tel:+917378567707">7378567707</a></p>
    <p class="contact-item">📧 <a href="mailto:raaynaenterprises@gmail.com">raaynaenterprises@gmail.com</a></p>
    <p class="contact-item">🌐 <a href="https://www.raaynaenterprises.in" target="_blank">raaynaenterprises.in</a></p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.markdown("""
<div class="footer">
    © 2026 Raayna Enterprises — Professional Property Management, Pune<br>
    <em>Your Property, Our Priority</em>
</div>
""", unsafe_allow_html=True)