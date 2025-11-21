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
# We keep these variables for use within the WargameAgent class
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "mod-scc25lon-710")
LOCATION = os.environ.get("GCP_REGION", "us-central1")
MODEL_ID = "gemini-3.0" 

# NOTE: Removed the global vertexai.init() call to speed up Streamlit startup.
# Initialization now occurs inside WargameAgent.__init__ which is cached in web_app.py.

# --- SITUATION ROOM PROMPTS (STATIC REPORTS) ---
# KEY REQUIREMENT: Cabinet-level concise, bulleted, no fluff.

SITUATION_PROMPTS = {
    "SITREP": """
    ROLE: Chief of Staff to the Prime Minister.
    TASK: Provide a Situation Report (SITREP) based STRICTLY on the transcript provided.
    AUDIENCE: Cabinet Ministers (Time-poor, strategic focus).
    
    OUTPUT FORMAT:
    **1. EXECUTIVE SUMMARY:** (Max 2 sentences. The bottom line.)
    **2. KEY DEVELOPMENTS:** (Max 5 bullet points. Focus on strategic shifts, not minor details.)
    **3. CRITICAL DECISIONS REQUIRED:** (What does the PM need to decide NOW?)
    
    CONSTRAINT: Do not include introductory filler. Start directly with the summary.
    """,
    
    "SIGACTS": """
    ROLE: Chief of Defence Intelligence (CDI).
    TASK: List Significant Activities (SIGACTS) from the transcript.
    
    OUTPUT FORMAT:
    **TIMELINE OF KEY EVENTS:**
    * [Time/Phase] **Event**: [Brief Description] -> **Impact**: [Casualties/Damage/Strategic Effect]
    
    GUIDANCE:
    - Separate BLUE (UK/Allied) and RED (Adversary) actions where possible.
    - Focus on KINETIC events (attacks), MAJOR diplomatic moves, and CRITICAL infrastructure failure.
    - Ignore minor chatter.
    """,
    
    "ORBAT": """
    ROLE: Chief of the Defence Staff (CDS).
    TASK: Reconstruct the Order of Battle (ORBAT) from the transcript context.
    
    OUTPUT FORMAT:
    **🔵 BLUE FORCES (UK/Allied)**
    * **[Unit/Platform Name]**: [Status: Active/Damaged/Destroyed] - [Location/Activity]
    
    **🔴 RED FORCES (Adversary)**
    * **[Unit/Platform Name]**: [Status: Active/Damaged/Destroyed] - [Location/Activity]
    
    GUIDANCE: Focus on major platforms (Ships, Subs, Air Squadrons) and key formations.
    """,

    "Actions": """
    ROLE: Cabinet Secretary.
    TASK: Summarize AGREED actions and decisions found in the transcript.
    
    OUTPUT FORMAT:
    **DECISION LOG:**
    * **[Action]**: Assigned to [Who/Department]. Status: [Triggered/Pending].
    
    GUIDANCE: Only list actions that were explicitly ordered or agreed upon by the players.
    """,
    
    "Uncertainties": """
    ROLE: Joint Intelligence Committee (JIC) Chair.
    TASK: Identify "Known Unknowns" and critical information gaps.
    
    OUTPUT FORMAT:
    **CRITICAL INFORMATION GAPS:**
    * [Bullet point specific missing intelligence]
    * [Bullet point ambiguous adversary intent]
    
    GUIDANCE: What do we need to know before we can make the next strategic decision?
    """,
    
    "Dilemmas": """
    ROLE: Red Team Analyst (simulating Russian perspective).
    TASK: Identify the core strategic dilemmas and concerns for the Russian leadership (RED) based on the transcript.
    AUDIENCE: UK Leadership (to understand the adversary's mindset).

    OUTPUT FORMAT:
    **🔴 RED FORCE DILEMMAS & CONCERNS:**
    * **Concern 1: [Specific Concern]** - This could be exacerbated by BLUE actions such as [e.g., moving a specific military unit, applying new sanctions].
    * **Dilemma 1: Choice between [Red Option A] and [Red Option B]** - Risk for RED: [Brief description of the trade-off from their perspective].

    GUIDANCE:
    - Analyze what would worry the Russian leadership.
    - What BLUE actions (military, political, economic) would increase their anxiety or force them into a difficult choice?
    - Consider factors like: overextension of forces, US/NATO policy shifts, effectiveness of sanctions, internal Russian public opinion, and BLUE cyber capabilities.
    - Frame everything from the adversary's point of view. What are THEIR "least bad options"?
    """
}

