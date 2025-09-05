"""
Final, Intelligent, and RELIABLE Medical Agent
RagaAI Assignment - Fixes patient recognition and adds conversational intelligence.
"""

from datetime import datetime
from typing import TypedDict, Annotated
import logging
import json

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from database.database import DatabaseManager
from integrations.calendly_integration import CalendlyIntegration
from database.models import Appointment, AppointmentStatus, Patient, PatientType
from integrations.email_service import EmailService
from integrations.reminder_system import get_reminder_system

logger = logging.getLogger(__name__)

db = DatabaseManager()

# --- Tools ---

# NOTE: This tool for returning patients is the version that worked and has NOT been changed.
@tool
def identify_patient(full_name: str, dob: str = None) -> str:
    """
    Identifies a patient from the database using their full name and an optional date of birth (DOB).
    This tool should be the first step in any conversation.
    """
    name_parts = full_name.strip().split()
    if len(name_parts) < 2:
        return json.dumps({"status": "error", "message": "Please provide both a first and last name."})
    
    first_name, last_name = name_parts[0], " ".join(name_parts[1:])
    
    normalized_dob = None
    if dob:
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
            try:
                normalized_dob = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
                break
            except (ValueError, TypeError):
                continue

    matches = db.find_patient(first_name, last_name, normalized_dob)
    
    if not matches:
        return json.dumps({"status": "not_found"})
    
    if len(matches) == 1:
        patient = matches[0]
        history = db.get_patient_appointment_history(patient.id)
        suggestion = ""
        if history:
            last_visit = history[0]
            suggestion = f"I see your last visit was with {last_visit['doctor']}. Would you like to schedule with them again?"
        
        return json.dumps({
            "status": "verified", "patient_id": patient.id,
            "full_name": patient.full_name, "suggestion": suggestion
        })
        
    if len(matches) > 1:
        dob_options = [p.dob for p in matches]
        return json.dumps({
            "status": "clarification_needed",
            "message": f"I found a few people with that name. To confirm, is your date of birth one of these: {', '.join(dob_options)}?"
        })

@tool
def register_new_patient(first_name: str, last_name: str, dob: str, phone: str, email: str) -> str:
    """Registers a new patient in the database. MUST be called for a new patient before booking."""
    normalized_dob = None
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            normalized_dob = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
            break
        except (ValueError, TypeError): continue
    if not normalized_dob: return "Failed to register: DOB format is invalid. Please use YYYY-MM-DD."

    patient_data = { "first_name": first_name, "last_name": last_name, "dob": normalized_dob, "phone": phone, "email": email }
    new_patient = db.create_patient(patient_data)
    if new_patient:
        return f"Successfully registered new patient {new_patient.full_name} with ID {new_patient.id}. You may now book their appointment."
    return "Failed to register new patient."

@tool
def find_available_appointments(symptom: str = None, doctor_specialty: str = None) -> str:
    """
    Intelligently finds available appointments.
    If a symptom is provided (e.g., 'cough', 'allergy'), it recommends the best specialist.
    If the recommended specialist is unavailable, it automatically checks for a General Practitioner as an alternative.
    """
    calendar = CalendlyIntegration()
    
    symptom_map = {
        "cough": "Pulmonologist", "breathing": "Pulmonologist",
        "allergy": "Allergist", "rash": "Allergist", "immune": "Immunologist"
    }
    
    doctor_map = {
        "Pulmonologist": "Dr. Michael Chen", "Allergist": "Dr. Sarah Johnson",
        "Immunologist": "Dr. Emily Rodriguez", "General Practitioner": "Dr. Sarah Johnson" # Simulating GP
    }

    primary_specialty = doctor_specialty
    if not primary_specialty and symptom:
        for key, specialty in symptom_map.items():
            if key in symptom.lower():
                primary_specialty = specialty
                break
    
    if not primary_specialty:
        return json.dumps({"status": "clarification_needed", "message": "To find the right doctor, could you tell me a bit about your symptoms or what specialty you're looking for?"})

    primary_doctor_name = doctor_map.get(primary_specialty)
    if not primary_doctor_name:
        return json.dumps({"status": "error", "message": f"We don't have a '{primary_specialty}'. Our specialties are Pulmonologist, Allergist, and Immunologist."})

    earliest_slot = calendar.get_earliest_slot(primary_doctor_name, datetime.now())
    if earliest_slot:
        return json.dumps({
            "status": "slot_found",
            "message": f"For your symptoms, I recommend a {primary_specialty}. The earliest appointment with {primary_doctor_name} is {earliest_slot.strftime('%A, %B %d at %I:%M %p')}.",
            "booking_details": {"doctor": primary_doctor_name, "iso_datetime": earliest_slot.isoformat()}
        })

    secondary_doctor_name = doctor_map.get("General Practitioner") 
    secondary_slot = calendar.get_earliest_slot(secondary_doctor_name, datetime.now())
    if secondary_slot:
        return json.dumps({
            "status": "alternative_found",
            "message": f"Our {primary_specialty} ({primary_doctor_name}) is fully booked right now. However, a General Practitioner ({secondary_doctor_name}) can see you for your {symptom}. Their earliest availability is {secondary_slot.strftime('%A, %B %d at %I:%M %p')}. Would that work?",
            "booking_details": {"doctor": secondary_doctor_name, "iso_datetime": secondary_slot.isoformat()}
        })
        
    return json.dumps({"status": "no_slots", "message": "I'm very sorry, but all of our relevant doctors are fully booked at the moment. Please try checking again tomorrow."})

