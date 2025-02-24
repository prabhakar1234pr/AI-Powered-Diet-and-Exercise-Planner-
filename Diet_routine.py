import streamlit as st
import requests
import json
import re

# =============================================================================
# COMMON CONFIGURATION
# =============================================================================
BASE_API_URL = "https://api.langflow.astra.datastax.com"
LANGFLOW_ID = "664e2890-0079-4091-88d4-68d3da05aa38"

# =============================================================================
# API 1 CONFIGURATION (Diet Macro Recommendation)
# =============================================================================
FLOW_ID_API1 = "0287e3b8-2cca-4c53-b48e-80a75ca171cb"
APPLICATION_TOKEN_API1 = st.secrets["APPLICATION_TOKEN_1"]  # Replace with your actual token
ENDPOINT_API1 = "Macro"
TWEAKS_API1 = {
    "TextInput-hjvnW": {"input_value": "goals"},
    "TextInput-0QPCj": {"input_value": "profile"},
    "Prompt-h7iA7": {},
    "TextOutput-4vQAa": {},
    "PerplexityModel-Jtf2S": {}
}

def run_flow_api1(message: str) -> dict:
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{ENDPOINT_API1}"
    payload = {
        "input_value": message,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS_API1
    }
    headers = {
        "Authorization": "Bearer " + APPLICATION_TOKEN_API1,
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, json=payload, headers=headers)
    try:
        return response.json()
    except Exception as e:
        return {
            "error": "Failed to decode JSON in API 1",
            "response_text": response.text,
            "details": str(e)
        }

# =============================================================================
# API 2 CONFIGURATION (Personalized Workout & Diet Plan)
# =============================================================================
FLOW_ID_API2 = "3e774dd8-0d0f-4006-93ca-fd14e2bcf0cb"
APPLICATION_TOKEN_API2 = st.secrets["APPLICATION_TOKEN_2"]  # Replace with your actual token
ENDPOINT_API2 = ""
TWEAKS_API2 = {
    "ChatInput-Biji5": {},
    "ParseData-E7X2H": {},
    "Prompt-hp7nd": {},
    "OpenAIModel-6rbG5": {},
    "AstraDB-d5nX2": {},
    "ConditionalRouter-7wvO2": {},
    "ToolCallingAgent-67WWg": {},
    "CalculatorTool-tGUPc": {},
    "OpenAIModel-Vp8ph": {},
    "ChatOutput-a0cfr": {},
    "Prompt-sldfq": {},
    "TextInput-g5A4Q": {},
    "Prompt-xGw0X": {},
    "OpenAIModel-UTsqR": {},
    "ChatOutput-d7HLR": {}
}

def run_flow_api2(message: str) -> dict:
    endpoint = ENDPOINT_API2 if ENDPOINT_API2 else FLOW_ID_API2
    api_url = f"{BASE_API_URL}/lf/{LANGFLOW_ID}/api/v1/run/{endpoint}"
    payload = {
        "input_value": message,
        "output_type": "chat",
        "input_type": "chat",
        "tweaks": TWEAKS_API2
    }
    headers = {
        "Authorization": "Bearer " + APPLICATION_TOKEN_API2,
        "Content-Type": "application/json"
    }
    response = requests.post(api_url, json=payload, headers=headers)
    try:
        return response.json()
    except Exception as e:
        return {
            "error": "Failed to decode JSON in API 2",
            "response_text": response.text,
            "details": str(e)
        }

# =============================================================================
# HELPER FUNCTION TO EXTRACT THE FINAL ANSWER
# =============================================================================
def extract_answer(response: dict) -> dict:
    """
    Attempts to extract the final answer from the API response.
    It follows these steps:
      1. Verify the top-level 'outputs' key exists.
      2. Attempt to retrieve the answer from:
             response["outputs"][0]["outputs"][0]["results"]
         checking for either a "text" or "message" key.
      3. If not found, fallback to the first message in:
             response["outputs"][0]["messages"][0]["message"]
      4. If nothing is found, return an error with the full response for debugging.
    """
    raw_text = None
    if "outputs" in response and len(response["outputs"]) > 0:
        output0 = response["outputs"][0]
        # Try to extract from the "outputs" array if it exists
        if "outputs" in output0 and len(output0["outputs"]) > 0:
            inner = output0["outputs"][0]
            results = inner.get("results", {})
            # Try "text" first
            if (isinstance(results.get("text"), dict) and 
                "data" in results["text"] and 
                "text" in results["text"]["data"]):
                raw_text = results["text"]["data"]["text"]
            # Otherwise try "message"
            elif (isinstance(results.get("message"), dict) and 
                  "data" in results["message"] and 
                  "text" in results["message"]["data"]):
                raw_text = results["message"]["data"]["text"]
        # Fallback: if raw_text not found, try using the first message
        if not raw_text and "messages" in output0 and len(output0["messages"]) > 0:
            raw_text = output0["messages"][0].get("message", None)
    else:
        return {"error": "Failed to extract answer", "details": "Key 'outputs' not found in response", "response": response}

    if not raw_text:
        return {"error": "Failed to extract answer", "details": "No answer text found", "response": response}

    # Clean up markdown formatting (remove triple backticks)
    clean_text = re.sub(r"```json|```", "", raw_text).strip()
    try:
        answer = json.loads(clean_text)
    except Exception:
        answer = clean_text
    return answer

# =============================================================================
# STREAMLIT APP
# =============================================================================
def main():
    st.title("Workout & Diet Design App")
    st.write("Provide your details to receive personalized recommendations.")

    # Create two tabs for the two functionalities.
    tab1, tab2 = st.tabs(["Diet Macro Recommendation", "Personalized Plan"])

    # --- Tab 1: Diet Macro Recommendation ---
    with tab1:
        profile = st.text_area("Profile (e.g., name, age, weight, height):", height=100)
        goals = st.text_area("Diet Goals (e.g., muscle gain, weight loss):", height=100)
        notes = st.text_area("Additional Notes (optional):", height=100)
        if st.button("Get Diet Recommendation", key="diet_button"):
            if not profile.strip() or not goals.strip():
                st.error("Please enter both profile details and diet goals.")
            else:
                prompt = (
                    "Based on the following user profile and diet goals, please calculate the recommended daily intake "
                    "of portions (in grams), calories, fat (in grams), and carbohydrates (in grams) to achieve their goals.\n\n"
                    f"Profile: {profile}\nGoals: {goals}\nAdditional Notes: {notes}"
                )
                with st.spinner("Processing..."):
                    response_api1 = run_flow_api1(prompt)
                    answer_api1 = extract_answer(response_api1)
                st.write(answer_api1)

    # --- Tab 2: Personalized Plan ---
    with tab2:
        detailed_profile = st.text_area("Detailed Profile (include nutritional habits, biometric stats, etc.):", height=150)
        if st.button("Get Personalized Plan", key="personalized_button"):
            if not detailed_profile.strip():
                st.error("Please enter your detailed profile information.")
            else:
                prompt = (
                    "As a highly experienced personal trainer and dietician with expertise in health, nutrition, and fitness, "
                    "use the following user profile context to provide a personalized and accurate workout and diet plan:\n\n"
                    f"{detailed_profile}"
                )
                with st.spinner("Processing..."):
                    response_api2 = run_flow_api2(prompt)
                    answer_api2 = extract_answer(response_api2)
                st.write(answer_api2)

if __name__ == "__main__":
    main()

