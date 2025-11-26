import streamlit as st
import streamlit.components.v1 as components 
import json
import os
import sys
import logging
import re
import base64
import mimetypes
# Import necessary for Streamlit caching
from functools import lru_cache

# --- PATH SETUP ---
sys.path.append(os.path.dirname(__file__))

# --- LOGGING ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# --- IMPORTS ---
AGENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'agents.py')
if not os.path.exists(AGENTS_FILE_PATH):
    st.error("FATAL: agents.py not found.")
    st.stop()
else:
    try:
        # Import the factory function from agents.py
        from agents import get_agent, ADVISOR_DEFINITIONS 
    except ImportError as e:
        st.error(f"FATAL: Import failed: {e}")
        st.stop()

# --- CONFIG ---
st.set_page_config(layout="wide", page_title="AI Wargame Situation Room")
PRECOMPUTED_FILE = "intelligence_analysis.json"
TRANSCRIPT_VIEWER_HTML = "transcript_viewer.html"
SCENARIO_MD_FILE = "wargame_scenario.md" # Define the scenario file path

# --- SESSION STATE ---
if 'current_page_id' not in st.session_state:
    st.session_state.current_page_id = "Overview - Scenario" 
if 'wargame_context' not in st.session_state:
    st.session_state.wargame_context = []
if 'all_transcripts' not in st.session_state:
    st.session_state.all_transcripts = []
if 'all_analysis' not in st.session_state:
    st.session_state.all_analysis = {}
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'transcript_context_length' not in st.session_state:
    st.session_state.transcript_context_length = 0
if 'selected_episode' not in st.session_state:
    st.session_state.selected_episode = 3

# --- CACHED AGENT CREATION ---
@st.cache_resource
def initialize_wargame_agent(agent_name):
    """
    Initializes and caches a WargameAgent instance. 
    This prevents running vertexai.init() and model loading on every rerun.
    """
    if agent_name in ADVISOR_DEFINITIONS:
        st.toast(f"Initializing {agent_name}...", icon=ADVISOR_DEFINITIONS[agent_name]['icon'])
    
    agent = get_agent(agent_name)
    if agent:
        agent.start_new_session()
    return agent

# --- NAVIGATION ---
NAVIGATION = {
    "Overview": {
        "Scenario": {"icon": "📰", "type": "static", "file": SCENARIO_MD_FILE},
        "Transcript": {"icon": "📖", "type": "transcript_view", "file": TRANSCRIPT_VIEWER_HTML},
    },
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
    },
    "Tools": {
        "Knowledge Graph": {"icon": "🕸️", "type": "knowledge_graph", "file": "wargame_network.html"},
    }
}

def load_data_fast():
    """
    Loads 1) Raw transcripts into a Python list of objects and 2) Precomputed Analysis JSON.
    """
    # 1. Load Transcripts into a structured list
    transcript_file_to_load = "the_wargame_s2e1+2+3_clean_transcript.json"
    all_transcript_entries = []
    
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    path = os.path.join(data_dir, transcript_file_to_load)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                if isinstance(data, list):
                    all_transcript_entries.extend(data)
                else:
                    logger.warning(f"Transcript file {transcript_file_to_load} content is not a list. Skipping.")
                
        except Exception as e:
            logger.warning(f"Failed to load or parse transcript file {transcript_file_to_load}: {e}")
    else:
        logger.warning(f"Transcript file not found: {path}")

    # Store the full list in session state
    st.session_state.all_transcripts = all_transcript_entries
    
    # 2. Load Precomputed Analysis
    precomputed_path = os.path.join(os.path.dirname(__file__), PRECOMPUTED_FILE)
    if os.path.exists(precomputed_path):
        try:
            with open(precomputed_path, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)
                st.session_state.all_analysis = analysis_data
                st.session_state.data_loaded = True
                return True
        except Exception as e:
            st.error(f"Error reading {PRECOMPUTED_FILE}: {e}")
            return False
    else:
        logger.warning(f"Precomputed analysis file not found: {precomputed_path}")
        return False

def update_state_for_episode():
    """
    Updates the session state based on the selected episode.
    Filters transcripts and loads the correct intelligence reports.
    """
    episode = st.session_state.selected_episode
    
    # 1. Update Intelligence Reports
    episode_key = f"episode_{episode}"
    if episode_key in st.session_state.all_analysis:
        current_analysis = st.session_state.all_analysis[episode_key]
        for key, content in current_analysis.items():
            st.session_state[key] = content
    else:
        # Fallback or clear if data missing
        pass

    # 2. Filter Transcripts
    # Define which episodes to include for each slider position
    # The transcript file uses "S2E1", "S2E2", "S2E3"
    episodes_to_include = []
    for i in range(1, episode + 1):
        episodes_to_include.append(f"S2E{i}")
        
    filtered_transcripts = [
        entry for entry in st.session_state.all_transcripts 
        if entry.get('episode') in episodes_to_include
    ]
    
    st.session_state.wargame_context = filtered_transcripts

    # Calculate word count
    total_words = 0
    for entry in filtered_transcripts:
        text = entry.get('text', '') or entry.get('content', '')
        if isinstance(text, str):
            total_words += len(text.split())
            
    st.session_state.transcript_context_length = total_words

