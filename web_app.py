import streamlit as st
import json
import os
import sys
import logging

# --- PATH SETUP ---
sys.path.append(os.path.dirname(__file__))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- IMPORTS ---
# We still need agents.py for the Chatbot functionality (get_agent)
AGENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'agents.py')
if not os.path.exists(AGENTS_FILE_PATH):
    st.error("FATAL: agents.py not found.")
    st.stop()
else:
    try:
        from agents import get_agent
    except ImportError as e:
        st.error(f"FATAL: Import failed: {e}")
        st.stop()

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="AI Wargame Situation Room")
PRECOMPUTED_FILE = "intelligence_analysis.json"

# --- SESSION STATE ---
if 'current_page_id' not in st.session_state:
    st.session_state.current_page_id = "Situation Room - SITREP"
if 'wargame_context' not in st.session_state:
    st.session_state.wargame_context = ""
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# --- NAVIGATION ---
NAVIGATION = {
    "Situation Room": {
        "SITREP": {"icon": "📊", "type": "llm_static"},
        "SIGACTS": {"icon": "💥", "type": "llm_static"},
        "ORBAT": {"icon": "🛡️", "type": "llm_static"},
        "Actions": {"icon": "🎬", "type": "llm_static"},
        "Uncertainties": {"icon": "❓", "type": "llm_static"},
        "Dilemmas": {"icon": "⚖️", "type": "llm_static"},
    },
    "Advisors": {
        "Integrator": {"icon": "🧩", "type": "chatbot"},
        "Military Historian": {"icon": "🏛️", "type": "chatbot"},
        "Alliance Whisperer": {"icon": "🤝", "type": "chatbot"},
        "Red Teamer": {"icon": "😈", "type": "chatbot"},
        "The Missing Link": {"icon": "💡", "type": "chatbot"},
        "Citizen's Voice": {"icon": "🗣️", "type": "chatbot"},
    }
}

def load_data_fast():
    """
    Loads 1) Raw transcripts (for chat context) and 2) Precomputed Analysis JSON.
    """
    # 1. Load Transcripts (For Chat Context)
    files_to_load = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    combined_text = ""
    
    for filename in files_to_load:
        path = filename if os.path.exists(filename) else os.path.join("data", filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if 'text' in entry: combined_text += f"{entry.get('speaker', 'Unknown')}: {entry['text']}\n"
                            elif 'content' in entry: combined_text += f"{entry['content']}\n"
                    elif isinstance(data, dict):
                        combined_text += str(data)
                    combined_text += "\n--- END OF EPISODE ---\n"
            except Exception:
                pass

    st.session_state.wargame_context = combined_text
    
    # 2. Load Precomputed Analysis
    if os.path.exists(PRECOMPUTED_FILE):
        try:
            with open(PRECOMPUTED_FILE, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                # Load into session state
                for key, content in analysis_data.items():
                    st.session_state[key] = content
                st.session_state.data_loaded = True
                return True
        except Exception as e:
            st.error(f"Error reading {PRECOMPUTED_FILE}: {e}")
            return False
    else:
        # If file missing, we rely on manual generation or show error
        return False

# --- SIDEBAR ---
with st.sidebar:
    st.title("Wargame OS")
    
    # Auto-load on first run
    if not st.session_state.data_loaded:
        success = load_data_fast()
        if success:
            st.success("System Online (Cached Data)")
        else:
            st.warning(f"Cache missing: {PRECOMPUTED_FILE}")
            if st.button("Retry Load"):
                st.rerun()

    st.markdown("---")

    # Nav
    for group, pages in NAVIGATION.items():
        st.subheader(group)
        for page_title, data in pages.items():
            unique_id = f"{group} - {page_title}"
            if st.session_state.current_page_id == unique_id:
                st.markdown(f"**👉 {data['icon']} {page_title}**")
            else:
                if st.button(f"{data['icon']} {page_title}", key=unique_id, use_container_width=True):
                    st.session_state.current_page_id = unique_id
                    st.rerun()
        st.markdown("---")

# --- PAGE RENDERING ---
current_id = st.session_state.current_page_id
try:
    page_group, current_page_title = current_id.split(" - ")
    page_data = NAVIGATION[page_group][current_page_title]
except:
    page_group = "Situation Room"
    current_page_title = "SITREP"
    page_data = NAVIGATION["Situation Room"]["SITREP"]

def render_llm_static_page(group, title):
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")
    cache_key = f"report_{title}"
    
    if cache_key in st.session_state:
        st.markdown(st.session_state[cache_key])
    else:
        st.warning("Data not found. Ensure precompute_intelligence.py has been run.")

def render_chatbot_page(agent_name):
    st.header(f"{page_data['icon']} Advisor: {agent_name}")
    
    # Static Briefing
    briefing_key = f"briefing_{agent_name}"
    if briefing_key in st.session_state:
        with st.expander("📜 Initial Strategic Assessment", expanded=True):
            st.markdown(st.session_state[briefing_key])
    
    st.markdown("---")
    st.caption("Operational Chat Channel - Secure Line Open")

    # Interactive Chat
    history_key = f"chat_history_{agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(f"Ask {agent_name}..."):
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = get_agent(agent_name)
                if agent:
                    # We pass context here for RAG capability on follow-up questions
                    response = agent.get_response(prompt, context_text=st.session_state.wargame_context)
                    st.markdown(response)
                    st.session_state[history_key].append({"role": "assistant", "content": response})
                else:
                    st.error("Agent connection failed.")

if page_data['type'] == 'llm_static':
    render_llm_static_page(page_group, current_page_title)
elif page_data['type'] == 'chatbot':
    render_chatbot_page(current_page_title)