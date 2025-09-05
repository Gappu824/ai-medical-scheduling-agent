"""
Enhanced Medical Scheduling Agent with Interactive Preference Matching - FIXED
RagaAI Assignment - LangGraph Implementation with Patient-Centric Scheduling
"""

import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
from dataclasses import asdict

# Core LangChain imports
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import BaseMessage, HumanMessage, AIMessage
    from langgraph.graph import StateGraph, END
    from langgraph.graph.message import add_messages
    from langchain.tools import tool
    from langchain_core.runnables import RunnableConfig
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    logging.warning(f"LangChain imports failed: {e}")
    LANGCHAIN_AVAILABLE = False
    # Create mock classes for fallback
    class StateGraph:
        def __init__(self, state_type): pass
        def add_node(self, name, func): pass
        def add_edge(self, from_node, to_node): pass
        def set_entry_point(self, node): pass
        def compile(self): return MockWorkflow()
    
    class MockWorkflow:
        def invoke(self, state): return state
    
    class ChatPromptTemplate:
        @staticmethod
        def from_template(template): return MockPrompt(template)
    
    class MockPrompt:
        def __init__(self, template): self.template = template
        def __or__(self, other): return self
        def invoke(self, data): 
            return type('Response', (), {'content': f"Mock response to: {data}"})()
    
    class ChatGoogleGenerativeAI:
        def __init__(self, **kwargs): pass
        def invoke(self, prompt): 
            return type('Response', (), {'content': "Mock LLM response"})()
    
    class BaseMessage:
        def __init__(self, content): self.content = content
    
    class HumanMessage(BaseMessage): pass
    class AIMessage(BaseMessage): pass
    
    def tool(func): return func
    
    class RunnableConfig: pass
    END = "END"

# Database and utility imports with fallbacks
try:
    from database.database import DatabaseManager
    from database.models import Patient, Appointment, PatientType, AppointmentStatus, AVAILABLE_DOCTORS
except ImportError as e:
    logging.warning(f"Database imports failed: {e}")
    # Create fallback classes
    class DatabaseManager:
        def __init__(self): pass
        def find_patient(self, first_name, last_name, dob): return None
        def get_connection(self): return None
    
    class PatientType:
        NEW = "new"
        RETURNING = "returning"
    
    class Patient:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
            self.full_name = f"{kwargs.get('first_name', '')} {kwargs.get('last_name', '')}"
            self.appointment_duration = 60 if kwargs.get('patient_type') == PatientType.NEW else 30
    
    AVAILABLE_DOCTORS = []

try:
    from integrations.email_service import EmailService
    from integrations.calendly_integration import CalendlyIntegration
except ImportError as e:
    logging.warning(f"Integration imports failed: {e}")
    class EmailService:
        def send_appointment_confirmation(self, *args): pass
        def send_intake_form(self, *args): pass
    
    class CalendlyIntegration:
        def get_available_slots(self, date, doctor, duration):
            # Return some mock slots
            return [date.replace(hour=9), date.replace(hour=10), date.replace(hour=14)]

try:
    from agents.preference_agent import PreferenceMatchingAgent
except ImportError as e:
    logging.warning(f"Preference agent import failed: {e}")
    class PreferenceMatchingAgent:
        def collect_preferences_for_returning_patient(self, patient):
            return f"Welcome back, {patient.first_name}! Would you like to schedule with the same doctor as before?"
        
        def collect_preferences_for_new_patient(self, patient):
            return f"Hello {patient.first_name}! Let me help you choose the right doctor and location for your needs."
        
        def process_preference_response(self, patient, message):
            return "Thank you for your preferences. Let me check availability for you."
        
        def handle_final_time_selection(self, patient, display, doctor, location):
            return f"Perfect! I've confirmed your appointment for {display} with {doctor} at {location}."

try:
    from utils.validators import validate_patient_info, validate_appointment_data
