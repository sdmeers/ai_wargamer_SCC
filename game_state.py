import json
import os

class GameStateManager:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.episodes = {}
        self.load_data()

    def load_data(self):
        """Loads all cleaned transcript JSONs from the data directory."""
        # Assuming file naming convention: the_wargame_s2e{N}_transcript_cleaned.json
        # In a real app, use glob or os.listdir
        episode_files = [
            (1, "the_wargame_s2e1_transcript_cleaned.json"),
            (2, "the_wargame_s2e2_transcript_cleaned.json"),
            (3, "the_wargame_s2e3_transcript_cleaned.json"),
            # Add ep 4 and 5 when ready
        ]

        for ep_num, filename in episode_files:
            path = os.path.join(self.data_dir, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    self.episodes[ep_num] = json.load(f)

    def get_transcript_context(self, up_to_episode: int, include_types=None):
        """
        Concatenates transcript content up to a specific episode.
        
        Args:
            up_to_episode (int): The current episode state (e.g., 2 includes Ep 1 & 2).
            include_types (list): Filters like ['blue', 'red', 'explanation']. 
                                  If None, includes everything except 'advertisement'.
        """
        context_text = []
        
        for i in range(1, up_to_episode + 1):
            if i not in self.episodes:
                continue
                
            data = self.episodes[i]
            context_text.append(f"--- START OF EPISODE {i} ---")
            
            for segment in data.get('segments', []):
                seg_type = segment.get('type')
                
                # Filter logic
                if include_types and seg_type not in include_types:
                    continue
                
                # Format: [Blue Team]: "Content..."
                speaker_label = seg_type.upper() if seg_type else "UNKNOWN"
                content = segment.get('content', '')
                
                # Add to context buffer
                context_text.append(f"[{speaker_label}]: {content}")
                
            context_text.append(f"--- END OF EPISODE {i} ---\n")
            
        return "\n".join(context_text)

# Usage Example:
# manager = GameStateManager()
# context = manager.get_transcript_context(up_to_episode=2, include_types=['blue', 'red', 'explanation'])