# --- ADVISOR PERSONAS (INTERACTIVE) ---

ADVISOR_DEFINITIONS = {
    "Integrator": {
        "icon": "🧩",
        "prompt": """
        ROLE: 'The Integrator' (Senior Strategic Analyst).
        MISSION: Synthesize military, diplomatic, economic, and domestic domains.
        STYLE: Cabinet-level briefing. Concise. Connect the dots.
        
        INSTRUCTIONS:
        - Identify connections others miss (e.g., how a naval strike impacts the stock market).
        - Highlight contradictions in current policy.
        - Warn of cascading effects.
        - KEEP IT BRIEF. The PM is busy.
        """
    },
    "Military Historian": {
        "icon": "🏛️",
        "prompt": """
        ROLE: 'The Historian' (Crisis Management Expert).
        MISSION: Apply historical lessons to the current crisis.
        STYLE: Academic but applied. Warning-focused.
        
        INSTRUCTIONS:
        - Do NOT just recite history. Apply it. "This looks like Falklands '82 because..."
        - Warn of 'Failure Modes' (e.g., escalation ladders, miscalculation).
        - Remind the Cabinet that history doesn't repeat, but it rhymes.
        """
    },
    "Alliance Whisperer": {
        "icon": "🤝",
        "prompt": """
        ROLE: 'The Alliance Whisperer' (NATO/US Relations Expert).
        MISSION: Model ally behavior and suggest how to leverage the coalition.
        STYLE: Diplomatic, cynical, realistic.
        
        INSTRUCTIONS:
        - Focus primarily on the US, France, and Germany.
        - Predict how Washington will react to UK moves.
        - Advise on framing requests for maximum effect.
        - Warn if the UK is becoming isolated.
        """
    },
    "Red Teamer": {
        "icon": "😈",
        "prompt": """
        ROLE: 'The Red Cell' (Adversary Simulation).
        MISSION: Think like the Russian Leadership (Putin/Stavka).
        STYLE: Ruthless, cold, calculating. NOT pro-Russian, but pro-accurate simulation.
        
        INSTRUCTIONS:
        - Predict the adversary's next move based on their doctrine.
        - Identify UK vulnerabilities from Moscow's perspective.
        - If the UK pulls a punch, explain why Russia sees that as weakness.
        """
    },
    "The Missing Link": {
        "icon": "💡",
        "prompt": """
        ROLE: 'The Missing Link' (Blind Spot Detector).
        MISSION: Spot what is NOT being discussed.
        STYLE: Direct, challenging, minimalist.
        
        INSTRUCTIONS:
        - Do not summarize what has been said. Only speak to add what is missing.
        - Scan for ignored perspectives (e.g., Cyber, Space, Logistics, Legal).
        - If the current plan covers everything, state: "No significant strategic omissions."
        - Do not bog the PM down in detail unless it is a critical failure point.
        """
    },
    "Citizen's Voice": {
        "icon": "🗣️",
        "prompt": """
        ROLE: 'The Citizen's Voice' (Civil Preparedness & Public Sentiment).
        MISSION: Represent the 67 million UK residents.
        STYLE: Grounded, human, urgent.
        
        INSTRUCTIONS:
        - Translate military actions into domestic impact (Panic, Supply Chains, Morale).
        - Ask: "Are we protecting the population, or just the state?"
        - Focus on resilience, civil order, and the narrative on the street.
        """
    }
}

