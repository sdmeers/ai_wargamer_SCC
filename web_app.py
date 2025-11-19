import streamlit as st
import json
import os
import sys
import time

# --- PATH SETUP ---
sys.path.append(os.path.dirname(__file__))

# --- IMPORTS ---
AGENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'agents.py')

if not os.path.exists(AGENTS_FILE_PATH):
    st.error(f"FATAL: 'agents.py' not found at {AGENTS_FILE_PATH}.")
    get_agent = None
    generate_situation_report = None
    generate_advisor_briefing = None
    SITUATION_PROMPTS = {}
    ADVISOR_DEFINITIONS = {}
else:
    try:
        from agents import (
            get_agent, 
            generate_situation_report, 
            generate_advisor_briefing,
            SITUATION_PROMPTS,
            ADVISOR_DEFINITIONS
        )
    except ImportError as e:
        st.error(f"FATAL: Failed to import from agents.py: {e}")

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="AI Wargame Situation Room")

# --- SESSION STATE INIT ---
if 'current_page_id' not in st.session_state:
    st.session_state.current_page_id = "Situation Room - SITREP"
if 'wargame_context' not in st.session_state:
    st.session_state.wargame_context = ""
if 'transcript_context_length' not in st.session_state:
    st.session_state.transcript_context_length = 0
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# --- NAVIGATION STRUCTURE ---
NAVIGATION = {
    "Situation Room": {
        "Sitrep": {"icon": "📊", "type": "llm_static"},
        "SIGACTS": {"icon": "💥", "type": "llm_static"},
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

def load_and_analyze_data():
    """
    1. Loads transcripts.
    2. Runs a batch process to pre-generate ALL Situation Reports.
    3. Runs a batch process to pre-generate ALL Advisor Briefings.
    """
    # 1. LOAD FILES
    files_to_load = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    
    combined_text = ""
    loaded_count = 0
    
    progress_text = "Loading Transcripts..."
    my_bar = st.sidebar.progress(0, text=progress_text)
    
    for filename in files_to_load:
        if os.path.exists(filename):
            path = filename
        elif os.path.exists(os.path.join("data", filename)):
            path = os.path.join("data", filename)
        else:
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        if 'text' in entry: 
                            combined_text += f"{entry.get('speaker', 'Unknown')}: {entry['text']}\n"
                        elif 'content' in entry:
                            combined_text += f"{entry['content']}\n"
                elif isinstance(data, dict):
                     combined_text += str(data)
                loaded_count += 1
                combined_text += "\n--- END OF EPISODE ---\n"
        except Exception as e:
            st.sidebar.error(f"Error loading {filename}: {e}")

    st.session_state.wargame_context = combined_text
    st.session_state.transcript_context_length = len(combined_text)
    
    if loaded_count == 0:
        st.sidebar.error("No files loaded.")
        return 0

    # 2. BATCH ANALYSIS (Pre-generation)
    total_tasks = len(SITUATION_PROMPTS) + len(ADVISOR_DEFINITIONS)
    current_task = 0
    
    # A. Generate Situation Room Reports
    for report_name in SITUATION_PROMPTS:
        current_task += 1
        progress_percent = int((current_task / total_tasks) * 100)
        my_bar.progress(progress_percent, text=f"Analysing: {report_name}...")
        
        # Generate and Cache
        cache_key = f"report_{report_name}"
        if generate_situation_report:
            report_content = generate_situation_report(report_name, combined_text)
            st.session_state[cache_key] = report_content
    
    # B. Generate Advisor Briefings
    for advisor_name in ADVISOR_DEFINITIONS:
        current_task += 1
        progress_percent = int((current_task / total_tasks) * 100)
        my_bar.progress(progress_percent, text=f"Consulting: {advisor_name}...")
        
        # Generate and Cache
        cache_key = f"briefing_{advisor_name}"
        if generate_advisor_briefing:
            briefing_content = generate_advisor_briefing(advisor_name, combined_text)
            st.session_state[cache_key] = briefing_content

    my_bar.empty()
    st.session_state.data_loaded = True
    return loaded_count

# --- SIDEBAR ---
with st.sidebar:
    st.title("Wargame OS")
    
    # Initialize Button
    if st.button("INITIALIZE / RELOAD INTELLIGENCE", type="primary"):
        # Clear old cache
        keys_to_delete = [k for k in st.session_state.keys() if k.startswith("report_") or k.startswith("briefing_")]
        for k in keys_to_delete:
            del st.session_state[k]
            
        count = load_and_analyze_data()
        if count > 0:
            st.success(f"Intelligence Processed. {count} Files.")
            st.rerun()

    if st.session_state.data_loaded:
        st.success("✅ Intelligence Loaded & Analyzed")
    else:
        st.warning("⚠️ No Data. Click Initialize.")

    st.markdown("---")

    # Navigation Menu
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

# --- PAGE ROUTER ---

current_id = st.session_state.current_page_id
try:
    page_group, current_page_title = current_id.split(" - ")
    page_data = NAVIGATION[page_group][current_page_title]
except:
    page_group = "Situation Room"
    current_page_title = "SITREP"
    page_data = NAVIGATION["Situation Room"]["SITREP"]

# --- RENDER FUNCTIONS ---

def render_llm_static_page(group, title):
    """
    Renders a pre-generated situation report.
    """
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")
    
    cache_key = f"report_{title}"
    
    if cache_key in st.session_state:
        st.markdown(st.session_state[cache_key])
    else:
        if not st.session_state.data_loaded:
            st.info("System Offline. Please click 'INITIALIZE / RELOAD INTELLIGENCE' in the sidebar.")
        else:
            st.warning("Report generation pending or failed. Try reloading.")

def render_chatbot_page(agent_name):
    """
    Renders the Advisor page with a pre-generated briefing + interactive chat.
    """
    st.header(f"{page_data['icon']} Advisor: {agent_name}")
    
    if not st.session_state.data_loaded:
        st.info("Advisor Offline. Please initialize intelligence in the sidebar.")
        return

    # 1. Show the Pre-Generated Briefing
    briefing_key = f"briefing_{agent_name}"
    if briefing_key in st.session_state:
        with st.expander("📜 Initial Strategic Assessment", expanded=True):
            st.markdown(st.session_state[briefing_key])
    
    st.markdown("---")
    st.caption("Operational Chat Channel - Secure Line Open")

    # 2. Chat Interface
    history_key = f"chat_history_{agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        
    # Display History
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat Input
    if prompt := st.chat_input(f"Ask {agent_name} for clarification..."):
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = get_agent(agent_name)
                if agent:
                    # Context is only needed if you want to re-inject it, 
                    # but the agent instance maintains history in `chat_session`.
                    # Ideally, for a robust chat, we inject context invisibly in the first message
                    # or use the system prompt. 
                    # Here we pass it to get_response which handles context injection logic.
                    response = agent.get_response(prompt, context_text=st.session_state.wargame_context)
                    st.markdown(response)
                    st.session_state[history_key].append({"role": "assistant", "content": response})
                else:
                    st.error("Agent connection failed.")

# --- MAIN EXECUTION ---

if page_data['type'] == 'llm_static':
    render_llm_static_page(page_group, current_page_title)
elif page_data['type'] == 'chatbot':
    render_chatbot_page(current_page_title)
else:
    st.write("Page type not implemented.")