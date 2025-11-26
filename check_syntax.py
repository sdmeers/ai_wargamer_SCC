import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    import web_app
    print("Successfully imported web_app. No syntax errors.")
except SyntaxError as e:
    print(f"SyntaxError in web_app.py: {e}")
    sys.exit(1)
except ImportError as e:
    # ImportError might happen due to missing dependencies in this environment (like streamlit), 
    # but we are mainly checking for SyntaxError.
    print(f"ImportError (expected if deps missing): {e}")
except Exception as e:
    print(f"An error occurred: {e}")