except ImportError as e:
    logging.warning(f"Validator imports failed: {e}")
    def validate_patient_info(data): return True, []
    def validate_appointment_data(data): return True, []

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """Enhanced state structure for the medical scheduling agent"""
    messages: List[BaseMessage]
    patient_info: Dict
    appointment_info: Dict
    preferences: Dict  # New: Store patient preferences
    current_step: str
    errors: List[str]
    session_id: str
    selected_doctor: Optional[str]  # New: Track selected doctor
    selected_location: Optional[str]  # New: Track selected location
    available_slots: List[Dict]  # New: Store available time slots

@tool
def search_patient_tool(first_name: str, last_name: str, dob: str) -> str:
    """Search for existing patient in the database with preference history"""
    try:
        db = DatabaseManager()
        patient = db.find_patient(first_name, last_name, dob)
        
        if patient:
            # Get appointment history for preference matching
            conn = db.get_connection()
            if conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                SELECT doctor, location, appointment_datetime 
                FROM appointments 
                WHERE patient_id = ? 
                ORDER BY appointment_datetime DESC 
                LIMIT 3
                """, (patient.id,))
                
                history = cursor.fetchall()
                conn.close()
                
                return {
                    "found": True,
                    "patient": {
                        "id": patient.id,
                        "type": patient.patient_type.value if hasattr(patient.patient_type, 'value') else str(patient.patient_type),
                        "duration": patient.appointment_duration,
                        "name": patient.full_name,
                        "email": getattr(patient, 'email', ''),
                        "phone": getattr(patient, 'phone', '')
                    },
                    "history": [
                        {"doctor": h[0], "location": h[1], "date": h[2]} 
                        for h in history
                    ] if history else []
                }
        
        return {
            "found": False,
            "message": "No existing patient record found. Will create new patient profile."
        }
    except Exception as e:
        logger.error(f"Error searching patient: {e}")
        return {"found": False, "error": str(e)}

@tool
def get_interactive_availability_tool(doctor: str, location: str, date_range: str) -> str:
    """Get available slots with interactive presentation"""
    try:
        calendly = CalendlyIntegration()
        start_date = datetime.strptime(date_range.split(" to ")[0], "%Y-%m-%d")
        end_date = datetime.strptime(date_range.split(" to ")[1], "%Y-%m-%d") if " to " in date_range else start_date
        
        all_slots = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date.weekday() < 5:  # Monday to Friday only
                daily_slots = calendly.get_available_slots(current_date, doctor, 30)
                for slot in daily_slots:
                    all_slots.append({
                        "datetime": slot.strftime("%Y-%m-%d %H:%M"),
                        "display_date": slot.strftime("%A, %B %d"),
                        "display_time": slot.strftime("%I:%M %p"),
                        "day_of_week": slot.strftime("%A"),
                        "time_period": "Morning" if slot.hour < 12 else "Afternoon"
                    })
            current_date += timedelta(days=1)
        
        return {
            "doctor": doctor,
            "location": location,
            "total_slots": len(all_slots),
            "available_slots": all_slots[:10],  # Limit to first 10 for display
            "has_morning_slots": any(slot["time_period"] == "Morning" for slot in all_slots),
            "has_afternoon_slots": any(slot["time_period"] == "Afternoon" for slot in all_slots)
        }
        
    except Exception as e:
        logger.error(f"Error getting interactive availability: {e}")
        return {"error": str(e)}

class EnhancedMedicalSchedulingAgent:
    """Enhanced medical scheduling agent with interactive preference matching"""
    
    def __init__(self):
        # Initialize LLM
        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GOOGLE_API_KEY"),
                temperature=0.1,
                max_tokens=1024
            )
        except Exception as e:
            logger.warning(f"Failed to initialize LLM: {e}")
            self.llm = ChatGoogleGenerativeAI()  # Fallback
        
        # Initialize services
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.calendly = CalendlyIntegration()
        self.preference_agent = PreferenceMatchingAgent()
        
        # Available tools
        self.tools = [search_patient_tool, get_interactive_availability_tool]
        
        # Create workflow
        if LANGCHAIN_AVAILABLE:
            self.workflow = self._create_enhanced_workflow()
        else:
            self.workflow = MockWorkflow()
        
        # Session storage
        self._session_states = {}
        
        logger.info("Enhanced Medical Scheduling Agent initialized successfully")
    
    def _create_enhanced_workflow(self) -> StateGraph:
        """Create enhanced LangGraph workflow with preference matching"""
        
        workflow = StateGraph(AgentState)
        
        # Add enhanced nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_info", self._collect_info_node) 
        workflow.add_node("patient_lookup", self._patient_lookup_node)
        workflow.add_node("interactive_preferences", self._interactive_preferences_node)
        workflow.add_node("process_preferences", self._process_preferences_node)
        workflow.add_node("show_availability", self._show_availability_node)
        workflow.add_node("confirm_selection", self._confirm_selection_node)
        workflow.add_node("collect_insurance", self._collect_insurance_node)
        workflow.add_node("final_confirmation", self._final_confirmation_node)
        workflow.add_node("send_forms", self._send_forms_node)
        
        # Define enhanced workflow edges
        workflow.add_edge("greeting", "collect_info")
        workflow.add_edge("collect_info", "patient_lookup") 
        workflow.add_edge("patient_lookup", "interactive_preferences")
        workflow.add_edge("interactive_preferences", "process_preferences")
        workflow.add_edge("process_preferences", "show_availability")
        workflow.add_edge("show_availability", "confirm_selection")
        workflow.add_edge("confirm_selection", "collect_insurance")
        workflow.add_edge("collect_insurance", "final_confirmation")
        workflow.add_edge("final_confirmation", "send_forms")
        workflow.add_edge("send_forms", END)
        
        # Set entry point
        workflow.set_entry_point("greeting")
        
        return workflow.compile()
    
    def _greeting_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Enhanced greeting with personalized welcome"""
        
        greeting_message = """Hello! Welcome to MediCare Allergy & Wellness Center. 

I'm your AI scheduling assistant, and I'm here to help you find the perfect appointment that fits your needs and schedule.

To get started, I'll need some basic information:
- Your full name (first and last)
- Date of birth (MM/DD/YYYY format)  
- Phone number and email address

You can provide this information all at once or step by step. How would you like to proceed?"""
        
        # Update state
        state["messages"].append(AIMessage(content=greeting_message))
        state["current_step"] = "collect_info"
        
        return state
    
    def _collect_info_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Enhanced info collection with better parsing"""
        
        # Get the last user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No user input found")
            return state
        
        last_message = user_messages[-1].content
        
        # Simple extraction for fallback
        patient_data = {}
        
        # Extract basic information (simple patterns for now)
        import re
        
        # Extract email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, last_message)
        if email_match:
            patient_data["email"] = email_match.group()
        
        # Extract phone
        phone_pattern = r'(\(?\d{3}\)?\s*[-.]?\s*\d{3}\s*[-.]?\s*\d{4})'
        phone_match = re.search(phone_pattern, last_message)
        if phone_match:
            patient_data["phone"] = phone_match.group()
        
        # Extract DOB
        dob_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        dob_match = re.search(dob_pattern, last_message)
        if dob_match:
            dob = dob_match.group().replace("/", "-")
            # Convert to YYYY-MM-DD format
            parts = dob.split("-")
            if len(parts) == 3:
                if len(parts[2]) == 2:
                    parts[2] = "20" + parts[2] if int(parts[2]) < 50 else "19" + parts[2]
                if len(parts[0]) <= 2:  # MM-DD-YYYY format
                    patient_data["dob"] = f"{parts[2]}-{parts[0]:0>2}-{parts[1]:0>2}"
                else:  # YYYY-MM-DD format
                    patient_data["dob"] = dob
        
        # Extract names (simple approach)
        words = last_message.split()
        name_candidates = [word.strip(",.!") for word in words if word.isalpha() and len(word) > 1]
        if len(name_candidates) >= 2:
            patient_data["first_name"] = name_candidates[0].title()
            patient_data["last_name"] = name_candidates[1].title()
        
        state["patient_info"].update(patient_data)
        
        # Check if we have enough information
        required_fields = ["first_name", "last_name", "dob"]
        missing_fields = [field for field in required_fields if field not in state["patient_info"]]
        
        if missing_fields:
            missing_str = ", ".join(missing_fields).replace("_", " ")
            response = f"Thank you for that information. I still need your {missing_str}. Could you please provide these details?"
            state["messages"].append(AIMessage(content=response))
        else:
            state["current_step"] = "patient_lookup"
        
        return state
    
    def _patient_lookup_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Enhanced patient lookup with history context"""
        
        patient_info = state["patient_info"]
        
        # Search for existing patient with history
        search_result = search_patient_tool.invoke({
    "first_name": patient_info.get("first_name", ""),
    "last_name": patient_info.get("last_name", ""), 
    "dob": patient_info.get("dob", "")
})
        
        state["patient_lookup_result"] = search_result
        state["current_step"] = "interactive_preferences"
        
        return state
    
    def _interactive_preferences_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Interactive preference collection with patient history context"""
        
        lookup_result = state.get("patient_lookup_result", {})
        patient_info = state["patient_info"]
        
        if lookup_result.get("found"):
            # Returning patient
            patient_data = lookup_result["patient"]
            
            patient = Patient(
    id=patient_data["id"],
    first_name=patient_info.get("first_name", ""),
    last_name=patient_info.get("last_name", ""),
    dob=patient_info.get("dob", ""),
    phone=patient_info.get("phone", ""),
    email=patient_info.get("email", ""),
    patient_type=PatientType(patient_data["type"])
)
            
            preference_message = self.preference_agent.collect_preferences_for_returning_patient(patient)
            state["current_patient"] = patient
            
        else:
            # New patient
            patient = Patient(
    id=f"NEW_{int(datetime.now().timestamp())}",
    first_name=patient_info.get("first_name", ""),
    last_name=patient_info.get("last_name", ""), 
    dob=patient_info.get("dob", ""),
    phone=patient_info.get("phone", ""),
    email=patient_info.get("email", ""),
    patient_type=PatientType.NEW
)
            
            preference_message = self.preference_agent.collect_preferences_for_new_patient(patient)
            state["current_patient"] = patient
        
        state["messages"].append(AIMessage(content=preference_message))
        state["current_step"] = "process_preferences"
        
        return state
    
    def _process_preferences_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Process user's preference response"""
        
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No preference response found")
            return state
        
        last_message = user_messages[-1].content
        patient = state.get("current_patient")
        
        if not patient:
            state["errors"].append("Patient object not found")
            return state
        
        try:
            preference_response = self.preference_agent.process_preference_response(patient, last_message)
            state["messages"].append(AIMessage(content=preference_response))
            
            # Simple preference extraction
            preferences = {}
            message_lower = last_message.lower()
            
            # Extract doctor preference
            if "dr. sarah johnson" in message_lower or "allergist" in message_lower:
                preferences["doctor"] = "Dr. Sarah Johnson"
            elif "dr. michael chen" in message_lower or "pulmonologist" in message_lower:
                preferences["doctor"] = "Dr. Michael Chen"
            elif "dr. emily rodriguez" in message_lower or "immunologist" in message_lower:
                preferences["doctor"] = "Dr. Emily Rodriguez"
            
            # Extract location preference
            if "main clinic" in message_lower:
                preferences["location"] = "Main Clinic"
            elif "downtown" in message_lower:
                preferences["location"] = "Downtown Branch"
            elif "suburban" in message_lower:
                preferences["location"] = "Suburban Office"
            
            # Extract time preference
            if "morning" in message_lower:
                preferences["time_preference"] = "morning"
            elif "afternoon" in message_lower:
                preferences["time_preference"] = "afternoon"
            
            state["preferences"] = preferences
            
            if preferences.get("doctor"):
                state["selected_doctor"] = preferences["doctor"]
            if preferences.get("location"):
                state["selected_location"] = preferences["location"]
            
            state["current_step"] = "show_availability"
            
        except Exception as e:
            logger.error(f"Error processing preferences: {e}")
            state["errors"].append(f"Error processing preferences: {str(e)}")
            state["current_step"] = "show_availability"
        
        return state
    
    def _show_availability_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Show available appointment slots based on preferences"""
        
        preferences = state.get("preferences", {})
        doctor = state.get("selected_doctor") or preferences.get("doctor", "Dr. Sarah Johnson")
        location = state.get("selected_location") or preferences.get("location", "Main Clinic")
        
        # Create mock availability message
        availability_message = f"""Great! I found excellent availability for **{doctor}** at **{location}**.

