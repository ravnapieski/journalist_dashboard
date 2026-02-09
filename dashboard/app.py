import streamlit as st
import sqlite3
import pandas as pd
import sys
import os
import math

# Add the project root to python path so we can import from src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import DB_PATH

# --- Page Config ---
st.set_page_config(
    page_title="Yle Journalist Dashboard",
    page_icon="📰",
    layout="wide"
)

# --- Helper Functions ---
@st.cache_data # Caches the data so it doesn't reload on every click
def load_data():
    conn = sqlite3.connect(DB_PATH)
    
    # query to join articles and journalists
    query = """
    SELECT 
        a.title,
        a.published_date,
        a.url,
        length(a.content) as char_count,
        a.keywords,
        j.name as journalist_name
    FROM articles a
    JOIN journalists j ON a.journalist_id = j.id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Main Dashboard ---
def main():
    st.title("📰 Yle Journalist Dashboard")
    st.markdown("Analyze content production, topics, and styles of Yle journalists.")

    # 1. Load Data
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading database: {e}")
        return

    # 2. Sidebar Filters
    st.sidebar.header("Filters")
    
    # Filter by Journalist
    journalist_list = df['journalist_name'].unique().tolist()
    selected_journalist = st.sidebar.selectbox("Select Journalist", journalist_list)
    
    # Filter Data based on selection
    filtered_df = df[df['journalist_name'] == selected_journalist]

    # 3. Top Metrics Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Articles", len(filtered_df))
    
    with col2:
        avg_len = filtered_df['char_count'].mean()
        if avg_len is None or math.isnan(avg_len):
            st.metric("Avg Article Length", "–")
        else:
            st.metric("Avg Article Length", f"{int(avg_len)} chars")
        
    with col3:
        # Simple keyword extraction mock-up (first keyword)
        # In the future, we will use AI here
        st.metric("Top Topic", "Politics (Demo)")

    st.divider()

    # 4. Content Analysis Section
    st.subheader(f"Articles by {selected_journalist}")
    
    # Search bar
    search_term = st.text_input("Search articles...")
    if search_term:
        filtered_df = filtered_df[filtered_df['title'].str.contains(search_term, case=False)]

    # Display Data Table
    # We configure the URL column to be clickable
    st.dataframe(
        filtered_df[['title', 'url', 'char_count', 'keywords']],
        column_config={
            "url": st.column_config.LinkColumn("Link"),
            "char_count": st.column_config.ProgressColumn(
                "Length", format="%d", min_value=0, max_value=10000
            ),
        },
        use_container_width=True,
        hide_index=True
    )

    # 5. Future AI Section Placeholder
    st.divider()
    st.subheader("🤖 AI Assistant (Coming Soon)")
    st.info("The RAG (Retrieval-Augmented Generation) chat interface will appear here.")
    
    user_query = st.text_input("Ask a question about these articles:")
    if user_query:
        st.write(f"**User asked:** {user_query}")
        st.write("*AI System is currently offline. Please proceed to the next development step.*")

if __name__ == "__main__":
    main()