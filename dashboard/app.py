import streamlit as st
import sqlite3
import pandas as pd
import sys
import os
import re

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

# --- Main Dashboard ---
def main():
    st.title("📰 Yle Journalist Dashboard")

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
    
    # 5. Auto-Select Logic implementation
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

    # Data Table
    if not filtered_df.empty:
        st.subheader(f"Articles: {selected_journalist}")
        
        # Calculate max length and convert to standard Python int
        max_char_count = int(filtered_df['char_count'].max()) if not filtered_df.empty else 10000

        st.dataframe(
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
            hide_index=True
        )
        
        # Success message underneath the table if just added
        if 'last_added_journalist' in st.session_state and st.session_state['last_added_journalist'] == selected_journalist:
            st.caption(f"✅ Displaying newly added data for {selected_journalist}")

if __name__ == "__main__":
    main()