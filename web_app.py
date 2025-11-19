import streamlit as st
import json
import os
import sys

# --- PATH SETUP ---
# Ensure local modules can be imported
sys.path.append(os.path.dirname(__file__))

# --- IMPORTS ---
AGENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'agents.py')

# Check file existence
if not os.path.exists(AGENTS_FILE_PATH):
    st.error(f"FATAL: 'agents.py' not found at {AGENTS_FILE_PATH}.")
    get_agent = None
    generate_situation_report = None
else:
    try:
        # Import both the factory and the report generator
        from agents import get_agent, generate_situation_report
    except ImportError as e:
        st.error(f"FATAL: Failed to import from agents.py: {e}")
        get_agent = None
        generate_situation_report = None

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="AI Wargame Situation Room")

# --- SESSION STATE INIT ---
if 'current_page_id' not in st.session_state:
    st.session_state.current_page_id = "Situation Room - SITREP" # Default landing
if 'wargame_context' not in st.session_state:
    st.session_state.wargame_context = ""
if 'transcript_context_length' not in st.session_state:
    st.session_state.transcript_context_length = 0

# --- NAVIGATION STRUCTURE ---
NAVIGATION = {
    "Situation Room": {
        "Sitrep": {"icon": "📊", "type": "llm_static"},
        "Sigacts": {"icon": "💥", "type": "llm_static"},
        "ORBAT": {"icon": "🛡️", "type": "llm_static"},
        "Actions": {"icon": "🎬", "type": "llm_static"},
        "Uncertainties": {"icon": "❓", "type": "llm_static"},
        "Dilemmas": {"icon": "⚖️", "type": "llm_static"},
    },
    "Advisors": {
        "Integrator": {"icon": "🧩", "type": "chatbot"},
        "Red Teamer": {"icon": "😈", "type": "chatbot"},
        "Military Historian": {"icon": "🏛️", "type": "chatbot"},
        "Citizen's Voice": {"icon": "🗣️", "type": "chatbot"},
    }
}

def load_transcripts():
    """
    Loads transcript JSON files from the 'data' directory (or current dir).
    """
    # Hardcoded list based on your request
    files_to_load = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    
    combined_text = ""
    loaded_count = 0
    
    for filename in files_to_load:
        # Check current directory or a 'data' subdirectory
        if os.path.exists(filename):
            path = filename
        elif os.path.exists(os.path.join("data", filename)):
            path = os.path.join("data", filename)
        else:
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Assuming the JSON structure is list of dicts or has a 'text' field
                # Adjust this logic based on your actual JSON structure
                if isinstance(data, list):
                    for entry in data:
                        if 'text' in entry: # Common transcript format
                            combined_text += f"{entry.get('speaker', 'Unknown')}: {entry['text']}\n"
                        elif 'content' in entry:
                            combined_text += f"{entry['content']}\n"
                elif isinstance(data, dict):
                     # Fallback for specific structure
                     combined_text += str(data)
                
                loaded_count += 1
                combined_text += "\n--- END OF EPISODE ---\n"
        except Exception as e:
            st.sidebar.error(f"Error loading {filename}: {e}")

    st.session_state.wargame_context = combined_text
    st.session_state.transcript_context_length = len(combined_text)
    return loaded_count

# --- SIDEBAR ---
with st.sidebar:
    st.title("Wargame OS")
    
    # Data Loader
    if st.button("Reload Transcripts"):
        count = load_transcripts()
        if count > 0:
            st.success(f"Loaded {count} files.")
            # Clear report cache on data reload
            keys_to_delete = [k for k in st.session_state.keys() if k.startswith("report_")]
            for k in keys_to_delete:
                del st.session_state[k]
            st.rerun()
        else:
            st.warning("No transcript files found.")

    st.info(f"Context Buffer: {st.session_state.get('transcript_context_length', 0):,} chars")
    st.markdown("---")

    # Navigation Menu
    for group, pages in NAVIGATION.items():
        st.subheader(group)
        for page_title, data in pages.items():
            unique_id = f"{group} - {page_title}"
            
            # Styling selected button
            if st.session_state.current_page_id == unique_id:
                st.markdown(f"**👉 {data['icon']} {page_title}**")
            else:
                if st.button(f"{data['icon']} {page_title}", key=unique_id, use_container_width=True):
                    st.session_state.current_page_id = unique_id
                    st.rerun()
        st.markdown("---")

# --- PAGE ROUTER ---

# Determine current page details
current_id = st.session_state.current_page_id
try:
    page_group, current_page_title = current_id.split(" - ")
    page_data = NAVIGATION[page_group][current_page_title]
except:
    # Fallback
    page_group = "Situation Room"
    current_page_title = "SITREP"
    page_data = NAVIGATION["Situation Room"]["SITREP"]

# --- RENDER FUNCTIONS ---

def render_llm_static_page(group, title):
    """
    Renders a situation report. Checks cache, if missing, calls LLM.
    """
    st.header(f"{page_data['icon']} {group}: {title}")
    st.caption("AI-Generated Analysis based on current transcripts")
    st.markdown("---")
    
    if not st.session_state.wargame_context:
        st.warning("⚠️ No transcripts loaded. Please click 'Reload Transcripts' in the sidebar.")
        return

    # Cache Key: Ensures we don't re-generate just by resizing window or clicking other things
    cache_key = f"report_{title}"
    
    # 1. Check if we have it
    if cache_key in st.session_state:
        st.markdown(st.session_state[cache_key])
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Regenerate Analysis"):
                del st.session_state[cache_key]
                st.rerun()
    
    # 2. If not, generate it
    else:
        with st.spinner(f"Agents are analyzing {st.session_state.transcript_context_length:,} characters of intelligence..."):
            if generate_situation_report:
                report = generate_situation_report(title, st.session_state.wargame_context)
                st.session_state[cache_key] = report
                st.rerun() # Rerun to display the cached content cleanly
            else:
                st.error("Backend function missing.")

def render_chatbot_page(agent_name):
    """
    Renders the chat interface for specific advisors.
    """
    st.header(f"{page_data['icon']} Advisor: {agent_name}")
    
    # Initialize chat history for this specific agent if needed
    history_key = f"chat_history_{agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        
    # Display History
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input
    if prompt := st.chat_input(f"Ask {agent_name}..."):
        # User Message
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Agent Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = get_agent(agent_name)
                if agent:
                    # We pass the full context only if it's the start or handled inside the agent logic
                    response = agent.get_response(prompt, context_text=st.session_state.wargame_context)
                    st.markdown(response)
                    st.session_state[history_key].append({"role": "assistant", "content": response})
                else:
                    st.error("Agent not found.")

# --- MAIN EXECUTION ---

if page_data['type'] == 'llm_static':
    render_llm_static_page(page_group, current_page_title)
elif page_data['type'] == 'chatbot':
    render_chatbot_page(current_page_title)
else:
    st.write("Page type not implemented.")