# --- PAGE RENDERING FUNCTIONS ---

def get_page_data_from_id(page_id):
    """Utility to safely retrieve page data from a page ID."""
    try:
        group, title = page_id.split(" - ")
        return group, title, NAVIGATION[group][title]
    except (ValueError, KeyError):
        # Fallback to default page if ID is malformed or not found
        return "Overview", "Scenario", NAVIGATION["Overview"]["Scenario"]


def render_static_page(group, title, file_path):
    """Renders content from a static file (e.g., Markdown)."""
    page_data = get_page_data_from_id(st.session_state.current_page_id)[2] # Re-fetch data for icon
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")
    
    try:
        # NOTE: File access should now be relative to the web_app.py script location
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Convert local image paths in markdown to base64 to ensure they render in Docker
        def path_to_base64(match):
            tag_start = match.group(1)
            img_path = match.group(2)
            full_img_path = os.path.join(os.path.dirname(__file__), img_path)
            try:
                with open(full_img_path, "rb") as f:
                    img_bytes = f.read()
                mime_type, _ = mimetypes.guess_type(full_img_path)
                if mime_type is None: return match.group(0) 
                base64_str = base64.b64encode(img_bytes).decode()
                return f'{tag_start}data:{mime_type};base64,{base64_str}"'
            except FileNotFoundError:
                return match.group(0)

        content = re.sub(r'(<img\s[^>]*src=")([^"]+)"', path_to_base64, content, flags=re.IGNORECASE)

        # --- START: MERMAID DIAGRAM RENDERING (Robust Method) ---
        mermaid_pattern = re.compile(r'```mermaid(.*?)```', re.DOTALL)
        match = mermaid_pattern.search(content)
        
        mermaid_code = ""
        if match:
            mermaid_code = match.group(1)
            # Remove the mermaid block from the main content string
            content = mermaid_pattern.sub("", content)
        # --- END: MERMAID DIAGRAM RENDERING ---

        # Render the main markdown content (now without the mermaid block)
        st.markdown(content, unsafe_allow_html=True)

        # If mermaid code was found, render it in a dedicated component
        if mermaid_code:
            components.html(f"""
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                <pre class="mermaid">
                    {mermaid_code}
                </pre>
                <script>
                    mermaid.initialize({{ startOnLoad: true }});
                </script>
            """, height=600, scrolling=True)
            
    except FileNotFoundError:
        st.error(f"Error: Static content file '{file_path}' not found at {full_path}. Please ensure the file exists in the deployment package.")
        st.markdown(f"***NOTE:*** *If this is the Scenario page, ensure **{SCENARIO_MD_FILE}** is present.*")


def render_transcript_page(group, title, file_path):
    """Renders the transcript by injecting data directly into the HTML viewer."""
    page_data = get_page_data_from_id(st.session_state.current_page_id)[2] # Re-fetch data for icon
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")

    # Check if data loading was successful
    if not st.session_state.wargame_context or not isinstance(st.session_state.wargame_context, list):
        st.warning("Transcript data could not be loaded or is in an incorrect format.")
        return

    try:
        # Load the HTML template from the file
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            html_template = f.read()

        # --- DATA INJECTION ---
        # 1. Get the data, which is a Python list of objects.
        context_to_send = st.session_state.wargame_context
        
        # 2. Serialize the list into a JSON string.
        json_string = json.dumps(context_to_send)

        # 3. Replace the placeholder in the HTML.
        html_with_data = html_template.replace(
            '`%%TRANSCRIPT_DATA_PLACEHOLDER%%`',
            json_string
        )

        # 4. Dynamically calculate height to avoid nested scrollbars
        # Estimate: 250px for header/legend + 40px per transcript line
        num_lines = len(context_to_send)
        estimated_height = 250 + (num_lines * 40)

        # 5. Embed the HTML component with the data now included.
        components.html(
            html_with_data,
            height=estimated_height, 
            scrolling=False 
        )

    except FileNotFoundError:
        st.error(f"Error: Transcript viewer HTML file '{file_path}' not found.")
        st.markdown("Please ensure `transcript_viewer.html` exists in the deployment package.")


def render_knowledge_graph(group, title, file_path):
    """
    Renders the knowledge graph by embedding the HTML file directly.
    """
    page_data = get_page_data_from_id(st.session_state.current_page_id)[2] # Re-fetch data for icon
    st.header(f"{page_data['icon']} {group}: {title}")
    st.markdown("---")

    try:
        # Load the HTML template from the file
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            html_template = f.read()

        # Embed the HTML component
        st.info("The Knowledge Graph is interactive. Scroll within the viewer to explore the network.")
        components.html(
            html_template,
            height=800, 
            scrolling=True 
        )
        
    except FileNotFoundError:
        st.error(f"Error: Knowledge Graph HTML file '{file_path}' not found.")
        st.markdown("Please ensure `wargame_network.html` exists in the deployment package.")


