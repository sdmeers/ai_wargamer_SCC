import json
import os
import re

def split_transcripts():
    input_file = 'data/the_wargame_s2e1+2+3_clean_transcript.json'
    output_dir = 'data'
    
    print(f"Reading from {input_file}...")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File {input_file} not found.")
        return

    if not isinstance(data, list):
        print("Error: Input data is not a list.")
        return

    episodes = {}
    
    # Group by episode
    for entry in data:
        ep = entry.get('episode')
        if not ep:
            print(f"Warning: Entry missing 'episode' field: {entry}")
            continue
            
        if ep not in episodes:
            episodes[ep] = []
        episodes[ep].append(entry)
    
    # Write to separate files
    for ep, entries in episodes.items():
        # Extract episode number from S2E1, S2E2, etc.
        match = re.search(r'E(\d+)', ep)
        if match:
            ep_num = match.group(1)
            filename = f"clean_transcript_s2e{ep_num}.json"
            output_path = os.path.join(output_dir, filename)
            
            print(f"Writing {len(entries)} entries to {output_path}...")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
        else:
            print(f"Warning: Could not parse episode number from '{ep}'. Skipping.")

    print("Done.")

if __name__ == "__main__":
    split_transcripts()
