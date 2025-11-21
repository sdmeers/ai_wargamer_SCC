import json
import os
import time
import logging
import concurrent.futures
from agents import (
    generate_situation_report, 
    generate_advisor_briefing,
    SITUATION_PROMPTS,
    ADVISOR_DEFINITIONS
)

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

OUTPUT_FILE = "intelligence_analysis.json"

def load_transcripts():
    logger.info("Reading transcript files...")
    files_to_load = [
        "the_wargame_s2e1_transcript_cleaned.json",
        "the_wargame_s2e2_transcript_cleaned.json",
        "the_wargame_s2e3_transcript_cleaned.json"
    ]
    combined_text = ""
    for filename in files_to_load:
        path = filename if os.path.exists(filename) else os.path.join("data", filename)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            if 'text' in entry: combined_text += f"{entry.get('speaker', 'Unknown')}: {entry['text']}\n"
                            elif 'content' in entry: combined_text += f"{entry['content']}\n"
                    elif isinstance(data, dict):
                        combined_text += str(data)
                    combined_text += "\n--- END OF EPISODE ---\n"
            except Exception as e:
                logger.error(f"Failed to load {path}: {e}")
    return combined_text

def main():
    # 1. Get Context
    context = load_transcripts()
    if not context:
        logger.error("No transcripts found. Exiting.")
        return

    results = {}
    tasks = []

    # 2. Queue Tasks
    logger.info(f"Queueing tasks for {len(SITUATION_PROMPTS)} Reports and {len(ADVISOR_DEFINITIONS)} Advisors...")
    
    for report_name in SITUATION_PROMPTS:
        tasks.append(("report", report_name))
    for advisor_name in ADVISOR_DEFINITIONS:
        tasks.append(("advisor", advisor_name))

    # 3. Execute in Parallel
    # We can use higher workers here as we run this offline/once, 
    # but keeping it safe at 4 to avoid hitting strict quotas.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        future_to_task = {}
        
        for t_type, t_name in tasks:
            if t_type == "report":
                future = executor.submit(generate_situation_report, t_name, context)
            else:
                future = executor.submit(generate_advisor_briefing, t_name, context)
            future_to_task[future] = (t_type, t_name)

        for future in concurrent.futures.as_completed(future_to_task):
            t_type, t_name = future_to_task[future]
            key = f"report_{t_name}" if t_type == "report" else f"briefing_{t_name}"
            
            try:
                content = future.result()
                results[key] = content
                logger.info(f"✅ Generated: {key}")
            except Exception as e:
                logger.error(f"❌ Failed: {key} - {e}")
                results[key] = f"Generation Failed: {e}"

    # 4. Save to Disk
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"🎉 SUCCESS. Analysis saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()