import streamlit as st
from datetime import datetime
from pathlib import Path
import sys

# This MUST be at the top to load API keys before any other imports
from dotenv import load_dotenv
load_dotenv()

# Now import the project modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.medical_agent import EnhancedMedicalSchedulingAgent
from langchain_core.messages import AIMessage, HumanMessage

st.set_page_config(page_title="MediCare AI Scheduling", page_icon="🏥", layout="wide")


# ui/streamlit_app.py
# (other imports...)

# This system prompt is the agent's "brain" and core instructions.
SYSTEM_PROMPT = """You are a friendly and highly efficient AI assistant for the MediCare Allergy & Wellness Center.
Your primary goal is to help users book appointments. You MUST be interactive and guide the user step-by-step.

Your Workflow:
1.  Start by asking for the patient's full name and date of birth. Do not proceed until you have it. If they provide invalid info (like a non-existent date), politely correct them and ask again.
2.  Once you have a valid name and DOB, use the `search_for_patient` tool.
3.  Based on the tool's output, inform the user if they are 'new' or 'returning' and state the correct appointment duration (60 min for new, 30 min for returning).
4.  Next, ask for their medical needs. **Based on their symptoms, you must recommend the appropriate specialist.** For example, if they say "bad cough", you should say "For a cough, I recommend our Pulmonologist."
5.  After suggesting a specialist, ask what day they would like an appointment. Use the `find_available_appointments` tool to get a list of slots. **If the user mentions multiple symptoms for different specialists, use the `find_available_appointments` tool for ALL relevant specialists in a single turn.**
6.  **Crucially, if the user changes their mind (e.g., wants a different doctor or day), use the conversation history to understand the new request and use your tools again. Do not say you cannot do it.**
7.  Once the user confirms a specific date and time, use the `book_appointment` tool to finalize it. Remember to pass the correct duration (60 or 30) to the tool.
8.  **After the booking tool returns a "Success" message, and only then, you MUST politely ask for their insurance information to complete the process.**
9.  If a tool returns an error or no results, inform the user and ask a clarifying question to help them try again. Do not make up information or doctors.
"""

# (the rest of the streamlit app code remains the same)




@st.cache_resource
def get_agent():
    return EnhancedMedicalSchedulingAgent()

agent = get_agent()

# Initialize session state for conversation memory
if "messages" not in st.session_state:
    st.session_state.messages = [AIMessage(content="Hello! I am your AI assistant for the MediCare Allergy & Wellness Center. To get started, please tell me your full name and date of birth.")]

st.title("💬 MediCare AI Scheduling Assistant")

for msg in st.session_state.messages:
    if isinstance(msg, AIMessage):
        st.chat_message("assistant", avatar="🤖").write(msg.content)
    elif isinstance(msg, HumanMessage):
        st.chat_message("user", avatar="👤").write(msg.content)

if prompt := st.chat_input("Enter your message here..."):
    st.chat_message("user", avatar="👤").write(prompt)
    st.session_state.messages.append(HumanMessage(content=prompt))

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking..."):
            conversation_with_prompt = [HumanMessage(content=SYSTEM_PROMPT)] + st.session_state.messages
            updated_messages = agent.process_message(conversation_with_prompt)
            st.session_state.messages = updated_messages[1:]
            st.write(st.session_state.messages[-1].content)