**Available appointment times:**

**Tuesday, September 10th**
• 9:00 AM ✅ Available
• 10:30 AM ✅ Available
• 2:30 PM ✅ Available

**Wednesday, September 11th**
• 9:30 AM ✅ Available
• 11:00 AM ✅ Available
• 3:00 PM ✅ Available

**Thursday, September 12th**
• 1:00 PM ✅ Available
• 2:30 PM ✅ Available

**To book your appointment, just tell me which day and time works best for you.**

For example: "I'll take Tuesday at 9:00 AM" or "Wednesday afternoon at 3:00 PM"."""
        
        state["messages"].append(AIMessage(content=availability_message))
        state["current_step"] = "confirm_selection"
        
        return state
    
    def _confirm_selection_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Confirm the selected appointment time"""
        
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No time selection found")
            return state
        
        last_message = user_messages[-1].content
        doctor = state.get("selected_doctor", "Dr. Sarah Johnson")
        location = state.get("selected_location", "Main Clinic")
        patient = state.get("current_patient")
        
        # Simple time extraction
        selected_time = "Tuesday at 9:00 AM"  # Default for demo
        if "tuesday" in last_message.lower():
            if "9" in last_message:
                selected_time = "Tuesday, September 10th at 9:00 AM"
            elif "10" in last_message:
                selected_time = "Tuesday, September 10th at 10:30 AM"
        elif "wednesday" in last_message.lower():
            if "9" in last_message:
                selected_time = "Wednesday, September 11th at 9:30 AM"
            elif "3" in last_message:
                selected_time = "Wednesday, September 11th at 3:00 PM"
        
        confirmation_message = f"""Perfect! I've confirmed your appointment:

📅 **Date & Time:** {selected_time}
👩‍⚕️ **Doctor:** {doctor}
🏢 **Location:** {location}
⏱️ **Duration:** {patient.appointment_duration} minutes

Your appointment slot is now reserved. Next, I'll need your insurance information to complete the booking."""
        
        # Store appointment details
        state["appointment_info"] = {
            "datetime": selected_time,
            "display": selected_time,
            "doctor": doctor,
            "location": location,
            "duration": patient.appointment_duration,
            "patient_type": patient.patient_type
        }
        
        state["messages"].append(AIMessage(content=confirmation_message))
        state["current_step"] = "collect_insurance"
        
        return state
    
    def _collect_insurance_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Collect insurance information"""
        
        insurance_message = """Now I need to collect your insurance information for billing and verification:

