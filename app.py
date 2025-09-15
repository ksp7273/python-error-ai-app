import streamlit as st
import requests
import re
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# System prompt for CodeLlama
SYSTEM_PROMPT = """
You are a Python error troubleshooting expert. Based only on the user's descriptive text about a Python error or problem (no code or logs provided), respond with:
1. Why this problem likely occurs (common causes in Python).
2. Step-by-step instructions to solve it.
Keep the response concise, structured, and focused on Python language specifics. Do not ask for more information.

Error description: {description}

Why This Problem Occurs:
"""

# Function to validate input: Ensure it's only descriptive text, no code-like content
def is_valid_description(description):
    code_patterns = [
        r'^\s*import\s',  # import statements
        r'^\s*def\s',     # function defs
        r'^\s*class\s',   # class defs
        r'```',           # code blocks
        r'^\s*print\(',   # print statements
    ]
    for pattern in code_patterns:
        if re.search(pattern, description, re.MULTILINE):
            return False
    return True

# Function to call Hugging Face Inference API with CodeLlama
def get_ai_response(description, api_key):
    print(f"Calling Hugging Face API with description: {description[:50]}...")  # Debug log
    url = "https://api-inference.huggingface.co/models/codellama/CodeLlama-7b-Python-hf"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    full_prompt = SYSTEM_PROMPT.format(description=description)
    data = {
        "inputs": full_prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.7,
            "return_full_text": False
        }
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"API response status: {response.status_code}")  # Debug log
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
                return result[0]["generated_text"].strip()
            else:
                return "Unexpected API response format."
        else:
            error_text = response.text
            try:
                error_json = json.loads(error_text)
                if "error" in error_json:
                    return f"API error: {error_json['error']}"
            except:
                pass
            return f"API error: {response.status_code} - {error_text}"
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {str(e)}")  # Debug log
        return f"API request failed: {str(e)}"

# Streamlit app
st.set_page_config(page_title="Python Error Troubleshooter", layout="wide")
st.title("Python Error Troubleshooting AI")

st.write("Enter a description of your Python error or problem (e.g., 'I get an error saying division by zero'). No code, logs, or other details allowed.")

description = st.text_area("Description:", height=150)

if st.button("Get Solution"):
    if not description.strip():
        st.error("Please provide a description.")
    elif not is_valid_description(description):
        st.error("Input must be a plain description only. No code snippets or technical logs allowed. Rephrase and try again.")
    else:
        api_key = os.getenv("HF_API_KEY")
        print(f"API key loaded: {bool(api_key)}")  # Debug log (True if key exists)
        if not api_key:
            st.error("Hugging Face API key not set. Add it to .env as HF_API_KEY=your_token.")
        else:
            with st.spinner("Analyzing with CodeLlama..."):
                response = get_ai_response(description, api_key)
                st.success("Analysis Complete!")
                # Parse response
                if "Steps to solve:" in response or "Steps to Solve:" in response:
                    explanation, steps = response.split("Steps to solve:", 1)
                    steps = steps.strip()
                else:
                    explanation = response.split("Steps")[0].strip()
                    steps = response[len(explanation):].strip() if "Steps" in response else response
                    if not steps.startswith("Steps"):
                        steps = response  # Fallback
                st.markdown("### Why This Problem Occurs")
                st.write(explanation)
                st.markdown("### Steps to Solve")
                st.write(steps)

# Run Streamlit with explicit host/port for Codespaces
if __name__ == "__main__":
    print("Starting Streamlit server on 0.0.0.0:8501...")  # Debug log
    import streamlit.web.cli as stcli
    import sys
    sys.argv = ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
    stcli.main()