import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import os
import logging
import time

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "mod-scc25lon-710")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
MODEL_ID = "gemini-2.5-pro" 

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    logger.info(f"Vertex AI Initialized. Model: {MODEL_ID}")
except Exception as e:
    logger.error(f"Vertex AI Init Failed: {e}")

# --- PROMPTS ---
SITUATION_PROMPTS = {
    "SITREP": """Role & Persona: You are a Senior Geopolitical Intelligence Analyst. Your tone must be formal, urgent, and professional. Task & Goal: Review the transcript of the simulated COBRA meeting ("The Wargame S2E1: False Flag") and generate an Executive Summary. Constraints: The output must be a maximum of 300 words. Focus only on: 1) The nature of the initial "False Flag" scenario. 2) The immediate, critical decisions made by the UK government team. 3) The main vulnerabilities or lack of preparation identified by the experts. System Prompt "Your task is to review the following transcript and generate an executive summary. The summary must be a maximum of 300 words and focus only on the scenario, the immediate response by the COBRA meeting. You must provide a summary suitable for decision making by senior UK officials in a high stakes scenario. Maintain a formal, urgent, and professional tone suitable for a high-level government briefing.""",
    "SIGACTS": "You are an Intelligence Analyst. List Significant Activities (SIGACTS): Attacks, movements, kinetic events. Time-ordered list.",
    "ORBAT": "You are a Military Analyst. Reconstruct the Order of Battle (ORBAT). List Units, Assets, Key Individuals. Categorize Blue/Red. Status/Location.",
    "Actions": "Summarize decisions and actions taken by the Blue Team (friendly forces). Orders, communications, resources.",
    "Uncertainties": "Identify 'Known Unknowns'. What information gaps exist? What is ambiguous?",
    "Dilemmas": "Identify strategic dilemmas. Where must the team choose between bad options? What are the trade-offs?"
}

ADVISOR_DEFINITIONS = {
    "Integrator": {
        "icon": "🧩",
        "prompt": "You are 'The Integrator,' advising the PM. Synthesize military, diplomatic, economic domains. Identify connections/contradictions."
    },
    "Red Teamer": {
        "icon": "😈",
        "prompt": "You are 'The Red Cell.' Think like Russian leadership. Predict responses, identify UK vulnerabilities. Be ruthless."
    },
    "Military Historian": {
        "icon": "🏛️",
        "prompt": "You are 'The Historian.' Identify historical parallels. Warn about failure modes. History rhymes."
    },
    "Citizen's Voice": {
        "icon": "🗣️",
        "prompt": "You are 'The Citizen's Voice.' Represent 67m UK residents. Ask: What does this mean for ordinary people? Are we protecting them?"
    }
}

# --- GENERATION FUNCTIONS ---

def generate_situation_report(report_type, context_text):
    start_time = time.time()
    # Using thread ID in log can help visualize parallelism if needed, but name is sufficient
    logger.info(f"--> START: Report [{report_type}]")
    
    if not context_text:
        return "Error: No transcript context."
    if report_type not in SITUATION_PROMPTS:
        return f"Error: No prompt for {report_type}"

    try:
        model = GenerativeModel(MODEL_ID, system_instruction=[SITUATION_PROMPTS[report_type]])
        prompt = f"ANALYZE TRANSCRIPT:\n{context_text}\n\nGENERATE REPORT ({report_type})."
        
        response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.info(f"<-- FINISH: Report [{report_type}] in {duration:.2f}s")
        return response.text
    except Exception as e:
        logger.error(f"!!! ERROR: Report [{report_type}] failed: {e}")
        raise e # Re-raise to trigger the retry in web_app

def generate_advisor_briefing(agent_name, context_text):
    start_time = time.time()
    logger.info(f"--> START: Briefing [{agent_name}]")
    
    if agent_name not in ADVISOR_DEFINITIONS:
        return "Error: Unknown Advisor"
    
    try:
        definition = ADVISOR_DEFINITIONS[agent_name]
        model = GenerativeModel(MODEL_ID, system_instruction=[definition['prompt']])
        prompt = f"CONTEXT:\n{context_text}\n\nTASK:\nProvide a high-level initial assessment (max 150 words)."
        
        response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.info(f"<-- FINISH: Briefing [{agent_name}] in {duration:.2f}s")
        return response.text
    except Exception as e:
        logger.error(f"!!! ERROR: Briefing [{agent_name}] failed: {e}")
        raise e

# --- AGENT CLASS ---

class WargameAgent:
    def __init__(self, name, icon, system_prompt):
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt
        self.model = GenerativeModel(MODEL_ID, system_instruction=[system_prompt])
        self.chat_session = None

    def start_new_session(self):
        self.chat_session = self.model.start_chat(history=[])

    def get_response(self, user_input, context_text=""):
        try:
            if self.chat_session is None:
                self.start_new_session()
            full_prompt = f"CONTEXT:\n{context_text}\n\nUSER QUERY:\n{user_input}" if context_text else user_input
            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"

def get_agent(agent_name):
    if agent_name in ADVISOR_DEFINITIONS:
        data = ADVISOR_DEFINITIONS[agent_name]
        return WargameAgent(agent_name, data['icon'], data['prompt'])
    return None