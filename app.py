import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os
import re
import base64

# ==========================================
# 👇 1. User Configuration Area (Relative paths for cloud deployment)
# ==========================================
LOCATIONS_CSV_PATH = "儒林外史_7_Cities.csv"
TXT_FILE_PATH = "总.txt"
CHAPTER_INFO_PATH = "chapter_data.xlsx"
PICTURE_PATH = "BG.jpg"
# ==========================================

# 2. Basic Page Configuration
st.set_page_config(
    page_title="The Scholars Location Analysis",
    page_icon="🗺️",
    layout="wide"
)

# --- Function to Set Background Image ---
def set_bg_hack(main_bg):
    """
    A function to unpack an image from root folder and set as bg.
    """
    if os.path.exists(main_bg):
        with open(main_bg, "rb") as f:
            data = f.read()
            bin_str = base64.b64encode(data).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{bin_str}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* Add a semi-transparent background to the main content area for readability */
            .main .block-container {{
                background-color: rgba(255, 255, 255, 0.9);
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

# Apply background
set_bg_hack(PICTURE_PATH)

# --- Define Location Dictionary (Used for statistical analysis of the original text) ---
# NOTE: 'aliases' are kept in Chinese to match the source text file.
LOCATIONS_DB = [
    {"name": "Hangzhou",
     "aliases": ["杭州", "杭城", "西湖", "省城", "武林", "錢塘", "斷河頭", "清波門", "仁和", "錢塘門", "靈隱", "天竺",
                 "蘇堤", "雷峰", "淨慈", "城隍山", "吳山"]},
    {"name": "Huzhou", "aliases": ["湖州", "鶯脰湖", "新市鎮", "雙林", "婁府", "烏程"]},
    {"name": "Beijing",
     "aliases": ["北京", "京師", "京裏", "京城", "都門", "魏闕", "長安", "順天府", "內廷", "入京", "進京"]},
    {"name": "Nanjing", "aliases": ["南京", "金陵", "白下", "建康", "應天"]},
    {"name": "Yangzhou", "aliases": ["揚州", "廣陵", "維揚", "江都"]},
    {"name": "Jinan", "aliases": ["濟南", "歷下"]},
    {"name": "Suzhou", "aliases": ["蘇州", "姑蘇", "吳門", "平江"]},
    {"name": "Wenzhou", "aliases": ["溫州", "樂清"]},
    {"name": "Shaoxing", "aliases": ["紹興", "會稽", "越城"]}
]


# 3. Data Loading Functions
@st.cache_data
def load_map_data():
    if not os.path.exists(LOCATIONS_CSV_PATH): return None
    return pd.read_csv(LOCATIONS_CSV_PATH, encoding="utf-8-sig")


@st.cache_data
def load_text_data():
    if not os.path.exists(TXT_FILE_PATH): return None
    with open(TXT_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read()


@st.cache_data
def load_chapter_info():
    if not os.path.exists(CHAPTER_INFO_PATH): return None
    try:
        # Use read_excel to read .xlsx, specifying engine
        return pd.read_excel(CHAPTER_INFO_PATH, engine='openpyxl')
    except Exception as e:
        st.error(f"Failed to read Excel: {e}")
        return None


@st.cache_data
def process_chapter_stats(text):
    """Split text by chapters and count location frequencies."""
    chapters = re.split(r'(?=\*[^\n]+)', text)
    chapter_data = []
    for chapter in chapters:
        if not chapter.strip(): continue
        lines = chapter.split('\n')
        title = lines[0].replace('*', '').strip()
        short_title = title.split(' ')[0] if ' ' in title else title[:6]

        row = {"Chapter": short_title, "Full_Title": title}
        for loc in LOCATIONS_DB:
            count = 0
            for alias in loc["aliases"]:
                count += chapter.count(alias)
            row[loc["name"]] = count
        chapter_data.append(row)
    return pd.DataFrame(chapter_data)


# Execute Loading
df_map = load_map_data()
full_text = load_text_data()
df_info = load_chapter_info()

# Error Checking
if df_map is None or full_text is None:
    st.error("❌ Missing basic data files. Please check if csv and txt files are uploaded to the GitHub repository.")
    st.stop()

df_stats = process_chapter_stats(full_text)

# ==========================================
# 4. Interface Layout
# ==========================================

st.title("🗺️ Spatial Analysis of *The Scholars* (Chapters 10-20)")
st.markdown("""
**Digital Humanities Analysis of *The Scholars* (Ch. 10-20)**
This application combines **GIS spatial analysis** and **close reading** to explore the mobility of scholars between the arena of fame and profit (Hangzhou) and the center of power (Beijing).
""")
st.markdown("---")

# --- Sidebar ---
with st.sidebar:
    st.header("📊 Data Console")
    st.success(f"✅ Loaded location data: {len(df_map)} items")
    if df_info is not None:
        st.success(f"✅ Loaded plot data: {len(df_info)} chapters")
    else:
        st.warning("⚠️ Chapter plot Excel file not found")

    st.markdown("---")
    st.write("**Map Data Preview:**")
    st.dataframe(df_map, use_container_width=True)

# --- Tab Layout Management ---
tab_map, tab_trend, tab_details, tab_insight, tab_route = st.tabs([
    "Map",
    "Trend",
    "Details",
    "Insights",
    "Route"
])

# === TAB 1: Map & Ranking ===
with tab_map:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("Location Frequency Map")
        layer = pdk.Layer(
            "ScatterplotLayer",
            df_map,
            get_position='[Lon, Lat]',
            get_color='[200, 30, 0, 160]',
            get_radius='Frequency * 4000',
            pickable=True,
            auto_highlight=True
        )
        view_state = pdk.ViewState(latitude=31.0, longitude=119.0, zoom=5)
        st.pydeck_chart(pdk.Deck(
            map_provider="carto",
            map_style="light",
            initial_view_state=view_state,
            layers=[layer],
            tooltip={"html": "<b>{Name}</b><br/>Frequency: {Frequency}<br/>Type: {Type}"}
        ))
    with col2:
        st.subheader("Total Frequency Ranking")
        fig_bar = px.bar(df_map.sort_values('Frequency', ascending=True), x='Frequency', y='Name', orientation='h',
                         color='Type')
        st.plotly_chart(fig_bar, use_container_width=True)

# === TAB 2: Trend Analysis ===
with tab_trend:
    st.subheader("Location Activity by Chapter")
    cities_list = [loc["name"] for loc in LOCATIONS_DB]
    df_heatmap = df_stats.melt(id_vars=["Chapter", "Full_Title"], value_vars=cities_list, var_name="City",
                               value_name="Count")

    fig_heatmap = px.density_heatmap(
        df_heatmap, x="Chapter", y="City", z="Count", color_continuous_scale="Reds",
        labels={"Chapter": "Chapter", "City": "City", "Count": "Frequency"}, height=500
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# === TAB 3: Chapter Details (Reads Excel Data) ===
with tab_details:
    st.header("📖 Chapter Characters and Plot Comparison")

    if df_info is not None:
        if 'CHAPTER' in df_info.columns:
            chapter_list = df_info['CHAPTER'].unique()
            selected_chapter = st.selectbox("Select a chapter to view:", chapter_list)

            chapter_row = df_info[df_info['CHAPTER'] == selected_chapter].iloc[0]

            c1, c2 = st.columns([1, 2])

            with c1:
                st.info("### 🎭 Key Characters")
                chars = str(chapter_row.get('CHARACTERS', 'No Data')).replace('\n', '  \n')
                st.markdown(chars)

            with c2:
                st.warning("### ⚡ Key Events")
                events = str(chapter_row.get('MAIN PLOTS', 'No Data')).replace('\n', '  \n')
                st.markdown(events)

            with st.expander("Summary", expanded=True):
                st.write(chapter_row.get('SUMMARY', 'No Data'))
        else:
            st.error("Excel file column names do not match. Please check if it contains 'CHAPTER', 'CHARACTERS', 'MAIN PLOTS', 'SUMMARY'")
    else:
        st.error(f"Please ensure '{CHAPTER_INFO_PATH}' is uploaded.")

# === TAB 4: Deep Analysis ===
with tab_insight:
    st.subheader("Insights: The Flow of Space and Morality")

    st.markdown("""
    ### 1. The Binary Opposition of Cultural Spaces: Centrifugal Civil Society vs. Centripetal Power Machine

    * **Hangzhou as a "Centrifugal Civil Society"**: Hangzhou presents itself as a **decentralized, multi-nodal, self-organizing** ecosystem of fame and profit. There is no absolute authority here; power is dispersed among various figures like Ma Er (essay selection), Jing Lanjiang (poetry fame), Pan San (government office underground), and Wen Jianfeng (gatherings). It is a complex network driven by **commercial capital (bookstores), cultural prestige (literary gatherings), and the underground economy (lawsuits)**. Its social structure is **flat, fluid, and full of opportunities and traps**. Scholars here experience a **horizontal, divergent struggle and maneuvering**.

    * **Beijing as a "Centripetal Power Machine"**: Beijing exists as a **vertical, strictly hierarchical ultimate power field**. Its influence, though remote, is omnipresent. Through **civil service examinations, official personnel affairs, and gentry networks**, it sucks in resources and talent from across the country like a black hole, dictating the ultimate orientation of all social values. In Beijing, all behavior is reduced to **clinging to and parasitizing higher power strata**. Its social structure is **pyramidal and closed**. Scholars here experience a **vertical, oppressive, yet tempting anxiety for promotion**.

    ### 2. Spatial Narrative of Moral Degeneration (Kuang Chaoren)

    * **Kuang Chaoren as a "Spatial Traveler"**: He is a **specimen constantly migrating within the empire's core cultural spaces**. His trajectory from the countryside (Wenzhou) to the regional center (Hangzhou), and finally to the imperial heart (Beijing), completely demonstrates how a lower-class scholar is shaped by the production logic of different spaces. He is not a fixed resident of any place, but a **keen learner and speculator of spatial rules**, quickly mastering the survival laws of each space and becoming alienated by them.

    * **Ideological Level: From Confucian Ethics to Utilitarianism**. His ideological transformation trajectory is clear: starting with the **natural concept of filial piety** during the Wenzhou period; passing through the **market survival philosophy of "whoever feeds me is my mother"** formed under Pan San's tutelage in Hangzhou; and finally solidifying into the **extreme egoism of calculated interest** in Beijing. His worldview completes a thorough metamorphosis from **value rationality** to **instrumental rationality**.

    * **Tragic Spatial Symbols**:
        * **Wenhan Building in Hangzhou**: A place of alienated knowledge production. Here, he annotates model examination essays night after night. This space, which should be sacred for "seeking knowledge," runs parallel to his cheating in exams and participation in fraud. **Wenhan Building symbolizes the complete separation of his "knowledge" and "morality"**.
        * **Wedding Room in Beijing**: A ritual space for identity reconstruction and the end of humanity. In the wedding room in Beijing, through a wedding built on lies (concealing his first wife), he completes the whitewashing and elevation of his social identity. This space, which should symbolize the joyous union of human relations, becomes **the altar where he buries his last shred of conscience and completely instrumentalizes himself**.

    ### 3. The Persistence of Ma Chunshang

    * **Binary Opposition of Cultural Spaces: System Guardian vs. Wandering Outcast**
        * **Ma Er as a "Selector"**: He is a **systemic pillar of civil service examination knowledge production**. In the secular cultural market of Hangzhou, he plays the role of transforming official ideology (eight-legged essays) into standardized commodities that can be circulated and imitated. His commentaries show that he is a **rigorous, depersonalized porter of knowledge**.
        * **Ma Er as a "Wandering Scholar"**: He himself is a **marginal scholar detached from the center of power**. This identity of a "system guardian in the wild" constitutes the root of all his comedy and tragedy.

    * **Analysis of Ma Er's Personality Structure**
        * **Ideological Level**: A "man in a case" completely disciplined by the eight-legged essay. His worldview is entirely constructed by examination essays, even believing that "civil service examinations are something everyone must do from ancient times to the present." This **high purity and enclosure** of thought makes him appear pedantic, yet it also constitutes his **moral armor** against secular temptations.
        * **Behavioral Level**: A practitioner of Jiangnan chivalry. Although his thoughts are rigid, his actions shine with **simple Confucian chivalric spirit**. He gives all he has to help Kuang Chaoren, whom he meets by chance, demonstrating the **human brilliance retained at the practical level** by a person shaped by the system.

    * **Tragic Spatial Symbols**
        * **West Lake in Hangzhou: An Outsider in the World of Desire**. He is completely indifferent to the lake scenery and the colorful crowds, caring only about eating and the Emperor's calligraphy. This marks the **desertification of his sensory world**; his aesthetics and emotions have been completely alienated by the eight-legged essay.
        * **Mirror Relationship with Kuang Chaoren**: Ma Er is **Kuang Chaoren's spiritual father and frame of reference**. Kuang Chaoren learned composition from him but abandoned his conduct. Ma Er's "immobility" contrasts with the drastic and inevitable nature of Kuang Chaoren's "degeneration".
    """)

    st.divider()
    st.subheader("Original Text Keyword Search")
    # Default value kept in Chinese as it searches the source text
    search_term = st.text_input("Enter Keyword (Traditional Chinese)", "西湖", key="search_term_input")

    if search_term:
        paragraphs = full_text.replace("\\r", "").split("\\n")
        if len(paragraphs) < 2: paragraphs = full_text.split("\n")
        count = 0
        for p in paragraphs:
            if search_term in p:
                st.markdown(f"**...{p.strip()}...**")
                st.divider()
                count += 1
                if count >= 3: break
        if count == 0: st.warning("No relevant content found.")

# === TAB 5: Character Route (New) ===
with tab_route:
    # Define route data
    ROUTES_DATA = [
        {
            "name": "Kuang Chaoren",
            "color": [255, 0, 0],
            "path": [[120.98, 28.12], [120.15, 30.27], [120.58, 30.00], [120.15, 30.27], [119.41, 32.39],
                     [116.40, 39.90]],
            "chapters": "Ch. 15-20"
        },
        {
            "name": "Ma Chunshang",
            "color": [0, 128, 255],
            "path": [[120.75, 30.75], [120.15, 30.27]],
            "chapters": "Ch. 13-15"
        },
        {
            "name": "Niu Buyi",
            "color": [0, 128, 0],
            "path": [[120.58, 30.00], [120.08, 30.89], [119.41, 32.39], [118.37, 31.35]],
            "chapters": "Ch. 10, 20"
        }
    ]

    st.subheader("🚀 Character Trajectories")
    c_map, c_info = st.columns([3, 1])

    with c_map:
        view_state_route = pdk.ViewState(latitude=32.0, longitude=118.0, zoom=5)
        layer_routes = pdk.Layer("PathLayer", ROUTES_DATA, pickable=True, get_color="color", width_scale=20,
                                 width_min_pixels=3, get_path="path", get_width=5)

        all_points = []
        for r in ROUTES_DATA:
            for p in r['path']:
                all_points.append({"coord": p, "name": r['name'], "color": r['color']})
        layer_points = pdk.Layer("ScatterplotLayer", all_points, get_position="coord", get_color="color",
                                 get_radius=8000, pickable=True)

        st.pydeck_chart(pdk.Deck(
            map_provider="carto", map_style="light", initial_view_state=view_state_route,
            layers=[layer_routes, layer_points],
            tooltip={"html": "<b>{name}</b><br/>Active Chapters: {chapters}",
                     "style": {"backgroundColor": "steelblue", "color": "white"}}
        ))

    with c_info:
        st.markdown("#### 🔴 Kuang Chaoren")
        st.caption("Route: Wenzhou -> Beijing")
        st.write("A path of degeneration from the periphery to the center.")
        st.divider()
        st.markdown("#### 🔵 Ma Chunshang")
        st.caption("Route: Jiaxing -> Hangzhou")
        st.write("Adhering to the Confucian orthodoxy in Jiangnan.")
        st.divider()
        st.markdown("#### 🟢 Niu Buyi")
        st.caption("Route: Huzhou -> Wuhu")
        st.write("The desolation of wandering and dying in a foreign land.")


st.caption("Created by Streamlit | Data Source: Ctext.org")
