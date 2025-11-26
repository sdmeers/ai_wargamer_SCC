import streamlit as st
import os
import sys
import json

# Mock session state
if 'all_transcripts' not in st.session_state:
    st.session_state.all_transcripts = []
if 'all_analysis' not in st.session_state:
    st.session_state.all_analysis = {}
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Import web_app
import web_app

def verify_split_loading():
    print("Testing load_data_fast()...")
    success = web_app.load_data_fast()
    
    if not success:
        print("FAIL: load_data_fast returned False")
        return

    transcripts = st.session_state.all_transcripts
    print(f"Loaded {len(transcripts)} transcript entries.")
    
    if len(transcripts) == 0:
        print("FAIL: No transcripts loaded.")
        return

    # Check for episodes
    episodes_found = set()
    for entry in transcripts:
        ep = entry.get('episode')
        if ep:
            episodes_found.add(ep)
            
    print(f"Episodes found: {sorted(list(episodes_found))}")
    
    expected_episodes = {'S2E1', 'S2E2', 'S2E3', 'S2E4', 'S2E5'}
    if expected_episodes.issubset(episodes_found):
        print("SUCCESS: All expected episodes loaded.")
    else:
        print(f"FAIL: Missing episodes. Expected {expected_episodes}, found {episodes_found}")

if __name__ == "__main__":
    verify_split_loading()
