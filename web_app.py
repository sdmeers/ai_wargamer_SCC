import streamlit as st
import time
# Import the new backend modules
# Note: Ensure game_state.py and agents.py are in the same directory
try:
    from game_state import GameStateManager
    from agents import get_agent
except ImportError:
    # Fallback to prevent crash if files aren't created yet
    st.error("Backend modules (game_state.py, agents.py) not found. Please ensure they are created.")
    GameStateManager = None
    get_agent = None

# --- 1. CONFIGURATION AND INITIAL SETUP ---

st.set_page_config(
    page_title="AI Wargamer Interface",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a modern, dark theme
st.markdown("""
<style>
    /* Main Content Area Styling */
    .stApp {
        background-color: #121212;
        color: #E0E0E0;
    }
    [data-testid="stSidebar"] {
        background-color: #1E1E1E;
    }
    h1 {
        color: #FFD700;
        padding-top: 0px;
        margin-top: 0px;
    }
    h2, h3 {
        color: #A9A9A9;
    }
    .stTextInput > div > div > input {
        color: #E0E0E0;
        background-color: #2D2D2D;
        border: 1px solid #444444;
    }
    [data-testid="stChatMessage"] {
        background-color: #1E1E1E; 
    }
</style>
""", unsafe_allow_html=True)


# --- 2. NAVIGATION DATA STRUCTURE ---

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

# Initialize Game State Manager
if 'game_manager' not in st.session_state and GameStateManager:
    # Ensure you have a 'data' folder with your JSONs
    st.session_state.game_manager = GameStateManager(data_dir="data")


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
        st.info("Raw transcript data is processed by the Game State Manager.")
        # Optional: Display raw text if needed
        # st.text_area("Current Context", st.session_state.get('transcript_context', ''), height=400)
    else:
        st.markdown(f"""
        ### **Static Content**
        This page contains **pre-defined information**.
        """)

def render_llm_static_page(group, title):
    """Renders a page for LLM-generated static reports (Situation Room)."""
    icon = NAVIGATION[group][title]["icon"]
    st.header(f"{icon} {group}: {title}")
    st.markdown("---")
    st.markdown(f"### **{title} Report**")
    
    # Placeholder for Step 2 (Situation Room Agents)
    # In the next phase, we will connect 'agents.py' analyze_situation() here.
    
    st.info(f"Generating {title} based on current Episode state...")
    
    if title == "ORBAT":
        st.subheader("Friendly Order of Battle (Mock Data)")
        st.table({
            'Unit': ['1st Mechanized Brigade', '3rd Air Cavalry Regiment', 'Special Operations Task Force'],
            'Strength': ['Full', '75%', 'Full'],
            'Readiness': ['High', 'Medium', 'High']
        })
    else:
        st.markdown(f"**Report Excerpt for {title}:** *The latest intelligence from the podcast transcript indicates... [Agent Output Placeholder]*")

def render_chatbot_page(group, title):
    """Renders an interactive chatbot interface connected to Vertex AI."""
    icon = NAVIGATION[group][title]["icon"]
    st.header(f"{icon} **Advisor**: {title}")
    st.markdown("---")
    
    # Unique history key for this advisor
    history_key = f'messages_{title.replace(" ", "_")}'
    
    # Initialize chat history
    if history_key not in st.session_state:
        st.session_state[history_key] = [{"role": "assistant", "content": f"Greetings. I am the **{title}**. How can I assist you?"}]
    
    # Display chat history
    for message in st.session_state[history_key]:
        with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else None):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input(f"Consult with the {title}..."):
        # 1. User Message
        st.session_state[history_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Assistant Response
        with st.chat_message("assistant", avatar="🤖"):
            if not get_agent:
                st.error("Agent backend not loaded.")
            else:
                # Get the specific agent instance
                # Note: In a production app, you might cache the agent object itself to keep session memory active
                agent = get_agent(title)
                
                if agent:
                    with st.spinner(f"{title} is analyzing the transcript context..."):
                        try:
                            # Retrieve current context from the slider selection
                            current_context = st.session_state.get('transcript_context', '')
                            
                            # Call the Agent
                            response_text = agent.chat(prompt, current_context)
                            
                            st.markdown(response_text)
                            
                            # Save to history
                            st.session_state[history_key].append({"role": "assistant", "content": response_text})
                            
                        except Exception as e:
                            st.error(f"Error communicating with Agent: {e}")
                else:
                    st.warning(f"Agent '{title}' is not yet defined in agents.py")


# --- 4. STREAMLIT APPLICATION LAYOUT ---

# --- Sidebar (Navigation & Timeline) ---
with st.sidebar:
    st.title("🤖 AI Wargamer ⚔️")
    
    # --- TIMELINE CONTROL (New) ---
    st.subheader("Timeline Control")
    # Slider to select the current episode state (1 to 3 based on your files)
    selected_episode = st.slider("Current State (Episode End)", min_value=1, max_value=3, value=1)
    st.caption(f"Simulating state at end of Episode {selected_episode}")
    
    # Update Context based on slider
    if st.session_state.get('game_manager'):
        transcript_context = st.session_state.game_manager.get_transcript_context(
            up_to_episode=selected_episode,
            include_types=['blue', 'red', 'explanation', 'commentary']
        )
        st.session_state['transcript_context'] = transcript_context
    else:
        st.session_state['transcript_context'] = "Context not loaded (Game Manager missing)."

    st.markdown("---")

    # --- Navigation Menu ---
    for group, pages in NAVIGATION.items():
        st.subheader(group)
        for page_title, data in pages.items():
            unique_id = f"{group} - {page_title}"
            unique_key = f"nav_{group}_{page_title.replace(' ', '_')}"
            
            if st.button(f"{data['icon']} {page_title}", use_container_width=True, key=unique_key):
                st.session_state.current_page_id = unique_id
        st.markdown("---")

# --- Main Content Area ---

page_group, current_page_title = get_group_and_title(st.session_state.current_page_id)

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
    st.info("Select a page from the sidebar to view scenario data, SITREP details, or consult with an Advisor.")