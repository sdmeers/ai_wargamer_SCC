import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import streamlit as st

# Initialize Vertex AI (Ensure you have authenticated via gcloud auth application-default login locally)
# Replace with your actual Project ID and Location
PROJECT_ID = "your-gcp-project-id" 
LOCATION = "us-central1" 

try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"Vertex AI Init failed (expected if running locally without creds): {e}")

class WargameAgent:
    def __init__(self, name, icon, system_prompt, model_name="gemini-1.5-flash-001"):
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt
        self.model = GenerativeModel(
            model_name,
            system_instruction=[system_prompt]
        )
        self.chat_session = None

    def start_new_session(self):
        """Resets the chat session."""
        self.chat_session = self.model.start_chat(history=[])

    def analyze_situation(self, context_text, task_type="summary"):
        """
        Used for the 'Situation Room' static reports.
        """
        prompt = f"""
        Based strictly on the following transcript context, provide a {self.name} report.
        
        CONTEXT:
        {context_text}
        
        TASK:
        {task_type}
        """
        # Generate simple content
        response = self.model.generate_content(prompt)
        return response.text

    def chat(self, user_input, context_text):
        """
        Used for the 'Advisors' interactive chat.
        Injects context if it's the first turn, otherwise just chats.
        """
        if not self.chat_session:
            self.start_new_session()
            # On first message, we stealthily inject the context
            setup_prompt = f"""
            Here is the current scenario context (Transcripts of the wargame so far). 
            Use this to inform all your future answers.
            
            CONTEXT:
            {context_text}
            
            User Question: {user_input}
            """
            response = self.chat_session.send_message(setup_prompt)
        else:
            response = self.chat_session.send_message(user_input)
            
        return response.text

# --- DEFINING THE SPECIFIC PERSONAS ---

ADVISOR_DEFINITIONS = {
    "Integrator": {
        "icon": "🧩",
        "prompt": """You are 'The Integrator,' a senior strategic analyst advising the UK Prime Minister. 
        Synthesize information across military, diplomatic, economic, and domestic domains. 
        Identify connections, contradictions, and cascading effects. Be concise and strategic."""
    },
    "Red Teamer": {
        "icon": "😈",
        "prompt": """You are 'The Red Cell.' Your job is to think like the Russian leadership. 
        Predict Russian responses and identify UK vulnerabilities from Moscow's perspective. 
        You are NOT pro-Russian, you are pro-UK success, but you achieve this by ruthlessly simulating the adversary."""
    },
    "Military Historian": {
        "icon": "🏛️",
        "prompt": """You are 'The Historian.' Identify relevant historical parallels to the current crisis. 
        Warn about known failure modes. Acknowledge that history doesn't repeat but often rhymes."""
    },
    "Citizen's Voice": {
        "icon": "🗣️",
        "prompt": """You are 'The Citizen's Voice.' You represent the 67 million UK residents. 
        Ask: 'What does this mean for ordinary people?' and 'Are we protecting the population, not just the state?'"""
    }
}

def get_agent(agent_name):
    """Factory function to create an agent instance."""
    if agent_name in ADVISOR_DEFINITIONS:
        data = ADVISOR_DEFINITIONS[agent_name]
        return WargameAgent(agent_name, data['icon'], data['prompt'])
    return None