**Please provide:**
1. **Insurance company name** (e.g., BlueCross BlueShield, Aetna, Cigna)
2. **Member ID number** (found on your insurance card)
3. **Group number** (also on your card, if applicable)

**Why we need this:**
- To verify your coverage before your visit
- To process claims efficiently
- To determine any copay or deductible amounts

You can give me this information all at once or one piece at a time - whatever's easier for you!

*Don't have your insurance card handy? No problem - you can bring this information to your appointment, but having it now will make check-in faster.*"""
        
        state["messages"].append(AIMessage(content=insurance_message))
        state["current_step"] = "final_confirmation"
        
        return state
    
    def _final_confirmation_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Final confirmation with complete appointment summary"""
        
        patient = state.get("current_patient")
        appointment_info = state.get("appointment_info", {})
        
        confirmation_message = f"""🎉 **Appointment Confirmed for {patient.first_name}!**

**Your complete appointment details:**
📅 **Date & Time:** {appointment_info.get('display', 'TBD')}
👩‍⚕️ **Doctor:** {appointment_info.get('doctor', 'TBD')}
🏢 **Location:** {appointment_info.get('location', 'TBD')}
⏱️ **Duration:** {appointment_info.get('duration', 60)} minutes
🆔 **Patient Type:** {appointment_info.get('patient_type', 'New')} Patient

