import streamlit as st
import json
import os

# --- CONSTANTS ---
OUTPUT_FILE = "intelligence_analysis.json"

# --- HELPER FUNCTIONS ---

def load_intelligence_data():
    """Loads the intelligence analysis data from the JSON file."""
    if not os.path.exists(OUTPUT_FILE):
        st.error(f"Error: {OUTPUT_FILE} not found. Please run precompute_intelligence.py first.")
        return None
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        st.error(f"Error loading {OUTPUT_FILE}: {e}")
        return None

def save_intelligence_data(data):
    """Saves the intelligence analysis data back to the JSON file."""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        return True
    except IOError as e:
        st.error(f"Error saving data to {OUTPUT_FILE}: {e}")
        return False

# --- STREAMLIT UI ---

st.set_page_config(layout="wide")
st.title("Manual Intelligence Override")

st.info(f"This tool allows you to manually edit and overwrite the pre-computed intelligence reports stored in `{OUTPUT_FILE}`.")

data = load_intelligence_data()

if data:
    # Use session state to hold the currently selected text
    if 'current_text' not in st.session_state:
        st.session_state.current_text = ""

    agent_keys = sorted(data.keys())
    
    # Dropdown to select the agent/report
    selected_agent = st.selectbox(
        "Select Agent/Report to Edit:",
        options=agent_keys,
        index=0,
        key="selected_agent_key"
    )

    # When selection changes, update the text in session state
    if selected_agent != st.session_state.get('last_selected_agent'):
        st.session_state.last_selected_agent = selected_agent
        st.session_state.current_text = data.get(selected_agent, "")

    st.subheader(f"Editing: `{selected_agent}`")

    # Text area for editing
    edited_text = st.text_area(
        "Report Content:",
        value=st.session_state.current_text,
        height=500,
        key="text_editor"
    )

    # Save button
    if st.button("Save and Overwrite Changes"):
        if selected_agent:
            data[selected_agent] = edited_text
            if save_intelligence_data(data):
                st.success(f"Successfully updated `{selected_agent}` in `{OUTPUT_FILE}`.")
                # Update session state with the saved text
                st.session_state.current_text = edited_text
            else:
                st.error("Failed to save changes.")
        else:
            st.warning("No agent selected.")
