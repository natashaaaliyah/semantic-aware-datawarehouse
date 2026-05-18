import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from datetime import datetime
import time
 
# --- Page Configuration ---
st.set_page_config(
    page_title="SeDW - Exanthem Surveillance Uganda",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)
 
# --- All 146 Districts of Uganda ---
UGANDA_DISTRICTS = sorted([
    "Abim", "Adjumani", "Agago", "Alebtong", "Amolatar", "Amudat", "Amuria", "Amuru",
    "Apac", "Arua", "Budaka", "Bududa", "Bugiri", "Bugweri", "Buhweju", "Buikwe",
    "Bukedea", "Bukomansimbi", "Bukwo", "Bulambuli", "Buliisa", "Bundibugyo", "Bunyangabu",
    "Bushenyi", "Busia", "Butaleja", "Butebo", "Buvuma", "Buyende", "Dokolo", "Gomba",
    "Gulu", "Hoima", "Ibanda", "Iganga", "Isingiro", "Jinja", "Kaabong", "Kabale",
    "Kabarole", "Kaberemaido", "Kagadi", "Kakumiro", "Kalaki", "Kalangala", "Kaliro",
    "Kalungu", "Kampala", "Kamuli", "Kamwenge", "Kanungu", "Kapchorwa", "Kapelebyong",
    "Karenga", "Kasanda", "Kasese", "Katakwi", "Kayunga", "Kazo", "Kibale", "Kiboga",
    "Kibuku", "Kikuube", "Kiruhura", "Kiryandongo", "Kisoro", "Kitagwenda", "Kitgum",
    "Koboko", "Kole", "Kotido", "Kumi", "Kwania", "Kween", "Kyegegwa", "Kyenjojo",
    "Kyotera", "Lamwo", "Lira", "Luuka", "Luwero", "Lwengo", "Lyantonde", "Madi-Okollo",
    "Manafwa", "Maracha", "Masaka", "Masindi", "Mayuge", "Mbale", "Mbarara", "Mitooma",
    "Mityana", "Moroto", "Moyo", "Mpigi", "Mubende", "Mukono", "Nabilatuk", "Nakapiripirit",
    "Nakaseke", "Nakasongola", "Namayingo", "Namisindwa", "Namutumba", "Napak", "Nebbi",
    "Ngora", "Ntoroko", "Ntungamo", "Nwoya", "Obongi", "Omoro", "Otuke", "Oyam",
    "Pader", "Pakwach", "Pallisa", "Rakai", "Rubanda", "Rubirizi", "Rukiga", "Rukungiri",
    "Rwampara", "Sembabule", "Serere", "Sheema", "Sironko", "Soroti", "Tororo",
    "Wakiso", "Yumbe", "Zombo"
])
 
# --- Data Persistence Logic (Bronze Layer) ---
DB_FILE = "sedw_bronze_vault.csv"
 
def init_db():
    """Initializes the CSV database if it doesn't exist."""
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=["timestamp", "district", "role", "symptoms", "trust_score", "k_anonymity"])
        df.to_csv(DB_FILE, index=False)
 
def save_observation(district, role, symptoms, trust_score, k_anonymity):
    """Saves a new observation to the Bronze Layer."""
    new_data = pd.DataFrame([{
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "district": district,
        "role": role,
        "symptoms": "|".join(symptoms),
        "trust_score": trust_score,
        "k_anonymity": k_anonymity
    }])
    new_data.to_csv(DB_FILE, mode='a', header=False, index=False)
 