@tool
def book_appointment(patient_id: str, doctor: str, iso_datetime: str) -> str:
    """Books an appointment for a VERIFIED patient using their patient_id."""
    calendar = CalendlyIntegration()
    email_service = EmailService()
    patient = db.get_patient_by_id(patient_id)
    if not patient: return f"Error: Patient with ID '{patient_id}' not found."

    appointment_time = datetime.fromisoformat(iso_datetime)
    duration = 60 if patient.patient_type == PatientType.NEW else 30
    booking_result = calendar.book_appointment(doctor, appointment_time, {"full_name": patient.full_name}, duration)
    if not (booking_result and booking_result.get("status") == "confirmed"):
        return "I apologize, but there appears to be an issue with booking. That slot may have just been taken by another patient. Please try finding another appointment."

    appointment_id = booking_result.get("booking_id")
    new_appointment = Appointment(
        id=appointment_id, patient_id=patient.id, doctor=doctor,
        location="Main Clinic", appointment_datetime=appointment_time, duration=duration,
        status=AppointmentStatus.SCHEDULED, created_at=datetime.now().isoformat()
    )
    db.create_appointment(new_appointment)
    
    get_reminder_system().schedule_appointment_reminders(appointment_id, appointment_time, patient.email, patient.phone)
    
    success_message = f"Excellent, you're all set! I've booked an appointment for {patient.full_name} with {doctor} on {appointment_time.strftime('%A, %B %d at %I:%M %p')}. You'll receive reminders from us."
    
    if patient.patient_type == PatientType.NEW:
        email_service.send_intake_forms(patient.__dict__, new_appointment.__dict__)
        success_message += " I have also emailed the New Patient Intake Form to your email. Please fill it out before your visit."

    return success_message

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class EnhancedMedicalSchedulingAgent:
    def __init__(self):
        system_prompt = """You are a warm, empathetic, and highly competent medical scheduling assistant named Alex.

        **Your Core Workflow:**
        1.  **Identify Patient:** Always start by trying to identify the patient with the `identify_patient` tool. Get their full name and DOB to do this.
        2.  **Returning Patient Flow:** If `identify_patient` is successful, greet them warmly and use the suggestion provided by the tool to be proactive. This logic is proven and works well.
        3.  **New Patient Flow:**
            - If `identify_patient` fails, the user is new. Welcome them and collect their phone/email to use the `register_new_patient` tool.
            - Once registered, ask them about their symptoms (e.g., "What symptoms are you experiencing?").
            - Use their answer in the `symptom` parameter of the `find_available_appointments` tool.
            - The tool will intelligently find the best specialist and even a backup option. Present the results from the tool clearly and conversationally to the patient.
        4.  **Be Human:** If a patient is unsure, be helpful. If you don't have enough information, ask for it politely. If a tool fails, apologize and offer an alternative path.
        """
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, system_instruction=system_prompt)
        tools = [identify_patient, register_new_patient, find_available_appointments, book_appointment]
        self.agent = self.llm.bind_tools(tools)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)
        graph.add_node("agent", self.call_agent)
        graph.add_node("tools", self.call_tools)
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", lambda state: "tools" if state["messages"][-1].tool_calls else END)
        graph.add_edge("tools", "agent")
        return graph.compile()

    def call_agent(self, state: AgentState):
        return {"messages": [self.agent.invoke(state["messages"])]}

    def call_tools(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        tool_messages = []
        for call in tool_calls:
            tool_name = call['name']
            tool_to_call = next((t for t in [identify_patient, register_new_patient, find_available_appointments, book_appointment] if t.name == tool_name), None)
            if tool_to_call:
                try:
                    result = tool_to_call.invoke(call['args'])
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name} with args {call['args']}: {e}")
                    result = f"An internal error occurred while using the {tool_name} tool."
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))
        return {"messages": tool_messages}

    def process_message(self, conversation_history: list):
        return self.graph.invoke({"messages": conversation_history})['messages']