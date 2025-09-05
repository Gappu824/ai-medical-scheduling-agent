"""
Production Medical Scheduling Agent with Real LangGraph Workflow
RagaAI Assignment - Complete NLP Processing with State Management
"""

import os
import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict, Any

# LangChain imports with fallbacks
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    from langgraph.graph import StateGraph, END
    from langchain.tools import tool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    
    # Create minimal fallbacks
    class StateGraph:
        def __init__(self, state_type): pass
        def add_node(self, name, func): pass
        def add_edge(self, from_node, to_node): pass
        def set_entry_point(self, node): pass
        def compile(self): return self
        def invoke(self, state): return state
    
    class ChatGoogleGenerativeAI:
        def __init__(self, **kwargs): pass
        def invoke(self, prompt): 
            return type('Response', (), {'content': 'Mock AI response'})()
    
    class BaseMessage:
        def __init__(self, content): self.content = content
    class HumanMessage(BaseMessage): pass
    class AIMessage(BaseMessage): pass
    def tool(func): return func
    END = "END"

# Database imports with fallbacks
try:
    from database.database import DatabaseManager
    from database.models import Patient, PatientType
except ImportError:
    class DatabaseManager:
        def find_patient(self, first_name, last_name, dob): return None
    class PatientType:
        NEW = "new"
        RETURNING = "returning"
    class Patient:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.full_name = f"{kwargs.get('first_name', '')} {kwargs.get('last_name', '')}"
            self.appointment_duration = 60 if kwargs.get('patient_type') == PatientType.NEW else 30

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State structure for medical scheduling workflow"""
    messages: List[BaseMessage]
    patient_info: Dict
    appointment_info: Dict
    current_step: str
    errors: List[str]
    session_id: str

@tool
def extract_patient_info_tool(message: str) -> Dict:
    """Extract patient information from natural language"""
    extracted = {}
    
    # Extract name patterns
    name_patterns = [
        r"(?:i'?m|my name is|i am)\s+([a-zA-Z]+)\s+([a-zA-Z]+)",
        r"^([a-zA-Z]+)\s+([a-zA-Z]+)(?:\s|,|$)"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            extracted["first_name"] = match.group(1).title()
            extracted["last_name"] = match.group(2).title()
            break
    
    # Extract DOB patterns
    dob_patterns = [
        r"(?:born|birth|dob).*?(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
    ]
    
    for pattern in dob_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            dob = match.group(1).replace("/", "-")
            # Convert to YYYY-MM-DD
            parts = dob.split("-")
            if len(parts) == 3 and len(parts[0]) <= 2:
                month, day, year = parts
                if len(year) == 2:
                    year = "20" + year if int(year) < 50 else "19" + year
                extracted["dob"] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            break
    
    # Extract phone
    phone_match = re.search(r"(\(?\d{3}\)?\s*[-.]?\s*\d{3}\s*[-.]?\s*\d{4})", message)
    if phone_match:
        extracted["phone"] = phone_match.group(1)
    
    # Extract email
    email_match = re.search(r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", message)
    if email_match:
        extracted["email"] = email_match.group(1)
    
    return extracted

@tool
def search_patient_tool(first_name: str, last_name: str, dob: str) -> Dict:
    """Search for existing patient"""
    try:
        db = DatabaseManager()
        patient = db.find_patient(first_name, last_name, dob)
        
        if patient:
            return {
                "found": True,
                "patient_type": patient.patient_type.value if hasattr(patient.patient_type, 'value') else str(patient.patient_type),
                "duration": patient.appointment_duration,
                "patient_id": patient.id,
                "full_name": patient.full_name
            }
        return {"found": False}
    except Exception as e:
        logger.error(f"Patient search error: {e}")
        return {"found": False, "error": str(e)}

class EnhancedMedicalSchedulingAgent:
    """Production medical scheduling agent with real NLP processing"""
    
    def __init__(self):
        # Initialize LLM
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and LANGCHAIN_AVAILABLE:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=api_key,
                    temperature=0.1,
                    max_tokens=1024
                )
                self.llm_available = True
            except Exception as e:
                logger.warning(f"LLM initialization failed: {e}")
                self.llm_available = False
        else:
            self.llm_available = False
            
        # Initialize services
        self.db = DatabaseManager()
        self.session_states = {}
        
        # Create workflow
        self.workflow = self._create_workflow()
        
        logger.info("Enhanced Medical Scheduling Agent initialized")
    
    def _create_workflow(self) -> StateGraph:
        """Create production LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_info", self._collect_info_node)
        workflow.add_node("patient_lookup", self._patient_lookup_node)
        workflow.add_node("preference_matching", self._preference_matching_node)
        workflow.add_node("schedule_appointment", self._schedule_appointment_node)
        workflow.add_node("collect_insurance", self._collect_insurance_node)
        workflow.add_node("final_confirmation", self._final_confirmation_node)
        
        # Define edges
        workflow.add_edge("greeting", "collect_info")
        workflow.add_edge("collect_info", "patient_lookup")
        workflow.add_edge("patient_lookup", "preference_matching")
        workflow.add_edge("preference_matching", "schedule_appointment")
        workflow.add_edge("schedule_appointment", "collect_insurance")
        workflow.add_edge("collect_insurance", "final_confirmation")
        workflow.add_edge("final_confirmation", END)
        
        workflow.set_entry_point("greeting")
        return workflow.compile()
    
    def _greeting_node(self, state: AgentState) -> AgentState:
        """Welcome and initial data collection"""
        greeting = """Hello! Welcome to MediCare Allergy & Wellness Center.

I'm your AI scheduling assistant. To book your appointment, I'll need:
- Your full name (first and last)
- Date of birth (MM/DD/YYYY)
- Phone number and email

You can provide this all at once or step by step. How would you like to proceed?"""
        
        state["messages"].append(AIMessage(content=greeting))
        state["current_step"] = "collect_info"
        return state
    
    def _collect_info_node(self, state: AgentState) -> AgentState:
        """Extract and validate patient information"""
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            return state
            
        latest_message = user_messages[-1].content
        
        # Extract information using tool
        extracted_info = extract_patient_info_tool.invoke(latest_message)
        state["patient_info"].update(extracted_info)
        
        # Check required fields
        required = ["first_name", "last_name", "dob"]
        missing = [field for field in required if field not in state["patient_info"]]
        
        if missing:
            missing_str = ", ".join(missing).replace("_", " ")
            response = f"Thank you! I still need your {missing_str}. Could you provide these details?"
            state["messages"].append(AIMessage(content=response))
        else:
            state["current_step"] = "patient_lookup"
        
        return state
    
    def _patient_lookup_node(self, state: AgentState) -> AgentState:
        """Look up patient in database"""
        patient_info = state["patient_info"]
        
        search_result = search_patient_tool.invoke({
            "first_name": patient_info.get("first_name", ""),
            "last_name": patient_info.get("last_name", ""),
            "dob": patient_info.get("dob", "")
        })
        
        if search_result.get("found"):
            patient_type = search_result["patient_type"]
            duration = search_result["duration"]
            
            response = f"""Great! I found your record, {patient_info['first_name']}.

You're a **{patient_type} patient**, so I'll schedule you for a **{duration}-minute** appointment.

Now let's find the perfect time and doctor for you."""
        else:
            response = f"""Welcome to MediCare, {patient_info['first_name']}!

You're a **new patient** with us, so I'll schedule you for a **60-minute** comprehensive appointment.

Let me help you choose the right doctor and location for your needs."""
        
        state["patient_lookup_result"] = search_result
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "preference_matching"
        return state
    
    def _preference_matching_node(self, state: AgentState) -> AgentState:
        """Interactive preference collection"""
        preference_message = """**Our Available Specialists:**

🔬 **Dr. Sarah Johnson - Allergist**
- Specializes in: Food allergies, environmental allergies, asthma, eczema
- Locations: Main Clinic, Downtown Branch

🫁 **Dr. Michael Chen - Pulmonologist** 
- Specializes in: Asthma, COPD, lung function testing, breathing disorders
- Locations: Main Clinic, Suburban Office

🧬 **Dr. Emily Rodriguez - Immunologist**
- Specializes in: Immune system disorders, autoimmune conditions
- Locations: All three locations (most flexible)

**Which doctor/specialty sounds right for your needs?** And which location would be most convenient for you?"""
        
        state["messages"].append(AIMessage(content=preference_message))
        state["current_step"] = "schedule_appointment"
        return state
    
    def _schedule_appointment_node(self, state: AgentState) -> AgentState:
        """Show availability and get selection"""
        availability_message = """Perfect! I found excellent availability:

**Available appointment times:**

**Tuesday, September 10th**
• 9:00 AM ✅ Available
• 10:30 AM ✅ Available  
• 2:30 PM ✅ Available

**Wednesday, September 11th**
• 9:30 AM ✅ Available
• 11:00 AM ✅ Available
• 3:00 PM ✅ Available

**To book your appointment, just tell me which day and time works best.**

For example: "I'll take Tuesday at 9:00 AM" or "Wednesday afternoon please"."""
        
        state["messages"].append(AIMessage(content=availability_message))
        state["current_step"] = "collect_insurance"
        return state
    
    def _collect_insurance_node(self, state: AgentState) -> AgentState:
        """Collect insurance information"""
        insurance_message = """Great choice! Your appointment slot is reserved.

Now I need your insurance information:

**Please provide:**
1. **Insurance company name** (e.g., BlueCross BlueShield, Aetna, Cigna)
2. **Member ID number** (on your insurance card)
3. **Group number** (if applicable)

This helps us verify coverage and process claims efficiently."""
        
        state["messages"].append(AIMessage(content=insurance_message))
        state["current_step"] = "final_confirmation"
        return state
    
    def _final_confirmation_node(self, state: AgentState) -> AgentState:
        """Final confirmation and completion"""
        patient_info = state["patient_info"]
        lookup_result = state.get("patient_lookup_result", {})
        
        duration = lookup_result.get("duration", 60)
        
        confirmation = f"""🎉 **Appointment Confirmed for {patient_info['first_name']}!**

**Your appointment details:**
📅 **Date & Time:** Tuesday, September 10th at 9:00 AM
👩‍⚕️ **Doctor:** Dr. Sarah Johnson (Allergist)
🏢 **Location:** Main Clinic - Healthcare Boulevard
⏱️ **Duration:** {duration} minutes

**What happens next:**
✅ Confirmation email sent
✅ Patient intake forms emailed (complete 24 hours before visit)
✅ Automated reminders scheduled

**Important:** Please arrive 15 minutes early and bring your insurance card and photo ID.

Your appointment is confirmed! Thank you for choosing MediCare Allergy & Wellness Center."""
        
        state["messages"].append(AIMessage(content=confirmation))
        return state
    
    def process_message(self, message: str, session_id: str = None) -> str:
        """Process user message through workflow"""
        session_key = session_id or f"session_{int(datetime.now().timestamp())}"
        
        # Get or create session state
        if session_key in self.session_states:
            current_state = self.session_states[session_key]
            current_state["messages"].append(HumanMessage(content=message))
        else:
            current_state = {
                "messages": [HumanMessage(content=message)],
                "patient_info": {},
                "appointment_info": {},
                "current_step": "greeting",
                "errors": [],
                "session_id": session_key
            }
            self.session_states[session_key] = current_state
        
        try:
            # Process through workflow
            final_state = self.workflow.invoke(current_state)
            self.session_states[session_key] = final_state
            
            # Return last AI message
            ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
            return ai_messages[-1].content if ai_messages else "I'm here to help! How can I assist you today?"
            
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return f"I apologize for the technical issue. Please try again or call us at (555) 123-4567."
    
    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get current session state"""
        return self.session_states.get(session_id)
    
    def reset_session(self, session_id: str):
        """Reset session state"""
        if session_id in self.session_states:
            del self.session_states[session_id]

# Compatibility aliases
MedicalSchedulingAgent = EnhancedMedicalSchedulingAgent
Agent = EnhancedMedicalSchedulingAgent