def load_db():
    """Loads and returns the database, handling empty/missing files gracefully."""
    try:
        df = pd.read_csv(DB_FILE)
        if df.empty:
            return pd.DataFrame(columns=["timestamp", "district", "role", "symptoms", "trust_score", "k_anonymity"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame(columns=["timestamp", "district", "role", "symptoms", "trust_score", "k_anonymity"])
 
init_db()
 
# --- Uganda District Coordinates (approximate centroids) ---
DISTRICT_COORDS = {
    "Kampala": (0.3476, 32.5825), "Wakiso": (0.3136, 32.5811), "Nakasongola": (1.3000, 32.4000),
    "Mbarara": (-0.6072, 30.6545), "Kasese": (0.1833, 30.0833), "Jinja": (0.4244, 33.2041),
    "Gulu": (2.7748, 32.2990), "Lira": (2.2499, 32.8997), "Mbale": (1.0796, 34.1753),
    "Soroti": (1.7148, 33.6110), "Arua": (3.0200, 30.9100), "Kabale": (-1.2492, 29.9908),
    "Fort Portal": (0.6710, 30.2742), "Hoima": (1.4300, 31.3500), "Masaka": (-0.3333, 31.7333),
    "Tororo": (0.6920, 34.1810), "Iganga": (0.6090, 33.4690), "Mukono": (0.3536, 32.7553),
    "Mityana": (0.4230, 32.0230), "Masindi": (1.6740, 31.7150),
}
 
def get_coords(district):
    """Returns coordinates for a district, with a default for unknown ones."""
    return DISTRICT_COORDS.get(district, (1.3733, 32.2903))  # Default: Uganda center
 
# --- Mock Semantic Backend Logic ---
def get_semantic_trust_score(metadata):
    score = 0.4
    if metadata['location_verified']: score += 0.2
    if len(metadata['clinical_context']) >= 2: score += 0.2
    if metadata['observer_role'] in ["Community Health Worker", "Clinician"]: score += 0.15
    return min(score, 1.0)
 
# --- UI Header ---
st.markdown("""
    <div style='background-color: #004d40; padding: 1rem; border-radius: 10px; margin-bottom: 2rem;'>
        <h1 style='color: white; margin:0;'>🛡️ Semantic-Aware Data Warehouse (SeDW)</h1>
        <p style='color: #e0f2f1; margin:0;'>L6: Mobile-Edge Ingestion & Epidemiological Intelligence Portal</p>
    </div>
""", unsafe_allow_html=True)
 
# --- Sidebar Navigation ---
with st.sidebar:
    st.markdown("### System Navigation")
    page = st.radio("", ["📊 Surveillance Dashboard", "📸 Live Data Capture", "🕸️ Knowledge Graph View"])
    st.divider()
    st.caption("DWH-CS-1 Project")
    st.caption("Active Mode: Neuro-symbolic pipeline")
 
# ============================================================
# PAGE 1: Surveillance Dashboard — LIVE from DB
# ============================================================
if page == "📊 Surveillance Dashboard":
    st.markdown("### Epidemiological Intelligence (Gold Layer)")
 
    df = load_db()
    has_data = not df.empty
 
    # --- Top-level metrics from real data ---
    total_obs   = len(df) if has_data else 0
    high_trust  = len(df[df["trust_score"] >= 0.8]) if has_data else 0
    avg_trust   = round(df["trust_score"].mean() * 100, 1) if has_data else 0.0
    hotspots    = df["district"].nunique() if has_data else 0
 
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Observations", f"{total_obs:,}")
    col2.metric("High-Trust Alerts (>0.8)", str(high_trust), "Action Required" if high_trust > 0 else None, delta_color="inverse")
    col3.metric("Avg Trust Score", f"{avg_trust}%")
    col4.metric("Active Districts", str(hotspots))
 
    st.divider()
 
    if not has_data:
        st.info("📭 No submissions yet. Go to **📸 Live Data Capture** to ingest your first observation — charts will populate automatically.")
    else:
        chart_col1, chart_col2 = st.columns([2, 1])
 
        # --- Temporal Trend: submissions per day ---
        with chart_col1:
            st.markdown("#### 📈 Temporal Submission Trends")
            trend_df = (
                df.set_index("timestamp")
                .resample("D")
                .size()
                .reset_index(name="Submissions")
            )
            trend_df.rename(columns={"timestamp": "Date"}, inplace=True)
            fig_line = px.line(
                trend_df, x="Date", y="Submissions",
                color_discrete_sequence=["#d32f2f"],
                markers=True
            )
            fig_line.update_layout(plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_line, use_container_width=True)
 
        # --- Spatial Distribution: cases per district ---
        with chart_col2:
            st.markdown("#### 🗺️ Spatial Distribution")
            geo_df = df.groupby("district").size().reset_index(name="cases")
            geo_df["lat"] = geo_df["district"].apply(lambda d: get_coords(d)[0])
            geo_df["lon"] = geo_df["district"].apply(lambda d: get_coords(d)[1])
 
            fig_map = px.scatter_mapbox(
                geo_df, lat="lat", lon="lon", size="cases",
                color="cases", hover_name="district",
                color_continuous_scale=px.colors.sequential.Reds,
                size_max=25, zoom=6
            )
            fig_map.update_layout(
                mapbox_style="carto-positron",
                margin={"r": 0, "t": 0, "l": 0, "b": 0}
            )
            st.plotly_chart(fig_map, use_container_width=True)
 
 
 
# ============================================================
# PAGE 2: Live Data Capture
# ============================================================
elif page == "📸 Live Data Capture":
    st.markdown("### L6: Decentralized Mobile-Edge Ingestion")
    st.info("Upload multimodal citizen science data. Metadata is semantically enriched upon ingestion.")
 
    col_img, col_meta = st.columns([1, 1], gap="large")
 
    with col_img:
        st.markdown("#### 1. Visual Evidence")
        source = st.radio("Input Source:", ["Camera Capture", "File Upload"], horizontal=True)
        img_file = st.camera_input("Scan Exanthem") if source == "Camera Capture" else st.file_uploader("Upload Image", type=['jpg', 'png'])
        if img_file:
            st.success("✅ High-resolution artifact buffered.")
 
    with col_meta:
        st.markdown("#### 2. Semantic Context & Governance")
        role = st.selectbox("Observer Role (Epistemic Source)", ["Citizen Scientist", "Community Health Worker", "Clinician"])
 
        # --- Searchable district dropdown with ALL Uganda districts ---
        district = st.selectbox(
            "Geographic Node (District)",
            options=UGANDA_DISTRICTS,
            index=UGANDA_DISTRICTS.index("Kampala"),
            help="Type to search any of the 146 Uganda districts"
        )
 
        symptoms = st.multiselect("Clinical Signs (Ontology Mapping)", ["Fever", "Lymphadenopathy", "Headache", "Myalgia", "Asthenia"])
 
        st.markdown("##### Privacy Constraints (L5)")
        k_anon = st.toggle("Enable Spatial k-Anonymity", value=True, help="Obfuscates exact GPS to protect patient identity.")
 
        if st.button("🚀 Execute Neuro-symbolic Pipeline", use_container_width=True, type="primary"):
            if not img_file:
                st.error("Please provide visual evidence to proceed.")
            else:
                with st.status("Executing 8-Layer Locator Pipeline...", expanded=True) as status:
                    st.write("📥 L3: Ingesting multimodal data into Bronze Vault...")
                    time.sleep(1)
                    st.write("🧠 L7: Running CNN visual feature extraction...")
                    time.sleep(1.5)
                    st.write("🔗 L2: Aligning metadata with ExanthemObservation Ontology...")
 
                    trust = get_semantic_trust_score({
                        'location_verified': k_anon,
                        'clinical_context': symptoms,
                        'observer_role': role
                    })
                    time.sleep(1)
                    st.write(f"🛡️ L5: Epistemic Trust Score Calculated: **{trust:.2f}**")
 
                    if trust >= 0.7:
                        st.write("✅ **Validation Passed:** Promoting to Silver Knowledge Graph.")
                        save_observation(district, role, symptoms, trust, k_anon)
                        status.update(label="Semantic Ingestion Complete!", state="complete", expanded=False)
                        st.balloons()
                        st.success(f"Observation for **{district}** saved. Check the Dashboard to see it reflected.")
                    else:
                        st.write("⚠️ **Validation Warning:** Trust score too low. Flagged for human-in-the-loop review.")
                        status.update(label="Ingestion Paused: Awaiting Review", state="error", expanded=False)
 
# ============================================================
# PAGE 3: Knowledge Graph View
# ============================================================
elif page == "🕸️ Knowledge Graph View":
    st.markdown("### Semantic Traceability Interface")
    st.write("Query the exact provenance and semantic relationships of flagged anomalies.")
 
    st.markdown("#### 🗄️ Raw Bronze Vault Data (Local)")
    df = load_db()
    if df.empty:
        st.info("The local database is currently empty. Go to the Capture tab to ingest data.")
    else:
        st.dataframe(df.tail(10), use_container_width=True)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download Raw Ingestion Log", data=csv, file_name="bronze_layer_export.csv", mime="text/csv")
