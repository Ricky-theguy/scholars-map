import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import os
import re

# ==========================================
# 👇 1. 用户配置区域 (已修改为相对路径，适配云端部署)
# ==========================================
LOCATIONS_CSV_PATH = "儒林外史_7_Cities.csv"
TXT_FILE_PATH = "总.txt"
CHAPTER_INFO_PATH = "chapter_data.xlsx"
# ==========================================

# 2. 页面基础配置
st.set_page_config(
    page_title="儒林外史地点分析",
    page_icon="🗺️",
    layout="wide"
)

# --- 定义地点字典 (用于分章节统计原文) ---
LOCATIONS_DB = [
    {"name": "杭州 (Hangzhou)",
     "aliases": ["杭州", "杭城", "西湖", "省城", "武林", "錢塘", "斷河頭", "清波門", "仁和", "錢塘門", "靈隱", "天竺",
                 "蘇堤", "雷峰", "淨慈", "城隍山", "吳山"]},
    {"name": "湖州 (Huzhou)", "aliases": ["湖州", "鶯脰湖", "新市鎮", "雙林", "婁府", "烏程"]},
    {"name": "北京 (Beijing)",
     "aliases": ["北京", "京師", "京裏", "京城", "都門", "魏闕", "長安", "順天府", "內廷", "入京", "進京"]},
    {"name": "南京 (Nanjing)", "aliases": ["南京", "金陵", "白下", "建康", "應天"]},
    {"name": "揚州 (Yangzhou)", "aliases": ["揚州", "廣陵", "維揚", "江都"]},
    {"name": "濟南 (Jinan)", "aliases": ["濟南", "歷下"]},
    {"name": "蘇州 (Suzhou)", "aliases": ["蘇州", "姑蘇", "吳門", "平江"]},
    {"name": "溫州 (Wenzhou)", "aliases": ["溫州", "樂清"]},
    {"name": "紹興 (Shaoxing)", "aliases": ["紹興", "會稽", "越城"]}
]


# 3. 数据加载函数
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
        # 使用 read_excel 读取 .xlsx，指定 engine
        return pd.read_excel(CHAPTER_INFO_PATH, engine='openpyxl')
    except Exception as e:
        st.error(f"读取 Excel 失败: {e}")
        return None


@st.cache_data
def process_chapter_stats(text):
    """将文本按章节切分并统计地点频次"""
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


# 执行加载
df_map = load_map_data()
full_text = load_text_data()
df_info = load_chapter_info()

# 错误检查
if df_map is None or full_text is None:
    st.error("❌ 缺少基础数据文件，请检查 GitHub 仓库中是否上传了 csv 和 txt 文件。")
    st.stop()

df_stats = process_chapter_stats(full_text)

# ==========================================
# 4. 界面布局
# ==========================================

st.title("🗺️ 《儒林外史》第10-20回空间分析")
st.markdown("""
**Digital Humanities Analysis of *The Scholars* (Ch. 10-20)**
本应用结合了**GIS空间分析**与**文本细读**，主要探讨士人在名利场（杭州）与权力中心（北京）之间的流动。
""")
st.markdown("---")

# --- 侧边栏 ---
with st.sidebar:
    st.header("📊 数据控制台")
    st.success(f"✅ 已加载地点数据: {len(df_map)} 个")
    if df_info is not None:
        st.success(f"✅ 已加载情节数据: {len(df_info)} 章")
    else:
        st.warning("⚠️ 未找到章节情节 Excel 文件")

    st.markdown("---")
    st.write("**地图数据预览:**")
    st.dataframe(df_map, use_container_width=True)

# --- Tab 布局管理所有内容 ---
tab_map, tab_trend, tab_details, tab_insight, tab_route = st.tabs([
    "📍 空间分布 (Map)",
    "📈 动态演变 (Trend)",
    "📖 章节详情 (Details)",
    "🧐 深度分析 (Insights)",
    "🚀 人物轨迹 (Route)"
])

# === TAB 1: 地图与排名 ===
with tab_map:
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("地点频次地图")
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
            tooltip={"html": "<b>{Name}</b><br/>频次: {Frequency}<br/>性质: {Type}"}
        ))
    with col2:
        st.subheader("总频次排名")
        fig_bar = px.bar(df_map.sort_values('Frequency', ascending=True), x='Frequency', y='Name', orientation='h',
                         color='Type')
        st.plotly_chart(fig_bar, use_container_width=True)

