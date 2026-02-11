import streamlit as st # type: ignore
import sqlite3
import pandas as pd
import sys
import random
import os
import re
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import plotly.graph_objects as go # type: ignore

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import DB_PATH, COLORS
from main import run_scraper_pipeline
from mock_utils import generate_mock_analytics

# --- Page Config ---
st.set_page_config(page_title="Yle Journalist Dashboard", page_icon="📰", layout="wide")

# --- Helper Functions ---
@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    query = """
    SELECT 
        a.title,
        a.published_date,
        a.url,
        length(a.content) as char_count,
        a.keywords,
        j.name as journalist_name,
        a.journalist_id
    FROM articles a
    LEFT JOIN journalists j ON a.journalist_id = j.id
    """
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"SQL Error: {e}")
        conn.close()
        return pd.DataFrame()

def extract_id_from_url(url):
    match = re.search(r'56-\d+-\d+', url)
    if match:
        return match.group(0)
    return None
    
# --- Main Dashboard ---
def main():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarContent"] label,
            [data-testid="stSidebarContent"] h1,
            [data-testid="stSidebarContent"] h2 {
                color: white !important;
                /* 1px right, 2px down, 3px blur */
                text-shadow: 1px 2px 3px rgba(0, 0, 0, 0.5);
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    # --- SIDEBAR: SCRAPE AND SELECT JOURNALIST ---
    with st.sidebar:
        st.header("Add New Journalist")
        new_url = st.text_input("Paste Profile URL", placeholder="https://yle.fi/p/56-74-1533/fi")
        
        # Scraping Controls
        col1, col2 = st.columns([2, 1])
        with col1:
            # Default is 10. If 'scrape_all' is checked, this input is disabled visually (optional UI polish)
            article_limit = st.number_input("Max Articles", min_value=1, value=10, step=10)
        with col2:
            st.write("") # Spacer
            st.write("") 
            scrape_all = st.checkbox("All")
            
        # Warning Logic
        if scrape_all or article_limit > 10:
            st.warning("⚠️ Fetching many articles may take some time.")

        # Action Button
        if st.button("Scrape & Add", type="primary"):
            if new_url:
                profile_id = extract_id_from_url(new_url)
                if profile_id:
                    with st.status("Running...", expanded=True) as status:
                        try:
                            # Determine max limit (inf if All)
                            limit_arg = float('inf') if scrape_all else article_limit
                            
                            st.write(f"Scraping (Target: {limit_arg})...")
                            name, count = run_scraper_pipeline(profile_id, max_articles=limit_arg) # type: ignore
                            
                            status.update(label=f"Done! Added {name}", state="complete", expanded=False)
                            
                            # 4. Success & Auto-Select Logic
                            st.session_state['last_added_journalist'] = name
                            st.success(f"Successfully added {name} ({count} articles)")
                            
                            # Clear cache and reload to show new data
                            st.cache_data.clear()
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.error("Invalid URL. Look for '56-74-...' in the link.")

    # --- MAIN CONTENT ---
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    if df.empty:
        st.warning("Database is empty. Add a journalist using the sidebar!")
        return

    # Sidebar Filter
    st.sidebar.divider()
    st.sidebar.header("Filters")
    journalist_list = df['journalist_name'].unique().tolist()
    journalist_list = [x for x in journalist_list if x is not None]
    
    # Auto-Select Logic implementation
    # We check if a new journalist was just added and if they exist in the list
    default_index = 0
    if 'last_added_journalist' in st.session_state:
        target_name = st.session_state['last_added_journalist']
        if target_name in journalist_list:
            default_index = journalist_list.index(target_name)

    if journalist_list:
        selected_journalist = st.sidebar.selectbox(
            "Select Journalist", 
            journalist_list, 
            index=default_index
        )
        filtered_df = df[df['journalist_name'] == selected_journalist]
        j_id = filtered_df['journalist_id'].iloc[0] if not filtered_df.empty else "N/A"
        profile_url = f"https://yle.fi/p/{j_id}/fi" if j_id != "N/A" else "N/A"
        st.title(f"🪪 {selected_journalist}")   # Update title with name of journalist
        st.caption(f"**Profile URL:** {profile_url}")
    else:
        st.warning("No journalists found in DB.")
        filtered_df = df

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles (in database)", len(filtered_df))
    with col2:
        if not filtered_df.empty:
            avg_len = filtered_df['char_count'].mean()
            st.metric("Avg Article Length", f"{int(avg_len)} chars")
    with col3:
        if 'published_date' in filtered_df.columns and not filtered_df['published_date'].isnull().all():
            latest = filtered_df['published_date'].max()
            if latest:
                st.metric("Latest Article", latest[:10])
    st.divider()

    # --- INTERACTIVE DATA TABLE ---
    if not filtered_df.empty:
        st.subheader("📰Articles:")
        st.info("💡 Click the boxes on the left to view detailed analytics.")
        
        # Calculate max length and convert to standard Python int
        max_char_count = int(filtered_df['char_count'].max()) if not filtered_df.empty else 10000

        selection = st.dataframe(
            filtered_df[['title', 'url', 'published_date', 'char_count', 'keywords']],
            column_config={
                "title": st.column_config.TextColumn("Title", width="large"),
                "url": st.column_config.LinkColumn("Link", width=20),
                "published_date": st.column_config.DateColumn(
                    "Published", format="DD.MM.YYYY", width=20),
                "char_count": st.column_config.NumberColumn(
                    "Length", format="%d", width=20),
                "keywords": st.column_config.TextColumn("Keywords", width="medium"),
            },
            use_container_width=True,
            hide_index=True,
            on_select="rerun", 
            selection_mode="single-row"
        )
        # autoselect top row by default
        if selection.selection.rows:
            selected_index = selection.selection.rows[0]
        else:
            selected_index = 0

        # check bounds to ensure dataframe isn't empty
        if selected_index < len(filtered_df):
            selected_article = filtered_df.iloc[selected_index]
            
            # Generate Mock Stats
            stats = generate_mock_analytics(selected_article['url'])
            
            # --- ANALYTICS SECTION ---
            st.markdown("---")
            st.subheader("📊 Analytics:")
            st.subheader(f'“{selected_article["title"]}”')
            
            # Row 1: Key Metrics
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Views", f"{stats['views']:,}", delta=f"{random.randint(-10,10)}% vs avg")
            m2.metric("Avg Read Time", f"{stats['read_time']:.1f} min", delta=f"{random.randint(-20,20)}% vs avg")
            m3.metric("Conversion Rate", f"{stats['conversions']:.1f}%", delta=f"{random.randint(-5,5)}% vs avg")
            
            # Row 2: Charts
            c1, c2, c3 = st.columns([2, 2, 1])

            # Visual parameters
            FIGSIZE = (2.2, 2.2)   # small square for pies
            BAR_FIG = (1.1, 2.2)   # narrow + same height as pies
            DPI = 160             # increase DPI for crisper text
            FONT_SIZE = 6         # slightly larger for readability

            plt.rcParams.update({
                "font.family": "serif",
                "text.antialiased": True,
                "font.size": FONT_SIZE,
            })

            # Helper: small stroke for better legibility on colored backgrounds
            stroke = [pe.withStroke(linewidth=2, foreground="black", alpha=0.6)]

            # --- CHART 1: AGE ---
            with c1:
                st.write("**Reader Age Distribution**")
                age_df = stats["age_data"]

                fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)

                def make_autopct(values, labels):
                    def autopct(pct):
                        idx = autopct.idx # type: ignore
                        label = labels[idx]
                        autopct.idx += 1 # type: ignore
                        return f"{label}\n{pct:.1f}%"
                    autopct.idx = 0 # type: ignore
                    return autopct

                wedges, _, autotexts = ax.pie(
                    age_df["Readers"],
                    startangle=90,
                    colors=COLORS,
                    autopct=make_autopct(age_df["Readers"].tolist(), age_df["Age Group"].tolist()),
                    pctdistance=0.72,
                    wedgeprops=dict(width=0.47, edgecolor="white"),
                    textprops={'fontsize': FONT_SIZE}
                )

                for t in autotexts:
                    t.set_color("white")
                    t.set_path_effects(stroke) # type: ignore
                    t.set_ha("center") # type: ignore
                    t.set_va("center") # type: ignore

                ax.axis("equal")
                fig.tight_layout(pad=0.3)
                fig.patch.set_alpha(0) # type: ignore
                st.pyplot(fig, width='content')

            # --- CHART 2: GENDER ---
            with c2:
                st.write("**Gender Distribution**")
                g_data = stats["gender_data"]

                fig2, ax2 = plt.subplots(figsize=FIGSIZE, dpi=DPI)
                colors_gender = [COLORS[0], COLORS[3]]
                wedges2, texts2, autotexts2 = ax2.pie(
                    g_data['counts'],
                    labels=g_data['labels'],
                    autopct='%1.1f%%',
                    startangle=140,
                    colors=colors_gender,
                    wedgeprops=dict(width=1, edgecolor='white'),
                    textprops={'fontsize': FONT_SIZE},
                    labeldistance=0.5,
                    pctdistance=0.72
                )
                for t in texts2:
                    t.set_color("white")
                    t.set_path_effects(stroke) # type: ignore
                    
                for t in autotexts2:
                    t.set_color("white")
                    t.set_path_effects(stroke) # type: ignore

                ax2.axis('equal')
                fig2.tight_layout(pad=0.3)
                fig2.patch.set_alpha(0) # type: ignore
                st.pyplot(fig2, width='content')

            # --- CHART 3: DEVICES ---
            with c3:
                st.write("**Device Split**")
                dev_data = stats['device_data']
                mobile = dev_data['Mobile']
                desktop = dev_data['Desktop']
                other = dev_data['Other']

                fig3, ax3 = plt.subplots(figsize=BAR_FIG, dpi=DPI)

                ax3.set_ylim(0, 100)
                ax3.set_xlim(-0.5, 1.5)
                ax3.axis('off')

                # Colors: bottom -> other, middle -> desktop, top -> mobile
                c_other = COLORS[1]
                c_desktop = COLORS[2]
                c_mobile = COLORS[3]

                # Draw stacked bars bottom -> top
                p_other = ax3.bar(0, other, width=0.5, color=c_other, edgecolor='white')
                p_desktop = ax3.bar(0, desktop, width=0.5, bottom=other, color=c_desktop, edgecolor='white')
                p_mobile = ax3.bar(0, mobile, width=0.5, bottom=other + desktop, color=c_mobile, edgecolor='white')

                label_kwargs = dict(va='center', ha='left', fontsize=FONT_SIZE, color='white',
                                    bbox=dict(facecolor='black', alpha=0.35, boxstyle='round,pad=0.2', edgecolor='none'))

                t_other = ax3.text(0.62, other / 2, f"Other\n{other:.0f}%", **label_kwargs) # type: ignore
                t_desktop = ax3.text(0.62, other + desktop / 2, f"Desktop\n{desktop:.0f}%", **label_kwargs) # type: ignore
                t_mobile = ax3.text(0.62, other + desktop + mobile / 2, f"Mobile\n{mobile:.0f}%", **label_kwargs) # type: ignore

                # Add the same stroke effect on the text artists (makes them pop)
                for txt in (t_other, t_desktop, t_mobile):
                    txt.set_path_effects(stroke) # type: ignore

                fig3.tight_layout(pad=0.3)
                fig3.patch.set_alpha(0) # type: ignore
                st.pyplot(fig3, width='content')
            
            # --- Interactive time series chart ---
            st.markdown("---")
            st.subheader("📈 Traffic History")
            
            # Get data
            ts_df = stats['clicks_df']
            
            # Create Plotly Figure
            fig = go.Figure()
            
            # Add the Area Trace (The "Mountain")
            fig.add_trace(go.Scatter(
                x=ts_df['Date'],
                y=ts_df['Views'],
                mode='lines',
                fill='tozeroy', # Fills area below the line
                line=dict(color=COLORS[2], width=2), # Your theme green
                name='Views'
            ))
            
            # Update Layout for "Bloomberg" Aesthetic
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=0, b=0), # Remove whitespace
                height=350,
                hovermode="x unified", # Tooltip shows data for all lines at that x-position
                
                # The Axis Styling
                xaxis=dict(
                    showgrid=False, 
                    showline=True, 
                    linecolor='#333',
                    rangeselector=dict(
                        #bgcolor="#262730",
                        activecolor=COLORS[2]
                    ),
                    rangeslider=dict(visible=True, thickness=0.1), # The Zoom Bar at bottom!
                    type="date"
                ),
                yaxis=dict(
                    showgrid=True, 
                    gridcolor='#333', # Subtle grid lines
                    zeroline=False
                )
            )

            st.plotly_chart(fig, use_container_width=True)
            
               
        # Success message underneath the table if just added
        if 'last_added_journalist' in st.session_state and st.session_state['last_added_journalist'] == selected_journalist: # type: ignore
            st.caption(f"✅ Displaying newly added data for {selected_journalist}") # type: ignore

if __name__ == "__main__":
    main()