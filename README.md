graph TD
    %% Styles
    classDef storage fill:#f9f,stroke:#333,stroke-width:2px;
    classDef process fill:#e1f5fe,stroke:#0277bd,stroke-width:2px;
    classDef external fill:#fff9c4,stroke:#fbc02d,stroke-width:2px;
    classDef ui fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;

    subgraph "Data Pipeline (Offline Processing)"
        Audio[("🎙️ Audio File\n(Podcast MP3)")]:::storage
        Transcriber["⚡ Transcript Processor\n(Speech-to-Text + Speaker ID)"]:::process
        Classifier["🏷️ Text Classifier\n(Blue / Red / Explanation)"]:::process
        JSON[("📄 Cleaned Transcripts\n(JSON Snapshot)")]:::storage
        
        Audio --> Transcriber
        Transcriber --> Classifier
        Classifier --> JSON
    end

    subgraph "AI Wargamer Backend (GCP Cloud Run)"
        direction TB
        ContextEngine["⚙️ Game State Manager\n(Loads & Stitches Episodes)"]:::process
        SystemPrompts["📜 System Prompts\n(Agent Personas)"]:::storage
        
        subgraph "The Agents"
            SitRoom["📊 Situation Room Agents\n(SITREP, ORBAT, SIGACTS)"]:::process
            Advisors["🧠 Advisor Agents\n(Integrator, Red Team, etc.)"]:::process
        end
        
        VertexAI["☁️ Google Vertex AI\n(Gemini 1.5 Flash)"]:::external
    end

    subgraph "Frontend (Streamlit)"
        UI["💻 Web Application\n(Streamlit Interface)"]:::ui
        User((👤 User))
    end

    %% Data Flow Connections
    JSON -->|"Load Context"| ContextEngine
    ContextEngine -->|"Inject Context"| SitRoom
    ContextEngine -->|"Inject Context"| Advisors
    SystemPrompts --> Advisors & SitRoom
    
    SitRoom <-->|"Generate Reports"| VertexAI
    Advisors <-->|"Chat / Reasoning"| VertexAI
    
    SitRoom -->|"Static View"| UI
    Advisors <-->|"Interactive Chat"| UI
    User <-->|"Interact"| UI
