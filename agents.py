import time
import os
import logging
import json

ADVISOR_DEFINITIONS_PATH = 'prompts/advisor_prompts.json'

# Load advisor definitions from agent_prompts.json
try:
    with open(ADVISOR_DEFINITIONS_PATH, 'r') as f:
        ADVISOR_DEFINITIONS = json.load(f)
except FileNotFoundError:
    logger.error(f"{ADVISOR_DEFINITIONS_PATH} not found. Advisor definitions cannot be loaded.")
    ADVISOR_DEFINITIONS = {}
except json.JSONDecodeError:
    logger.error(f"Error decoding JSON from {ADVISOR_DEFINITIONS_PATH}. Check file format.")
    ADVISOR_DEFINITIONS = {}

# --- VERTEX AI IMPORTS (COMMENTED OUT FOR COST SAVINGS) ---
# To re-enable LLM functionality, uncomment the following lines:
# import vertexai
# from vertexai.generative_models import GenerativeModel, SafetySetting

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Note: These are now primarily informational, but set to your new project ID
PROJECT_ID = "ai-wargamer" 
LOCATION = "us-central1"
MODEL_ID = "gemini-3.0" 

# --- WargameAgent Class ---
class WargameAgent:
    def __init__(self, name, icon, system_prompt):
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt
        
        # --- LLM INITIALIZATION (COMMENTED OUT) ---
        # To re-enable, uncomment the following:
        # try:
        #     vertexai.init(project=PROJECT_ID, location=LOCATION)
        #     self.model = GenerativeModel(
        #         MODEL_ID,
        #         system_instruction=[system_prompt]
        #     )
        #     # The chat session will be initialized on first use or start_new_session
        #     self.chat_session = None
        #     logger.info(f"LLM Mode: Agent {name} initialized for {PROJECT_ID}")
        # except Exception as e:
        #     logger.warning(f"Mock Mode: Vertex AI initialization skipped or failed: {e}. Running in cost-free mock mode.")
        #     self.model = None
        
        # In cost-free mode, the model is explicitly set to None
        self.model = None 


    def start_new_session(self):
        """Resets the chat session (now mocked)."""
        logger.info(f"Mock mode: Starting new session for {self.name}")
        # --- LLM CODE (COMMENTED OUT) ---
        # if self.model:
        #     self.chat_session = self.model.start_chat(history=[])
        pass 

    def analyze_situation(self, context_text, task_type="summary"):
        """
        Used for the 'Situation Room' static reports (now mocked).
        """
        logger.info(f"Mock mode: Generating static report for {self.name} / {task_type}")
        time.sleep(1.0) # Simulate a slight delay

        # --- LLM CODE (COMMENTED OUT) ---
        # if self.model:
        #     # In a real setup, you would construct a detailed prompt and call generate_content
        #     # For now, we fall through to the mock response below
        #     pass

        # A static, non-LLM mock response for the Situation Room
        return f"""
        # [MOCK STATIC REPORT - {self.name}]

        This report is generated in **LLM-FREE MODE** to minimize cloud costs. The original LLM functionality is disabled.

        ### Key Takeaway for {self.name}
        The current game state (Episodes 1-3) indicates a highly kinetic environment, with significant actions taken by both Blue and Red forces. The most crucial factor for decision-makers remains **escalation control** and **alliance cohesion**.

        ### Mock Analysis
        * **Situation:** Kinematics against the UK mainland are confirmed, crossing a major red line.
        * **Focus:** NATO activation and Article 5 discussions are paramount.
        * **Recommendation:** Prioritize political signaling over military action in the next 12 hours.
        """

    def get_response(self, user_input, context_text=""):
        """
        Used for the 'Advisor' chatbot interaction (now mocked).
        """
        logger.info(f"Mock mode: Getting chat response for {self.name}")
        # Simulate LLM delay
        time.sleep(1.5)
        
        # --- LLM CODE (COMMENTED OUT) ---
        # if self.model and self.chat_session:
        #     try:
        #         # Pass the raw transcript context to the LLM for RAG-like capability
        #         full_prompt = f"CONTEXT:\n{context_text}\n\nUSER QUERY:\n{user_input}"
        #         response = self.chat_session.send_message(full_prompt)
        #         return response.text
        #     except Exception as e:
        #         logger.error(f"LLM Call Error: {e}")
        #         return f"**[LLM ERROR]** An error occurred while communicating with the AI. Check project logs. Falling back to mock response."
        
        # A static, non-LLM mock response for the Chatbot
        return f"**[MOCK RESPONSE - {self.name}]**\n\nI am currently operating in **LLM-FREE MODE**.\n\nYour query ('{user_input}') is understood.\n\nAs the **{self.name}**, my advice is currently locked to a placeholder message to ensure zero Vertex AI token usage. To enable the live AI capability, you will need to **uncomment the Vertex AI import and initialization code** in the `agents.py` file."




def get_agent(agent_name):
    """Factory function to create an agent instance."""
    if agent_name in ADVISOR_DEFINITIONS:
        data = ADVISOR_DEFINITIONS[agent_name]
        return WargameAgent(agent_name, data['icon'], data['prompt'])
    return None