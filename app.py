import streamlit as st
import os
from dotenv import load_dotenv
from PIL import Image
from models.gemini_reader import read_bill_gemini
from utils.bill_parser import (
    validate_bill_data,
    calculate_split,
    format_currency
)
import tempfile

# =====================================================
# LOAD ENV
# =====================================================

from pathlib import Path

env_path = Path(__file__).parent / ".env"

load_dotenv(dotenv_path=env_path)

API_KEY = os.getenv("GEMINI_API_KEY", "")


# DEBUG
print("DEBUG API KEY:", API_KEY)

# =====================================================
# STREAMLIT CONFIG
# =====================================================

st.set_page_config(
    page_title="SmartSplit Bill AI",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* ── Main background ── */
    .stApp {
        background: #0f1117;
    }

    /* ── Hero header ── */
    .hero {
        background: linear-gradient(135deg, #6c63ff 0%, #3ecfcf 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(108, 99, 255, 0.35);
    }
    .hero h1 {
        font-size: 2.4rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0 0 0.5rem 0;
        letter-spacing: -0.5px;
    }
    .hero p {
        font-size: 1rem;
        color: rgba(255,255,255,0.85);
        margin: 0;
    }

    /* ── Section card ── */
    .section-card {
        background: #1a1d2e;
        border: 1px solid rgba(108, 99, 255, 0.2);
        border-radius: 16px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1.25rem;
    }
    .section-title {
        font-size: 1.05rem;
        font-weight: 600;
        color: #c8c8ff;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }

    /* ── Item row ── */
    .item-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.65rem 0.9rem;
        border-radius: 10px;
        background: #12151f;
        margin-bottom: 0.5rem;
        border: 1px solid rgba(255,255,255,0.05);
        transition: background 0.2s;
    }
    .item-row:hover { background: #1e2236; }
    .item-name { font-weight: 500; color: #e2e2f0; font-size: 0.92rem; }
    .item-qty  { color: #8888aa; font-size: 0.85rem; }
    .item-price { font-weight: 600; color: #7ee8a2; font-size: 0.92rem; }

    /* ── Summary block ── */
    .summary-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        color: #b0b0cc;
        font-size: 0.9rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .summary-row:last-child { border-bottom: none; }
    .summary-total {
        display: flex;
        justify-content: space-between;
        padding: 0.8rem 0 0 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
    }

    /* ── Person card ── */
    .person-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background: rgba(108, 99, 255, 0.18);
        border: 1px solid rgba(108, 99, 255, 0.4);
        border-radius: 25px;
        padding: 0.35rem 0.9rem;
        font-size: 0.85rem;
        font-weight: 500;
        color: #c8c8ff;
        margin: 0.2rem;
    }

    /* ── Result card ── */
    .result-card {
        background: linear-gradient(135deg, #1a1d2e, #22253a);
        border: 1px solid rgba(126, 232, 162, 0.25);
        border-radius: 14px;
        padding: 1.1rem 1.4rem;
        margin-bottom: 0.75rem;
    }
    .result-name { font-size: 0.9rem; color: #8888aa; margin-bottom: 0.25rem; }
    .result-amount { font-size: 1.6rem; font-weight: 700; color: #7ee8a2; }
    .result-pct { font-size: 0.8rem; color: #5555aa; margin-top: 0.15rem; }

    /* ── Status pills ── */
    .pill-ok {
        background: rgba(126,232,162,0.15);
        border: 1px solid rgba(126,232,162,0.4);
        color: #7ee8a2;
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.82rem;
        font-weight: 600;
    }
    .pill-warn {
        background: rgba(255,190,90,0.15);
        border: 1px solid rgba(255,190,90,0.4);
        color: #ffbe5a;
        border-radius: 20px;
        padding: 0.25rem 0.85rem;
        font-size: 0.82rem;
        font-weight: 600;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #13162b !important;
        border-right: 1px solid rgba(108,99,255,0.15);
    }
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #c8c8ff;
    }

    /* ── Streamlit overrides ── */
    div[data-testid="stMetricValue"] { color: #7ee8a2 !important; font-size: 1rem !important; }
    div[data-testid="stMetricDelta"] { color: #8888aa !important; }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6c63ff, #3ecfcf) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        letter-spacing: 0.3px !important;
        transition: opacity 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover { opacity: 0.88 !important; }
    .stButton > button {
        border-radius: 10px !important;
        background: #1e2236 !important;
        border: 1px solid rgba(108,99,255,0.3) !important;
        color: #c8c8ff !important;
    }
    .stButton > button:hover {
        border-color: #6c63ff !important;
        color: #ffffff !important;
    }
    .stFileUploader {
        background: #1a1d2e;
        border-radius: 14px;
        border: 2px dashed rgba(108,99,255,0.35);
        padding: 1rem;
    }
    .stTextInput > div > input,
    .stMultiSelect > div {
        background: #12151f !important;
        border: 1px solid rgba(108,99,255,0.3) !important;
        border-radius: 10px !important;
        color: #e2e2f0 !important;
    }
    hr { border-color: rgba(108,99,255,0.15) !important; }
    .stAlert { border-radius: 10px !important; }
    .stExpander { background: #1a1d2e; border-radius: 12px; border: 1px solid rgba(108,99,255,0.15); }
    p, li { color: #c0c0d8; }
</style>
""", unsafe_allow_html=True)

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🧾 SmartSplit Bill AI</h1>
    <p>Upload foto nota, biarkan AI membacanya — lalu split tagihan otomatis ke semua orang.</p>
</div>
""", unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
for key, default in {
    "bill_data": None,
    "participants": [],
    "item_assignments": {},
    "split_result": None,
    "uploaded_image": None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Panel Kontrol")
    st.divider()

    # API key status (no input shown)
    if API_KEY:
        st.markdown('<span class="pill-ok">🔑 API Key Terhubung</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="pill-warn">⚠️ API Key Tidak Ditemukan</span>', unsafe_allow_html=True)
        st.caption("Buat file `.env` dan isi `GEMINI_API_KEY=...`")

    st.divider()

    # Progress tracker
    st.markdown("### 📋 Progress")
    steps = {
        "1. Upload Nota": st.session_state.uploaded_image is not None,
        "2. Baca dengan AI": st.session_state.bill_data is not None,
        "3. Tambah Peserta": len(st.session_state.participants) > 0,
        "4. Assign Item": any(
            len(v) > 0 for v in st.session_state.item_assignments.values()
        ),
        "5. Hitung Split": st.session_state.split_result is not None,
    }
    for label, done in steps.items():
        icon = "✅" if done else "⬜"
        st.markdown(f"{icon} {label}")

    st.divider()

    if st.session_state.bill_data is not None:
        bill = st.session_state.bill_data
        currency = bill.get("currency", "IDR")
        st.markdown("### 📊 Info Nota")
        st.metric("Total Bill", format_currency(bill.get("total", 0), currency))
        st.metric("Jumlah Item", len(bill.get("items", [])))
        st.metric("⚡ Inference", f"{bill.get('inference_time', 0):.2f}s")
        st.divider()

    if st.button("🔄 Reset Semua", use_container_width=True):
        for key in ["bill_data", "participants", "item_assignments", "split_result", "uploaded_image"]:
            st.session_state[key] = [] if key == "participants" else ({} if key == "item_assignments" else None)
        st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# STEP 1 — UPLOAD
# ════════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-card"><div class="section-title">📸 Step 1 — Upload Foto Nota</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "Drag & drop atau klik untuk memilih foto nota",
    type=["jpg", "jpeg", "png"],
    help="Pastikan foto cukup terang dan fokus untuk hasil terbaik.",
    label_visibility="collapsed",
)

if uploaded_file:
    st.session_state.uploaded_image = uploaded_file
    col_img, col_info = st.columns([1, 1], gap="large")

    with col_img:
        image = Image.open(uploaded_file)
        st.image(image, caption="Foto yang diupload", use_container_width=True)

    with col_info:
        st.markdown(f"""
        <div class="item-row">
            <span class="item-name">📄 Nama File</span>
            <span class="item-price">{uploaded_file.name}</span>
        </div>
        <div class="item-row">
            <span class="item-name">📦 Ukuran</span>
            <span class="item-price">{uploaded_file.size / 1024:.1f} KB</span>
        </div>
        <div class="item-row">
            <span class="item-name">🖼️ Dimensi</span>
            <span class="item-price">{image.width} × {image.height} px</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("🤖 Baca Nota dengan AI", type="primary", use_container_width=True):
            if not API_KEY:
                st.error("⚠️ `GEMINI_API_KEY` tidak ditemukan di file `.env`. Tambahkan dulu ya!")
            else:
                with st.spinner("AI sedang menganalisis nota... ✨"):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                            tmp.write(uploaded_file.getvalue())
                            tmp_path = tmp.name

                        bill_data = read_bill_gemini(tmp_path, API_KEY)
                        os.unlink(tmp_path)

                        is_valid, errors = validate_bill_data(bill_data)
                        if is_valid:
                            st.session_state.bill_data = bill_data
                            st.session_state.split_result = None
                            st.success("✅ Nota berhasil dibaca!")
                            st.rerun()
                        else:
                            st.error("❌ Data dari AI tidak lengkap:")
                            for err in errors:
                                st.write(f"• {err}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2 — HASIL BACAAN AI
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.bill_data is not None:
    bill     = st.session_state.bill_data
    currency = bill.get("currency", "IDR")

    st.markdown('<div class="section-card"><div class="section-title">📋 Step 2 — Hasil Bacaan AI</div>', unsafe_allow_html=True)

    # Item table header
    cols = st.columns([4, 1, 2, 2])
    for col, label in zip(cols, ["Nama Item", "Qty", "Harga Satuan", "Total"]):
        col.markdown(f"<span style='color:#5555aa;font-size:0.78rem;font-weight:600;text-transform:uppercase;'>{label}</span>", unsafe_allow_html=True)

    for item in bill.get("items", []):
        c1, c2, c3, c4 = st.columns([4, 1, 2, 2])
        c1.markdown(f"<span class='item-name'>{item.get('name', '—')}</span>", unsafe_allow_html=True)
        c2.markdown(f"<span class='item-qty'>×{item.get('quantity', 1)}</span>", unsafe_allow_html=True)
        c3.markdown(f"<span style='color:#c0c0d8;font-size:0.9rem;'>{format_currency(item.get('price_per_item', 0), currency)}</span>", unsafe_allow_html=True)
        c4.markdown(f"<span class='item-price'>{format_currency(item.get('total_price', 0), currency)}</span>", unsafe_allow_html=True)

    st.divider()

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("<span style='color:#8888aa;font-size:0.85rem;font-weight:600;'>RINGKASAN</span>", unsafe_allow_html=True)
        rows_html = f"<div class='summary-row'><span>Subtotal</span><span>{format_currency(bill.get('subtotal', 0), currency)}</span></div>"
        for charge in bill.get("additional_charges", []):
            rows_html += f"<div class='summary-row'><span>{charge.get('name','Charge')}</span><span>{format_currency(charge.get('amount', 0), currency)}</span></div>"
        rows_html += f"<div class='summary-total'><span>Total</span><span>{format_currency(bill.get('total', 0), currency)}</span></div>"
        st.markdown(rows_html, unsafe_allow_html=True)

    with col_right:
        st.markdown("<span style='color:#8888aa;font-size:0.85rem;font-weight:600;'>MODEL INFO</span>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="item-row" style="margin-top:0.5rem;">
            <span class="item-name">🤖 Model</span>
            <span class="item-price">{bill.get('model_used', 'Gemini')}</span>
        </div>
        <div class="item-row">
            <span class="item-name">⚡ Inference</span>
            <span class="item-price">{bill.get('inference_time', 0):.2f} detik</span>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("🔍 Lihat Raw JSON dari AI"):
        st.json(bill)

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3 — TAMBAH PESERTA
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.bill_data is not None:

    st.markdown('<div class="section-card"><div class="section-title">👥 Step 3 — Tambah Peserta</div>', unsafe_allow_html=True)

    col_in, col_btn = st.columns([4, 1], gap="small")
    with col_in:
        new_name = st.text_input(
            "Nama peserta",
            placeholder="Ketik nama lalu klik Tambah...",
            label_visibility="collapsed",
        )
    with col_btn:
        if st.button("➕ Tambah", use_container_width=True):
            name = new_name.strip()
            if not name:
                st.warning("Nama tidak boleh kosong.")
            elif name in st.session_state.participants:
                st.warning("Nama sudah ada!")
            else:
                st.session_state.participants.append(name)
                st.rerun()

    if st.session_state.participants:
        st.markdown("<br>", unsafe_allow_html=True)
        badges_html = ""
        for p in st.session_state.participants:
            badges_html += f"<span class='person-badge'>👤 {p}</span>"
        st.markdown(badges_html, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cols_del = st.columns(len(st.session_state.participants))
        for i, (col, person) in enumerate(zip(cols_del, st.session_state.participants)):
            with col:
                if st.button(f"❌ {person}", key=f"del_{i}", use_container_width=True):
                    st.session_state.participants.pop(i)
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4 — ASSIGN ITEM
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.bill_data is not None and len(st.session_state.participants) > 0:

    st.markdown('<div class="section-card"><div class="section-title">🔀 Step 4 — Assign Item ke Peserta</div>', unsafe_allow_html=True)
    st.caption("Pilih siapa saja yang ikut bayar tiap item. Jika lebih dari satu orang, biaya dibagi rata.")

    bill     = st.session_state.bill_data
    currency = bill.get("currency", "IDR")

    for i, item in enumerate(bill.get("items", [])):
        item_name  = item.get("name", f"Item {i+1}")
        item_total = item.get("total_price", 0)

        col_label, col_select = st.columns([2, 3], gap="medium")
        with col_label:
            st.markdown(
                f"<div class='item-row'><span class='item-name'>{item_name}</span>"
                f"<span class='item-price'>{format_currency(item_total, currency)}</span></div>",
                unsafe_allow_html=True
            )
        with col_select:
            selected = st.multiselect(
                "Peserta",
                options=st.session_state.participants,
                key=f"assign_{i}",
                label_visibility="collapsed",
                placeholder="Pilih peserta...",
            )
            st.session_state.item_assignments[i] = selected

    st.markdown("</div>", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5 — HITUNG SPLIT
# ════════════════════════════════════════════════════════════════════════════════
if st.session_state.bill_data is not None and len(st.session_state.participants) > 0:

    st.markdown('<div class="section-card">', unsafe_allow_html=True)

    if st.button("💰 Hitung Split Tagihan!", type="primary", use_container_width=True):
        bill  = st.session_state.bill_data
        items = bill.get("items", [])

        unassigned = [
            items[i].get("name", f"Item {i+1}")
            for i in range(len(items))
            if i not in st.session_state.item_assignments
            or len(st.session_state.item_assignments[i]) == 0
        ]

        if unassigned:
            st.warning(f"⚠️ Item belum di-assign: **{', '.join(unassigned)}**")
        else:
            st.session_state.split_result = calculate_split(
                bill, st.session_state.item_assignments
            )

    # ── Results ──────────────────────────────────────────────────────────────
    if st.session_state.split_result is not None:
        bill       = st.session_state.bill_data
        currency   = bill.get("currency", "IDR")
        total_bill = float(bill.get("total", 0))
        split      = st.session_state.split_result

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">🎯 Hasil Split Tagihan</div>', unsafe_allow_html=True)

        result_cols = st.columns(max(1, min(len(split), 3)))
        for col, (person, amount) in zip(result_cols * 10, split.items()):
            pct = (amount / total_bill * 100) if total_bill > 0 else 0
            with col:
                st.markdown(f"""
                <div class="result-card">
                    <div class="result-name">👤 {person}</div>
                    <div class="result-amount">{format_currency(amount, currency)}</div>
                    <div class="result-pct">{pct:.1f}% dari total tagihan</div>
                </div>
                """, unsafe_allow_html=True)

        st.divider()

        grand_total = sum(split.values())
        col_v1, col_v2, col_v3 = st.columns(3)

        with col_v1:
            st.metric("📊 Total Bill", format_currency(total_bill, currency))
        with col_v2:
            st.metric("🧮 Total Terhitung", format_currency(grand_total, currency))
        with col_v3:
            diff = abs(grand_total - total_bill)
            if diff < 1:
                st.markdown('<span class="pill-ok">✅ Total Cocok</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="pill-warn">⚠️ Selisih {format_currency(diff, currency)}</span>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)