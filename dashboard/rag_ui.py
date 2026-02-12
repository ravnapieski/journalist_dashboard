import streamlit as st # type: ignore
from src.rag_logic import RAGChain, RAGIngestion
import time

# load embedding model once per session, not on every interaction.
@st.cache_resource
def get_rag_chain():
    return RAGChain()

def render_rag_ui(journalist_id, journalist_name):
    """
    Renders the RAG Chat interface for a specific journalist.
    """
    st.markdown(f"### 🤖 Chat with {journalist_name}'s Articles")
    
    # sync with ai button to update vector database after scraping
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("Ask questions about their reporting style, specific topics, or gaps in their coverage.")
    with col2:
        if st.button("🔄 Sync/Update AI"):
            with st.spinner(f"Vectorizing {journalist_name}'s articles..."):
                ingester = RAGIngestion()
                success = ingester.ingest_journalist_data(journalist_id)
                if success:
                    st.success("AI Knowledge Base Updated!")
                    time.sleep(1) 
                    st.rerun() # just to be sure
                else:
                    st.warning("No articles found in database to sync.")
    
    # init chat history
    # use a unique key per journalist so chats don't mix if you switch profiles
    session_key = f"chat_history_{journalist_id}"
    
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    # display chat history
    for message in st.session_state[session_key]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            # show sources, important for journalism!!
            if "sources" in message and message["sources"]:
                with st.expander("📚 Sources Used"):
                    for source in message["sources"]:
                        st.markdown(f"- {source}")

    # handle user input
    if prompt := st.chat_input(f"Ask about {journalist_name}..."):
        # add user message to history
        st.session_state[session_key].append({"role": "user", "content": prompt})
        
        # display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)

        # generate assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            message_placeholder.markdown("Thinking...")
            
            try:
                # load the chains babyyyy
                rag_chain = get_rag_chain()
                
                # get response
                result = rag_chain.get_response(prompt, journalist_id)
                answer = result['answer']
                sources = result['sources']

                # update the placeholder with the final answer
                message_placeholder.markdown(answer)
                
                # show sources
                if sources:
                    with st.expander("📚 Sources Used"):
                        for source in sources:
                            st.markdown(f"- {source}")
                
                # save assistant response to history
                st.session_state[session_key].append({
                    "role": "assistant", 
                    "content": answer,
                    "sources": sources
                })
                
            except Exception as e:
                error_msg = f"⚠️ An error occurred: {str(e)}"
                message_placeholder.error(error_msg)