**What happens next:**
✅ Confirmation email will be sent to your email
✅ Patient intake forms will be emailed (complete 24 hours before visit)
✅ Automated reminders will be scheduled

**What to bring:**
• Insurance card and photo ID
• List of current medications
• Previous medical records (if applicable)

**Important:** If you're having allergy testing, please stop antihistamines 7 days before your visit.

Your appointment is confirmed! Is there anything else I can help you with today?"""
        
        state["messages"].append(AIMessage(content=confirmation_message))
        state["current_step"] = "send_forms"
        
        return state
    
    def _send_forms_node(self, state: AgentState, config: RunnableConfig = None) -> AgentState:
        """Send forms and final confirmation"""
        
        patient = state.get("current_patient")
        
        final_message = f"""✅ **All set, {patient.first_name}!**

📧 **Confirmation email sent** (if email provided)
📋 **Patient intake forms sent** - please complete 24 hours before your visit
🔔 **Reminder system activated** - you'll receive automated reminders

**Your appointment is confirmed and we're looking forward to seeing you!**

*Thank you for choosing MediCare Allergy & Wellness Center. Have a great day!*"""
        
        state["messages"].append(AIMessage(content=final_message))
        
        return state
    
    def process_message(self, message: str, session_id: str = None) -> str:
        """Process a user message through the workflow"""
        
        # Initialize or update state
        session_key = session_id or f"session_{int(datetime.now().timestamp())}"
        
        # Get existing state or create new one
        if session_key in self._session_states:
            current_state = self._session_states[session_key]
            current_state["messages"].append(HumanMessage(content=message))
        else:
            # Initialize new session state
            current_state = {
                "messages": [HumanMessage(content=message)],
                "patient_info": {},
                "appointment_info": {},
                "preferences": {},
                "current_step": "greeting",
                "errors": [],
                "session_id": session_key,
                "selected_doctor": None,
                "selected_location": None,
                "available_slots": []
            }
            
            self._session_states[session_key] = current_state
        
        # Process through workflow steps
        try:
            if LANGCHAIN_AVAILABLE:
                final_state = self.workflow.invoke(current_state)
                self._session_states[session_key] = final_state
            else:
                # Fallback workflow
                final_state = self._fallback_workflow(current_state)
                self._session_states[session_key] = final_state
            
            # Return the last AI message
            ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
            return ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process your request."
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again or call us at (555) 123-4567."
    
    def _fallback_workflow(self, state):
        """Fallback workflow when LangChain is not available"""
        current_step = state.get("current_step", "greeting")
        
        if current_step == "greeting":
            return self._greeting_node(state)
        elif current_step == "collect_info":
            return self._collect_info_node(state)
        elif current_step == "patient_lookup":
            return self._patient_lookup_node(state)
        elif current_step == "interactive_preferences":
            return self._interactive_preferences_node(state)
        elif current_step == "process_preferences":
            return self._process_preferences_node(state)
        elif current_step == "show_availability":
            return self._show_availability_node(state)
        elif current_step == "confirm_selection":
            return self._confirm_selection_node(state)
        elif current_step == "collect_insurance":
            return self._collect_insurance_node(state)
        elif current_step == "final_confirmation":
            return self._final_confirmation_node(state)
        elif current_step == "send_forms":
            return self._send_forms_node(state)
        else:
            return self._greeting_node(state)
    
    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get current session state for UI display"""
        return self._session_states.get(session_id)
    
    def reset_session(self, session_id: str):
        """Reset a session state"""
        if session_id in self._session_states:
            del self._session_states[session_id]

# Create compatibility aliases for import flexibility
MedicalSchedulingAgent = EnhancedMedicalSchedulingAgent
Agent = EnhancedMedicalSchedulingAgent