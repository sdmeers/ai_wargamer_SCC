import streamlit as st
import json
import os
import sys
import time
import logging
import concurrent.futures

# --- PATH SETUP ---
sys.path.append(os.path.dirname(__file__))

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- IMPORTS ---
AGENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'agents.py')

if not os.path.exists(AGENTS_FILE_PATH):
    st.error(f"FATAL: 'agents.py' not found at {AGENTS_FILE_PATH}.")
    st.stop()
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
        st.stop()

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
        "SITREP": {"icon": "📊", "type": "llm_static"},
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
    Loads transcripts and runs batch processing in HIGH PARALLEL.
    """
    # 1. LOAD FILES
    logger.info("--- STARTING DATA LOAD ---")
    files_to_load = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    
    combined_text = ""
    loaded_count = 0
    
    progress_text = "Reading Transcripts..."
    my_bar = st.sidebar.progress(0, text=progress_text)
    
    for filename in files_to_load:
        path = filename if os.path.exists(filename) else os.path.join("data", filename)
        if not os.path.exists(path):
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
            logger.error(f"Error loading {filename}: {e}")
            st.sidebar.error(f"Error loading {filename}: {e}")

    st.session_state.wargame_context = combined_text
    st.session_state.transcript_context_length = len(combined_text)
    
    if loaded_count == 0:
        st.sidebar.error("No files loaded.")
        return 0

    # 2. HIGH PARALLEL BATCH ANALYSIS
    logger.info("--- STARTING HIGH-SPEED PARALLEL GENERATION ---")
    
    # Define tasks
    tasks = []
    for report_name in SITUATION_PROMPTS:
        tasks.append(("report", report_name))
    for advisor_name in ADVISOR_DEFINITIONS:
        tasks.append(("advisor", advisor_name))

    total_tasks = len(tasks)
    completed_tasks = 0
    
    # Define a helper to be run in threads
    def process_task(task_info):
        t_type, t_name = task_info
        result_key = ""
        result_content = ""
        
        # Try generating up to 2 times (Simple Retry Logic)
        attempts = 2
        for i in range(attempts):
            try:
                if t_type == "report":
                    result_key = f"report_{t_name}"
                    result_content = generate_situation_report(t_name, combined_text)
                elif t_type == "advisor":
                    result_key = f"briefing_{t_name}"
                    result_content = generate_advisor_briefing(t_name, combined_text)
                
                # If we get here, it worked
                break
            except Exception as e:
                logger.warning(f"Task {t_name} failed attempt {i+1}: {e}")
                if i < attempts - 1:
                    time.sleep(2) # Wait 2 seconds before retry
                else:
                    result_content = f"Generation Failed after retries. Error: {e}"
            
        return result_key, result_content

    # --- INCREASED PARALLELISM ---
    # Increased to 8. This will be much faster but monitors for 429 errors.
    MAX_WORKERS = 8
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_task = {executor.submit(process_task, task): task for task in tasks}
        
        for future in concurrent.futures.as_completed(future_to_task):
            try:
                key, content = future.result()
                st.session_state[key] = content
                completed_tasks += 1
                
                pct = int((completed_tasks / total_tasks) * 100)
                my_bar.progress(pct, text=f"Generated: {future_to_task[future][1]} ({completed_tasks}/{total_tasks})")
                
            except Exception as exc:
                logger.error(f"Thread Exception: {exc}")

    my_bar.empty()
    st.session_state.data_loaded = True
    logger.info("--- DATA LOAD COMPLETE ---")
    return loaded_count

# --- SIDEBAR ---
with st.sidebar:
    st.title("Wargame OS")
    
    if st.button("INITIALIZE / RELOAD INTELLIGENCE", type="primary"):
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
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")
    cache_key = f"report_{title}"
    
    if cache_key in st.session_state:
        st.markdown(st.session_state[cache_key])
    else:
        if not st.session_state.data_loaded:
            st.info("System Offline. Please click 'INITIALIZE / RELOAD INTELLIGENCE' in the sidebar.")
        else:
            st.warning("Report generation pending or failed. Check logs.")

def render_chatbot_page(agent_name):
    st.header(f"{page_data['icon']} Advisor: {agent_name}")
    
    if not st.session_state.data_loaded:
        st.info("Advisor Offline. Please initialize intelligence in the sidebar.")
        return

    briefing_key = f"briefing_{agent_name}"
    if briefing_key in st.session_state:
        with st.expander("📜 Initial Strategic Assessment", expanded=True):
            st.markdown(st.session_state[briefing_key])
    else:
         st.warning("Briefing unavailable. You can still chat below.")
    
    st.markdown("---")
    st.caption("Operational Chat Channel - Secure Line Open")

    history_key = f"chat_history_{agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    if prompt := st.chat_input(f"Ask {agent_name} for clarification..."):
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent = get_agent(agent_name)
                if agent:
                    response = agent.get_response(prompt, context_text=st.session_state.wargame_context)
                    st.markdown(response)
                    st.session_state[history_key].append({"role": "assistant", "content": response})
                else:
                    st.error("Agent connection failed.")

if page_data['type'] == 'llm_static':
    render_llm_static_page(page_group, current_page_title)
elif page_data['type'] == 'chatbot':
    render_chatbot_page(current_page_title)
else:
    st.write("Page type not implemented.")