# === TAB 2: 趋势分析 ===
with tab_trend:
    st.subheader("地点在各章节的活跃度")
    cities_list = [loc["name"] for loc in LOCATIONS_DB]
    df_heatmap = df_stats.melt(id_vars=["Chapter", "Full_Title"], value_vars=cities_list, var_name="City",
                               value_name="Count")

    fig_heatmap = px.density_heatmap(
        df_heatmap, x="Chapter", y="City", z="Count", color_continuous_scale="Reds",
        labels={"Chapter": "章节", "City": "城市", "Count": "频次"}, height=500
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# === TAB 3: 章节详情 (读取 Excel 数据) ===
with tab_details:
    st.header("📖 章节人物与情节对照")

    if df_info is not None:
        if 'CHAPTER' in df_info.columns:
            chapter_list = df_info['CHAPTER'].unique()
            selected_chapter = st.selectbox("请选择要查看的章节:", chapter_list)

            chapter_row = df_info[df_info['CHAPTER'] == selected_chapter].iloc[0]

            c1, c2 = st.columns([1, 2])

            with c1:
                st.info("### 🎭 关键人物")
                chars = str(chapter_row.get('CHARACTERS', '无数据')).replace('\n', '  \n')
                st.markdown(chars)

            with c2:
                st.warning("### ⚡ 关键事件")
                events = str(chapter_row.get('MAIN PLOTS', '无数据')).replace('\n', '  \n')
                st.markdown(events)

            with st.expander("查看本章小结 (Summary)", expanded=True):
                st.write(chapter_row.get('SUMMARY', '无数据'))
        else:
            st.error("Excel 文件列名不匹配，请检查是否包含 'CHAPTER', 'CHARACTERS', 'MAIN PLOTS', 'SUMMARY'")
    else:
        st.error(f"请确保上传了 '{CHAPTER_INFO_PATH}' 文件。")

# === TAB 4: 深度分析 ===
with tab_insight:
    st.subheader("Insights: 空间与道德的流动")

    st.markdown("""
    ### 1. 文化空间的二元对立：离心化的市民社会与向心化的权力机器
    * **作为“离心化市民社会”的杭州**：杭州呈现为一个**去中心、多节点、自组织**的名利生态圈...
    * **作为“向心化权力机器”的北京**：北京则作为一个**垂直的、等级森严的终极权力场**而存在...

    ### 2. 匡超人的堕落轨迹 (Spatial Narrative of Moral Degeneration)
    * **作为“空间穿越者”的匡超人**：他是**一个在帝国核心文化空间中不断迁徙的样本**...
    * **思想层面**：从儒家伦理到彻底的功利主义...
    * **悲剧性空间象征**：杭州的文瀚楼、北京的婚房...

    ### 3. 马二先生的坚守与悖论 (The Persistence of Ma Chunshang)
    * **文化空间的二元对立**：体制守护者与江湖落魄人...
    * **马二先生的人格结构解析**：被八股彻底规训的“套中人” vs 江湖道义的践行者...
    """)

    st.divider()
    st.subheader("原文关键词检索")
    search_term = st.text_input("输入关键词 (繁体)", "西湖", key="search_term_input")

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
        if count == 0: st.warning("未找到相关内容。")

# === TAB 5: 人物轨迹 (新增) ===
with tab_route:
    # 定义路线数据
    ROUTES_DATA = [
        {
            "name": "匡超人 (Kuang Chaoren)",
            "color": [255, 0, 0],
            "path": [[120.98, 28.12], [120.15, 30.27], [120.58, 30.00], [120.15, 30.27], [119.41, 32.39],
                     [116.40, 39.90]],
            "chapters": "第15-20回"
        },
        {
            "name": "马二先生 (Ma Chunshang)",
            "color": [0, 128, 255],
            "path": [[120.75, 30.75], [120.15, 30.27]],
            "chapters": "第13-15回"
        },
        {
            "name": "牛布衣 (Niu Buyi)",
            "color": [0, 128, 0],
            "path": [[120.58, 30.00], [120.08, 30.89], [119.41, 32.39], [118.37, 31.35]],
            "chapters": "第10, 20回"
        }
    ]

    st.subheader("🚀 人物行动轨迹")
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
            tooltip={"html": "<b>{name}</b><br/>活动章节: {chapters}",
                     "style": {"backgroundColor": "steelblue", "color": "white"}}
        ))

    with c_info:
        st.markdown("#### 🔴 匡超人")
        st.caption("路线：温州 -> 北京")
        st.write("从边缘向中心的堕落之路。")
        st.divider()
        st.markdown("#### 🔵 马二先生")
        st.caption("路线：嘉兴 -> 杭州")
        st.write("坚守江南的儒家正统。")
        st.divider()
        st.markdown("#### 🟢 牛布衣")
        st.caption("路线：湖州 -> 芜湖")
        st.write("漂泊客死他乡的悲凉。")

st.caption("Created by Streamlit | Data Source: Ctext.org")