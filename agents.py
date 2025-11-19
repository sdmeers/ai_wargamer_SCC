import vertexai
from vertexai.generative_models import GenerativeModel, SafetySetting
import os
import streamlit as st

# --- CONFIGURATION ---
# Use environment variables for Docker/Cloud Run compatibility, fallback to defaults
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "mod-scc25lon-710")
LOCATION = os.environ.get("GCP_REGION", "europe-west2")
# UPDATED: Using Gemini 1.5 Pro (002) as the robust "Pro" model.
# If you have a specific ID for "2.5", replace the string below.
MODEL_ID = "gemini-2.5-pro" 

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    # This might fail locally if not authenticated, but will work in GCP/Docker if SA is attached
    print(f"Vertex AI Init Warning: {e}")

# --- SITUATION ROOM PROMPTS ---
# These prompts correspond to the 'llm_static' pages in your web_app navigation.
SITUATION_PROMPTS = {
    "SITREP": """
    You are the Chief of Staff. 
    Based strictly on the provided transcript context, write a Situation Report (SITREP).
    
    Format:
    **1. Situation Overview** (High level summary)
    **2. Key Events** (Bulleted list of what just happened)
    **3. Immediate Priorities** (What needs attention now)
    
    Style: Professional, military standard, concise.
    """,
    
    "SIGACTS": """
    You are an Intelligence Analyst.
    Extract all Significant Activities (SIGACTS) from the transcript.
    Focus on: Attacks, troop movements, kinetic events, and major diplomatic escalations.
    Provide them as a time-ordered list if time is discernible, otherwise by importance.
    """,
    
    "ORBAT": """
    You are a Military Analyst.
    Reconstruct the Order of Battle (ORBAT) based on the transcript.
    List all specific Units, Assets, and Key Individuals mentioned.
    Categorize them by Faction (Blue/Friendly vs Red/Hostile).
    State their current status/location if known.
    """,

    "Actions": """
    Summarize the specific decisions and actions taken by the Blue Team (friendly forces) in this transcript.
    Highlight orders given, communications sent, and resources deployed.
    """,
    
    "Uncertainties": """
    Identify the "Known Unknowns". 
    List the critical information gaps that the leadership is currently struggling with.
    What are they asking questions about? What is ambiguous?
    """,
    
    "Dilemmas": """
    Identify the strategic dilemmas. 
    Where is the team forced to choose between two bad options? 
    What are the moral or strategic trade-offs discussed?
    """
}

# --- AGENT DEFINITIONS ---
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

def generate_situation_report(report_type, context_text):
    """
    Generates a one-off static report for the Situation Room.
    """
    if not context_text:
        return "Error: No transcript context available for analysis."
        
    if report_type not in SITUATION_PROMPTS:
        return f"System Error: No prompt defined for report type '{report_type}'."

    system_instruction = SITUATION_PROMPTS[report_type]
    
    try:
        # Create the model instance
        model = GenerativeModel(
            MODEL_ID,
            system_instruction=[system_instruction]
        )
        
        # Construct the user prompt
        prompt = f"""
        ANALYZE THE FOLLOWING TRANSCRIPT DATA:
        --------------------------------------
        {context_text}
        --------------------------------------
        
        GENERATE THE REQUESTED REPORT ({report_type}).
        """
        
        # Generate
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error generating {report_type}: {str(e)}"

class WargameAgent:
    def __init__(self, name, icon, system_prompt):
        self.name = name
        self.icon = icon
        self.system_prompt = system_prompt
        # Initialize with the Pro model
        self.model = GenerativeModel(
            MODEL_ID,
            system_instruction=[system_prompt]
        )
        self.chat_session = None

    def start_new_session(self):
        """Resets the chat session."""
        self.chat_session = self.model.start_chat(history=[])

    def get_response(self, user_input, context_text=""):
        """
        Sends a message to the agent and gets a response.
        Includes context if provided (usually strictly for the first message or system context).
        """
        try:
            if self.chat_session is None:
                self.start_new_session()
            
            # If there's specific context to inject (RAG-lite), prepend it
            full_prompt = user_input
            if context_text:
                full_prompt = f"CONTEXT:\n{context_text}\n\nUSER QUERY:\n{user_input}"

            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error getting response from {self.name}: {e}"

def get_agent(agent_name):
    """Factory function to create an agent instance."""
    if agent_name in ADVISOR_DEFINITIONS:
        data = ADVISOR_DEFINITIONS[agent_name]
        return WargameAgent(agent_name, data['icon'], data['prompt'])
    return None