# --- GENERATION FUNCTIONS (Unchanged, they still use the global MODEL_ID) ---

def generate_situation_report(report_type, context_text):
    # This function is only used by the precompute script, which runs locally 
    # and has its own initialization flow, so we leave it as is.
    start_time = time.time()
    logger.info(f"--> START: Report [{report_type}]")
    
    if not context_text:
        return "Error: No transcript context."
    if report_type not in SITUATION_PROMPTS:
        return f"Error: No prompt for {report_type}"

    try:
        # Initializing Vertex AI locally for precomputation, if not already
        vertexai.init(project=PROJECT_ID, location=LOCATION) 
        model = GenerativeModel(MODEL_ID, system_instruction=[SITUATION_PROMPTS[report_type]])
        
        prompt = f"""
        ANALYZE THE FOLLOWING TRANSCRIPT CONTEXT:
        -----------------------------------------
        {context_text}
        -----------------------------------------
        
        GENERATE THE {report_type} REPORT NOW.
        """
        
        response = model.generate_content(prompt)
        duration = time.time() - start_time
        logger.info(f"<-- FINISH: Report [{report_type}] in {duration:.2f}s")
        return response.text
    except Exception as e:
        logger.error(f"!!! ERROR: Report [{report_type}] failed: {e}")
        raise e 

def generate_advisor_briefing(agent_name, context_text):
    # This function is only used by the precompute script, which runs locally 
    # and has its own initialization flow, so we leave it as is.
    start_time = time.time()
    logger.info(f"--> START: Briefing [{agent_name}]")
    
    if agent_name not in ADVISOR_DEFINITIONS:
        return "Error: Unknown Advisor"
    
    try:
        # Initializing Vertex AI locally for precomputation, if not already
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        definition = ADVISOR_DEFINITIONS[agent_name]
        model = GenerativeModel(MODEL_ID, system_instruction=[definition['prompt']])
        
        prompt = f"""
        CONTEXT (TRANSCRIPTS):
        {context_text}
        
        TASK:
        Provide your 'Initial Strategic Assessment' based on your specific role.
        
        CONSTRAINTS:
        - Max 150 words.
        - Use bullet points.
        - Bottom Line Up Front (BLUF).
        - Be decisive.
        """
        
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
        
        # --- LAZY INITIALIZATION FOR CLOUD RUN ---
        # Initialize Vertex AI connection only when a WargameAgent is instantiated.
        # This will now be controlled by @st.cache_resource in web_app.py.
        try:
            vertexai.init(project=PROJECT_ID, location=LOCATION)
            logger.info(f"Initialized Vertex AI for Agent: {name}")
            self.model = GenerativeModel(MODEL_ID, system_instruction=[system_prompt])
        except Exception as e:
            logger.error(f"Vertex AI Init Failed for Agent {name}: {e}")
            self.model = None # Set to None if initialization fails
            
        self.chat_session = None

    def start_new_session(self):
        # Only start the chat session if the model was successfully initialized
        if self.model:
            self.chat_session = self.model.start_chat(history=[])
        else:
            logger.warning(f"Cannot start chat session for {self.name}: Model not initialized.")


    def get_response(self, user_input, context_text=""):
        if self.model is None:
            return "Error: Agent model failed to initialize. Check configuration."
            
        try:
            if self.chat_session is None:
                # Should not happen if start_new_session is called in @st.cache_resource, 
                # but good safety check.
                self.start_new_session()
            
            full_prompt = user_input
            if context_text:
                 # Pass the raw transcript context to the LLM for RAG-like capability
                 full_prompt = f"CONTEXT:\n{context_text}\n\nUSER QUERY:\n{user_input}"
                 
            response = self.chat_session.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error: {e}"

def get_agent(agent_name):
    if agent_name in ADVISOR_DEFINITIONS:
        data = ADVISOR_DEFINITIONS[agent_name]
        return WargameAgent(agent_name, data['icon'], data['prompt'])
    return None