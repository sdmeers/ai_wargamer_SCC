import streamlit as st
import json
import os
import time

# Import the Agent factory. Ensure agents.py is in the same directory.
try:
    from agents import get_agent
except ImportError:
    st.error("Backend module 'agents.py' not found. Please ensure it is created.")
    get_agent = None


# --- 1. CONFIGURATION, STYLING, AND DATA LOADING ---

st.set_page_config(
    page_title="AI Wargamer Interface (MVP Snapshot)",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a dark theme
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #E0E0E0; }
    [data-testid="stSidebar"] { background-color: #1E1E1E; }
    h1 { color: #FFD700; padding-top: 0px; margin-top: 0px; }
    h2, h3 { color: #A9A9A9; }
    .stTextInput > div > div > input { color: #E0E0E0; background-color: #2D2D2D; border: 1px solid #444444; }
    [data-testid="stChatMessage"] { background-color: #1E1E1E; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_frozen_snapshot():
    """
    Loads and concatenates the first three episodes into a single context string.
    This replaces the dynamic timeline logic.
    """
    files = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    
    full_context = "--- FULL WARGAME CONTEXT (Episodes 1-3 Snapshot) ---\n"
    base_path = "data" 
    valid_types = ['blue', 'red', 'explanation'] # Focus on core game segments
    
    for i, filename in enumerate(files):
        path = os.path.join(base_path, filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                full_context += f"\n=== EPISODE {i+1} SEGMENTS ===\n"
                
                for segment in data.get('segments', []):
                    if segment.get('type') in valid_types:
                        speaker = segment.get('type', 'UNKNOWN').upper()
                        text = segment.get('content', '')
                        full_context += f"[{speaker}]: {text}\n"
                        
            except Exception as e:
                st.warning(f"Could not load or parse {filename}: {e}")
    
    full_context += "\n--- END OF CONTEXT ---"
    return full_context

# Load the context once and store it
if 'wargame_context' not in st.session_state:
    with st.spinner("Loading Wargame Data (Episodes 1-3 Snapshot)..."):
        st.session_state['wargame_context'] = load_frozen_snapshot()
        st.session_state['transcript_context_length'] = len(st.session_state['wargame_context'])

# --- 2. NAVIGATION DATA STRUCTURE (Original Structure Maintained) ---

NAVIGATION = {
    "Scenario": {
        "Summary": {"icon": "📜", "type": "static"},
        "Transcripts": {"icon": "🎙️", "type": "static"},
        "Knowledge Graph": {"icon": "🧠", "type": "llm_static"},
    },
    "Situation Room": {
        "SITREP": {"icon": "📊", "type": "llm_static"},
        "SIGACTS": {"icon": "💥", "type": "llm_static"},
        "ORBAT": {"icon": "♟️", "type": "llm_static"},
        "Actions": {"icon": "👉", "type": "llm_static"},
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

# Session state management
DEFAULT_PAGE_ID = "Scenario - Summary"
if 'current_page_id' not in st.session_state:
    st.session_state.current_page_id = DEFAULT_PAGE_ID 

# --- 3. PAGE RENDERING FUNCTIONS ---

def get_group_and_title(unique_id):
    """Parses the unique ID back into its group and page title components."""
    try:
        group, title = unique_id.split(" - ", 1)
        return group, title
    except ValueError:
        return "Scenario", "Summary"

def render_static_page(group, title):
    """Renders a simple static placeholder page."""
    icon = NAVIGATION[group][title]["icon"]
    st.header(f"{icon} {group}: {title}")
    st.markdown("---")
    
    if title == "Transcripts":
        st.info("The transcripts are loaded as one complete context block (Episodes 1-3).")
        # Display the context as raw text
        st.text_area(
            "Full Wargame Context (Read Only)", 
            st.session_state['wargame_context'], 
            height=400, 
            disabled=True
        )
    else:
        st.markdown(f"### **Static Content**\nThis page contains **pre-defined information** about the project.")

def render_llm_static_page(group, title):
    """
    Renders a page for LLM-generated static reports (Situation Room).
    Uses hardcoded data for the MVP to ensure fast, predictable results.
    """
    icon = NAVIGATION[group][title]["icon"]
    st.header(f"{icon} {group}: {title}")
    st.markdown("---")
    
    st.info(f"Report for **{title}** - (Based on End of Episode 3 Snapshot)")
    
    # --- MVP HARDCODED REPORTS (for speed) ---
    if title == "SITREP":
        st.subheader("High-Level Situation Report")
        st.markdown("""
        The conflict has escalated to missile strikes on the UK mainland. Key actions include:
        - **Russian Strike:** Successful attacks on Portsmouth Naval Base, Faslane, and Heathrow Airport.
        - **UK Response:** Activation of full military readiness; Trident deployment; Cabinet debate on Article 5 invocation.
        - **Diplomatic:** NATO discussions ongoing, but US commitment appears contingent on certain actions.
        """)
    elif title == "ORBAT":
        st.subheader("Order of Battle (ORBAT)")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🔵 UK Forces (Blue)")
            st.dataframe([
                {"Asset": "HMS Queen Elizabeth", "Status": "Damaged/On Fire", "Location": "Portsmouth"},
                {"Asset": "F-35 Squadron", "Status": "Deployed/Active", "Location": "Sortie"},
                {"Asset": "Trident Sub 1", "Status": "At Sea", "Location": "Classified"},
            ])
        with col2:
            st.markdown("#### 🔴 Russian Forces (Red)")
            st.dataframe([
                {"Asset": "Northern Fleet", "Status": "Active", "Location": "North Atlantic"},
                {"Asset": "SSN Flotilla", "Status": "Hunting", "Location": "UK Waters"},
                {"Asset": "Airborne Missiles", "Status": "Expended", "Location": "Targets Reached"},
            ])
    else:
        st.markdown(f"**{title}** content requires an agent call to format the transcript context. For the MVP, this section is a placeholder.")

def render_chatbot_page(group, title):
    """Renders an interactive chatbot interface connected to the Wargame Agent."""
    icon = NAVIGATION[group][title]["icon"]
    st.header(f"{icon} **Advisor**: {title}")
    st.markdown("---")
    
    # Unique history key for this advisor
    history_key = f'messages_{title.replace(" ", "_")}'
    
    # Initialize chat history
    if history_key not in st.session_state:
        st.session_state[history_key] = [{"role": "assistant", "content": f"Greetings. I am the **{title}**. I have analyzed the entire Wargame scenario up to Episode 3. How can I advise you?"}]
    
    # Display chat history
    for message in st.session_state[history_key]:
        # Use a generic icon for assistant, no icon for user
        avatar = NAVIGATION['Advisors'][title]['icon'] if message["role"] == "assistant" else None
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input(f"Consult with the {title}..."):
        # 1. User Message
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant", avatar=NAVIGATION['Advisors'][title]['icon']):
            if not get_agent:
                st.error("Agent backend not loaded.")
            else:
                agent = get_agent(title) # Get the specific agent instance
                
                if agent:
                    with st.spinner(f"{title} is synthesizing the full scenario context..."):
                        try:
                            # Pass the *single, frozen* context
                            response_text = agent.chat(prompt, st.session_state['wargame_context'])
                            
                            st.markdown(response_text)
                            
                            # Save to history
                            st.session_state[history_key].append({"role": "assistant", "content": response_text})
                            
                        except Exception as e:
                            st.error(f"Error communicating with Agent: {e}")
                else:
                    st.warning(f"Agent '{title}' is not defined.")


# --- 4. STREAMLIT APPLICATION LAYOUT ---

# --- Sidebar (Navigation) ---
with st.sidebar:
    st.title("🤖 AI Wargamer ⚔️")
    st.caption("Hackathon MVP: Frozen State (Eps 1-3)")
    
    # --- Context Display (Replaces Timeline Slider) ---
    st.subheader("Wargame Context")
    st.info(f"Loaded {st.session_state.get('transcript_context_length', 0):,} characters of transcript data.")
    st.markdown("---")

    # --- Navigation Menu (Original Structure) ---
    for group, pages in NAVIGATION.items():
        st.subheader(group)
        for page_title, data in pages.items():
            # Generate a UNIQUE IDENTIFIER and KEY for each button
            unique_id = f"{group} - {page_title}"
            unique_key = f"nav_{group}_{page_title.replace(' ', '_')}"
            
            if st.button(f"{data['icon']} {page_title}", use_container_width=True, key=unique_key):
                # On click, set the unique ID to the session state
                st.session_state.current_page_id = unique_id
        st.markdown("---") # Visual separator between groups

# --- Main Content Area ---

# Retrieve the components from the stored unique ID
page_group, current_page_title = get_group_and_title(st.session_state.current_page_id)

# Render the appropriate content based on the page type
if page_group in NAVIGATION and current_page_title in NAVIGATION[page_group]:
    page_type = NAVIGATION[page_group][current_page_title]['type']

    if page_type == "static":
        render_static_page(page_group, current_page_title)
    elif page_type == "llm_static":
        render_llm_static_page(page_group, current_page_title)
    elif page_type == "chatbot":
        render_chatbot_page(page_group, current_page_title)
else:
    st.title("Welcome to the AI Wargamer Interface")
    st.info("Select a page from the sidebar to view scenario data or consult with an Advisor.")