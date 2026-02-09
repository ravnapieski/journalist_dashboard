import streamlit as st
import sqlite3
import pandas as pd
import sys
import os
import re
import random
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import DB_PATH
from main import run_scraper_pipeline

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
        j.name as journalist_name
    FROM articles a
    LEFT JOIN journalists j ON a.journalist_id = j.id
    """
    try:
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        conn.close()
        return pd.DataFrame()

def extract_id_from_url(url):
    match = re.search(r'56-\d+-\d+', url)
    if match:
        return match.group(0)
    return None

def generate_mock_analytics(seed_str):
    """
    Generates consistent 'fake' stats based on the input seed (url).
    """
    # Seed the random generator so the stats for a specific article are always the same
    random.seed(seed_str)
    
    views = random.randint(1500, 85000)
    avg_read_time = random.uniform(0.4, 8.0) # Minutes
    conversion_rate = random.uniform(0.5, 6.9) # Percent
    
    # Mock Age Distribution
    age_groups = ['16-24', '25-34', '35-44', '45-54', '55-64', '65+']
    age_data = [random.randint(10, 100) for _ in age_groups]
    
    # Mock Gender distribution
    male = random.randint(35, 60)
    female = random.randint(40, 65)
    total = male + female
    gender_counts = [male / total * 100, female / total * 100]
    gender_labels = ["Male", "Female"]
    
    # Mock device split
    r1 = random.randint(60, 80)
    r2 = random.randint(10, 30)
    r3 = max(2, 100 - (r1 + r2)) # Other (Tablet/Console)
    
    # Normalize exactly to 100% just in case
    total = r1 + r2 + r3
    device_data = {
        "Mobile": (r1 / total) * 100,
        "Desktop": (r2 / total) * 100,
        "Other": (r3 / total) * 100
    }
    
    return {
        "views": views,
        "read_time": avg_read_time,
        "conversions": conversion_rate,
        "age_data": pd.DataFrame({"Age Group": age_groups, "Readers": age_data}),
        "gender_data": {"labels": gender_labels, "counts": gender_counts},
        "device_data": device_data
    }
    
# --- Main Dashboard ---
def main():
    # --- SIDEBAR: ADD NEW JOURNALIST ---
    with st.sidebar:
        st.header("Add New Journalist")
        new_url = st.text_input("Paste Profile URL", placeholder="https://yle.fi/p/56-74-1533/fi")
        
        # 1. Scraping Controls
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
        if st.button("Scrape & Add"):
            if new_url:
                profile_id = extract_id_from_url(new_url)
                if profile_id:
                    with st.status("Running...", expanded=True) as status:
                        try:
                            # Determine max limit (inf if All)
                            limit_arg = float('inf') if scrape_all else article_limit
                            
                            st.write(f"Scraping (Target: {limit_arg})...")
                            name, count = run_scraper_pipeline(profile_id, max_articles=limit_arg)
                            
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
        st.title(f"🪪 {selected_journalist}")   # Update title with name of journalist
    else:
        st.warning("No journalists found in DB.")
        filtered_df = df

    # Display Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Articles", len(filtered_df))
    with col2:
        if not filtered_df.empty:
            avg_len = filtered_df['char_count'].mean()
            st.metric("Avg Length", f"{int(avg_len)} chars")
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
        # Handle selection
        if selection.selection.rows:
            # Get the selected row index and fetch data
            selected_index = selection.selection.rows[0]
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
                colors = ['#003f5c', '#444e86', '#955196', '#dd5182', '#ff6e54', '#ffa600']

                def make_autopct(values, labels):
                    def autopct(pct):
                        idx = autopct.idx
                        label = labels[idx]
                        autopct.idx += 1
                        return f"{label}\n{pct:.1f}%"
                    autopct.idx = 0
                    return autopct

                wedges, _, autotexts = ax.pie(
                    age_df["Readers"],
                    startangle=90,
                    colors=colors,
                    autopct=make_autopct(age_df["Readers"].tolist(), age_df["Age Group"].tolist()),
                    pctdistance=0.72,
                    wedgeprops=dict(width=0.47, edgecolor="white"),
                    textprops={'fontsize': FONT_SIZE}
                )

                for t in autotexts:
                    t.set_color("white")
                    t.set_path_effects(stroke)
                    t.set_ha("center")
                    t.set_va("center")

                ax.axis("equal")
                fig.tight_layout(pad=0.3)
                fig.patch.set_alpha(0)
                st.pyplot(fig, width='content')

            # --- CHART 2: GENDER ---
            with c2:
                st.write("**Gender Distribution**")
                g_data = stats["gender_data"]

                fig2, ax2 = plt.subplots(figsize=FIGSIZE, dpi=DPI)
                colors_gender = ['#003f5c', '#dd5182']
                wedges2, texts2, autotexts2 = ax2.pie(
                    g_data['counts'],
                    #labels=g_data['labels'],
                    autopct='%1.1f%%',
                    startangle=140,
                    colors=colors_gender,
                    wedgeprops=dict(width=1, edgecolor='white'),
                    textprops={'fontsize': FONT_SIZE}
                )

                # Stroke + color for percentages
                for t in autotexts2:
                    t.set_color("white")
                    t.set_path_effects(stroke)

                ax2.axis('equal')
                fig2.tight_layout(pad=0.3)
                fig2.patch.set_alpha(0)
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
                c_other = '#444e86'
                c_desktop = '#955196'
                c_mobile = '#ff6e54'

                # Draw stacked bars bottom -> top
                p_other = ax3.bar(0, other, width=0.5, color=c_other, edgecolor='white')
                p_desktop = ax3.bar(0, desktop, width=0.5, bottom=other, color=c_desktop, edgecolor='white')
                p_mobile = ax3.bar(0, mobile, width=0.5, bottom=other + desktop, color=c_mobile, edgecolor='white')

                label_kwargs = dict(va='center', ha='left', fontsize=FONT_SIZE, color='white',
                                    bbox=dict(facecolor='black', alpha=0.35, boxstyle='round,pad=0.2', edgecolor='none'))

                t_other = ax3.text(0.62, other / 2, f"Other\n{other:.0f}%", **label_kwargs)
                t_desktop = ax3.text(0.62, other + desktop / 2, f"Desktop\n{desktop:.0f}%", **label_kwargs)
                t_mobile = ax3.text(0.62, other + desktop + mobile / 2, f"Mobile\n{mobile:.0f}%", **label_kwargs)

                # Add the same stroke effect on the text artists (makes them pop)
                for txt in (t_other, t_desktop, t_mobile):
                    txt.set_path_effects(stroke)

                fig3.tight_layout(pad=0.3)
                fig3.patch.set_alpha(0)
                st.pyplot(fig3, width='content')
                
        # Success message underneath the table if just added
        if 'last_added_journalist' in st.session_state and st.session_state['last_added_journalist'] == selected_journalist:
            st.caption(f"✅ Displaying newly added data for {selected_journalist}")

if __name__ == "__main__":
    main()