def render_llm_static_page(group, title):
    """Renders precomputed reports generated by the LLM."""
    page_data = get_page_data_from_id(st.session_state.current_page_id)[2] # Re-fetch data for icon
    st.header(f"{page_data['icon']} {group}: {title} Report")
    st.markdown("---")
    
    cache_key = f"report_{title}"
    
    if cache_key in st.session_state:
        st.markdown(st.session_state[cache_key])
    else:
        st.warning("Intelligence data not found. Ensure precompute_intelligence.py has been run and the data is loaded.")


def render_chatbot_page(agent_name):
    """Renders the interactive chatbot interface for an advisor."""
    page_data = get_page_data_from_id(st.session_state.current_page_id)[2] # Re-fetch data for icon
    st.header(f"{page_data['icon']} Advisor: {agent_name}")
    
    # Robustly find the briefing key, trying both space and underscore formats
    # to handle inconsistency in the source JSON file.
    key_with_space = f"briefing_{agent_name}"
    key_with_underscore = f"briefing_{agent_name.replace(' ', '_')}"
    
    briefing_content = None
    if key_with_space in st.session_state:
        briefing_content = st.session_state[key_with_space]
    elif key_with_underscore in st.session_state:
        briefing_content = st.session_state[key_with_underscore]

    if briefing_content:
        with st.expander("📜 Initial Strategic Assessment", expanded=True):
            st.markdown(briefing_content)
    
    st.markdown("---")
    st.caption("Operational Chat Channel - Secure Line Open")

    history_key = f"chat_history_{agent_name}"
    if history_key not in st.session_state:
        st.session_state[history_key] = []
        
    # Display chat messages from history
    for msg in st.session_state[history_key]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Handle user input
    if prompt := st.chat_input(f"Ask {agent_name}..."):
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner(f"{agent_name} is synthesizing intelligence..."):
                agent = initialize_wargame_agent(agent_name)
                
                if agent:
                    # Pass the full wargame context to the agent
                    response = agent.get_response(prompt, context_text=st.session_state.wargame_context)
                    st.markdown(response)
                    st.session_state[history_key].append({"role": "assistant", "content": response})
                else:
                    st.error("Agent connection failed. Check Vertex AI initialization.")


# --- SIDEBAR ---
with st.sidebar:
    st.title("Wargame OS")
    # Data Loading Check
    if not st.session_state.data_loaded:
        with st.spinner("Initializing system and loading intelligence data..."):
            success = load_data_fast()
            if success:
                st.success("System Online (Cached Data)")
            else:
                if not os.path.exists(os.path.join(os.path.dirname(__file__), PRECOMPUTED_FILE)):
                    st.error(f"Cache missing: {PRECOMPUTED_FILE}")
                else:
                    st.warning("Data loading failed.")
                
                if st.button("Retry Load"):
                    st.rerun()

    st.info(f"Loaded {st.session_state.transcript_context_length:,} words of transcript data.")
    
    # Time Slider
    st.markdown("### ⏳ Time Travel")
    selected_episode = st.select_slider(
        "Current Episode State",
        options=[1, 2, 3, 4, 5],
        value=st.session_state.selected_episode,
        key="episode_slider"
    )
    
    # Update state if slider changed
    if selected_episode != st.session_state.selected_episode:
        st.session_state.selected_episode = selected_episode
        update_state_for_episode()
        st.rerun()

    # Ensure state is updated on first load or reload
    if st.session_state.data_loaded:
        update_state_for_episode()

    st.markdown("---")

    # Navigation Menu
    for group, pages in NAVIGATION.items():
        st.subheader(group)
        for page_title, data in pages.items():
            unique_id = f"{group} - {page_title}"
            is_current = st.session_state.current_page_id == unique_id
            button_key = f"nav_btn_{unique_id.replace(' ', '_').replace('-', '_')}"

            if is_current:
                st.markdown(f"**👉 {data['icon']} {page_title}**")
            else:
                if st.button(f"{data['icon']} {page_title}", key=button_key, use_container_width=True):
                    st.session_state.current_page_id = unique_id
                    st.rerun()
        st.markdown("---")

# --- MAIN CONTENT AREA ---

# Determine the current page
page_group, current_page_title, page_data = get_page_data_from_id(st.session_state.current_page_id)

# --- Render the appropriate content based on the determined page data ---
page_type = page_data['type']

if page_type == 'static':
    render_static_page(page_group, current_page_title, page_data.get('file'))
elif page_type == 'transcript_view':
    render_transcript_page(page_group, current_page_title, page_data.get('file'))
elif page_type == 'knowledge_graph':
    render_knowledge_graph(page_group, current_page_title, page_data.get('file'))
elif page_type == 'llm_static':
    render_llm_static_page(page_group, current_page_title)
elif page_type == 'chatbot':
    render_chatbot_page(current_page_title)

# If the page type is unexpected (shouldn't happen with the current logic), default to Scenario
else:
    render_static_page("Overview", "Scenario", NAVIGATION["Overview"]["Scenario"].get('file'))