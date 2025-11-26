import json
import os

def calculate_height(transcript_entries):
    estimated_height = 400 
    chars_per_line = 80
    line_height_px = 25
    entry_padding_px = 20

    for entry in transcript_entries:
        text = entry.get('text', '')
        if text:
            # Calculate number of visual lines this text might take
            num_visual_lines = (len(text) // chars_per_line) + 1
            entry_height = (num_visual_lines * line_height_px) + entry_padding_px
            estimated_height += entry_height

    # Add a little extra buffer just in case
    estimated_height += 100
    return estimated_height

def test_height_calculation():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    for i in range(1, 6):
        filename = f"clean_transcript_s2e{i}.json"
        path = os.path.join(data_dir, filename)
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                height = calculate_height(data)
                print(f"Episode {i}: {len(data)} entries, Calculated Height: {height}px")
        else:
            print(f"Episode {i}: File not found")

if __name__ == "__main__":
    test_height_calculation()
