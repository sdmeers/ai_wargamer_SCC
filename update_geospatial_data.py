import json
import os
import sys

def update_geospatial_data():
    # Define file paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    kml_path = os.path.join(base_dir, 'data', 'wargame_locations.kml')
    json_path = os.path.join(base_dir, 'intelligence_analysis.json')

    print(f"Reading KML from: {kml_path}")
    print(f"Reading JSON from: {json_path}")

    # 1. Read KML content
    try:
        with open(kml_path, 'r', encoding='utf-8') as f:
            kml_content = f.read()
    except FileNotFoundError:
        print(f"Error: KML file not found at {kml_path}")
        sys.exit(1)

    # 2. Read JSON content
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file not found at {json_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file: {e}")
        sys.exit(1)

    # 3. Update each episode
    updated_count = 0
    for episode_key, episode_data in data.items():
        if isinstance(episode_data, dict):
            # Update or create the report_Geospatial key
            episode_data['report_Geospatial'] = kml_content
            updated_count += 1
            print(f"Updated {episode_key}")

    # 4. Save updated JSON
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"Successfully updated {updated_count} episodes in {json_path}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        sys.exit(1)

    # 5. Verification
    print("\n--- Verification ---")
    with open(json_path, 'r', encoding='utf-8') as f:
        verified_data = json.load(f)
    
    first_episode = list(verified_data.keys())[0]
    geospatial_data = verified_data[first_episode].get('report_Geospatial', '')
    
    if "Wellington Barracks" in geospatial_data:
        print("SUCCESS: 'Wellington Barracks' found in updated JSON.")
    else:
        print("FAILURE: 'Wellington Barracks' NOT found in updated JSON.")
        sys.exit(1)

    # Check for high precision coordinate (HMNB Clyde: -4.8200 vs -4.8170)
    # The KML file has -4.8200 for HMNB Clyde (Faslane)
    if "-4.8200" in geospatial_data:
         print("SUCCESS: High precision coordinate (-4.8200) found.")
    else:
         print("WARNING: High precision coordinate (-4.8200) NOT found. Please check KML content.")

if __name__ == "__main__":
    update_geospatial_data()
