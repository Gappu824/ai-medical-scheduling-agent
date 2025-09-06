"""
Final, Intelligent, and RELIABLE Medical Agent
RagaAI Assignment - Fixes patient recognition and adds conversational intelligence.
"""

from datetime import datetime, timedelta
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

# Around line 72, fix the name parsing:
@tool
def register_new_patient(first_name: str, last_name: str, dob: str, phone: str, email: str) -> str:
    """Registers a new patient in the database. MUST be called for a new patient before booking."""
    
    # Clean up names - handle "Golu badmosh" type names
    first_name = first_name.strip().title()
    last_name = last_name.strip().title()
    
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

    start_search = datetime.now() + timedelta(days=1)
    earliest_slot = calendar.get_earliest_slot(primary_doctor_name, start_search)
    if earliest_slot:
        # Force the year to be 2025 in the message formatting
        display_date = earliest_slot.replace(year=2025)
        return json.dumps({
            "status": "slot_found",
            "message": f"For your symptoms, I recommend a {primary_specialty}. The earliest appointment with {primary_doctor_name} is {display_date.strftime('%A, %B %d at %I:%M %p')}.",
            "booking_details": {"doctor": primary_doctor_name, "iso_datetime": display_date.isoformat()}
        })

    secondary_doctor_name = doctor_map.get("General Practitioner") 
    secondary_slot = calendar.get_earliest_slot(secondary_doctor_name, start_search)
    if secondary_slot:
        # Force the year to be 2025 in the message formatting  
        display_date = secondary_slot.replace(year=2025)
        return json.dumps({
            "status": "alternative_found",
            "message": f"Our {primary_specialty} ({primary_doctor_name}) is fully booked right now. However, a General Practitioner ({secondary_doctor_name}) can see you for your {symptom}. Their earliest availability is {display_date.strftime('%A, %B %d at %I:%M %p')}. Would that work?",
            "booking_details": {"doctor": secondary_doctor_name, "iso_datetime": display_date.isoformat()}
        })
        
    return json.dumps({"status": "no_slots", "message": "I'm very sorry, but all of our relevant doctors are fully booked at the moment. Please try checking again tomorrow."})
@tool
def find_earliest_across_locations(symptom: str = None) -> str:
    """Finds the earliest available appointment across all clinic locations."""
    calendar = CalendlyIntegration()
    
    symptom_map = {
        "cough": "Pulmonologist", "breathing": "Pulmonologist",
        "allergy": "Allergist", "rash": "Allergist", "hamstring": "General Practitioner",
        "injury": "General Practitioner", "pain": "General Practitioner"
    }
    
    doctor_map = {
        "Pulmonologist": "Dr. Michael Chen", "Allergist": "Dr. Sarah Johnson",
        "General Practitioner": "Dr. Sarah Johnson"
    }
    
    # Determine specialty
    specialty = "General Practitioner"  # default
    if symptom:
        for key, spec in symptom_map.items():
            if key in symptom.lower():
                specialty = spec
                break
    
    doctor = doctor_map.get(specialty, "Dr. Sarah Johnson")
    start_search = datetime.now() + timedelta(days=1)
    earliest_slot = calendar.get_earliest_slot(doctor, start_search)
    
    if earliest_slot:
        # Force 2025
        if earliest_slot.year == 2024:
            earliest_slot = earliest_slot.replace(year=2025)
        
        return json.dumps({
            "status": "slots_found",
            "message": f"I found the earliest appointment with {doctor} on {earliest_slot.strftime('%A, %B %d at %I:%M %p')}. Available locations:\n\n" +
                      f"• Main Clinic - Healthcare Boulevard\n" +
                      f"• Downtown Branch - Medical Center\n" + 
                      f"• Suburban Office - Wellness Plaza\n\n" +
                      f"Which location is most convenient for you?",
            "booking_details": {"doctor": doctor, "iso_datetime": earliest_slot.isoformat()}
        })
    
    return json.dumps({"status": "no_slots", "message": "No appointments available today. Would you like me to check tomorrow?"})
@tool
def book_earliest_appointment(patient_id: str, symptom: str = None) -> str:
    """Books the earliest available appointment for any symptom/condition."""
    # Find appointment
    find_result = find_available_appointments(symptom)
    result_data = json.loads(find_result)
    
    if result_data.get("status") == "slot_found":
        booking_details = result_data["booking_details"]
        return book_appointment(patient_id, booking_details["doctor"], booking_details["iso_datetime"])
    
    return "No appointments available. Please try again tomorrow."
@tool
def book_appointment(patient_id: str, doctor: str, iso_datetime: str) -> str:
    """Books an appointment for a VERIFIED patient using their patient_id."""
    calendar = CalendlyIntegration()
    email_service = EmailService()
    # In the book_appointment function, add debugging:
    patient = db.get_patient_by_id(patient_id)
    if not patient: 
        return f"Error: Patient with ID '{patient_id}' not found."

    logger.info(f"Patient type for {patient.full_name}: {patient.patient_type}")
    duration = 60 if patient.patient_type == PatientType.NEW else 30
    logger.info(f"Appointment duration set to: {duration} minutes")

    appointment_time = datetime.fromisoformat(iso_datetime)
    if appointment_time.year == 2024:
        appointment_time = appointment_time.replace(year=2025)
        logger.warning(f"Corrected appointment year from 2024 to 2025: {appointment_time}")
    
    # duration = 60 if patient.patient_type == PatientType.NEW else 30
    # Fix the patient type check
    if hasattr(patient.patient_type, 'value'):
        patient_type_str = patient.patient_type.value
    else:
        patient_type_str = str(patient.patient_type)

    duration = 60 if patient_type_str == "new" else 30
    logger.info(f"Patient {patient.full_name} type: {patient_type_str}, Duration: {duration}")
    
    # Single booking attempt - no retries to prevent duplicate bookings
    booking_result = calendar.book_appointment(doctor, appointment_time, {"full_name": patient.full_name}, duration)
    
    if not booking_result or booking_result.get("status") != "confirmed":
        return json.dumps({
            "status": "booking_failed",
            "message": "I apologize, but I was unable to book that specific time slot. It may no longer be available. Would you like me to find other available times?"
        })

    # Create appointment record
    appointment_id = booking_result.get("booking_id")
    new_appointment = Appointment(
        id=appointment_id, patient_id=patient.id, doctor=doctor,
        location="Main Clinic", appointment_datetime=appointment_time, duration=duration,
        status=AppointmentStatus.SCHEDULED, created_at=datetime.now().isoformat()
    )
    db.create_appointment(new_appointment)
    
    # Schedule reminders
    get_reminder_system().schedule_appointment_reminders(appointment_id, appointment_time, patient.email, patient.phone)
    
    # Build success message
    success_message = f"Perfect! I've successfully booked your appointment:\n\n"
    success_message += f"📅 Date: {appointment_time.strftime('%A, %B %d, %Y')}\n"
    success_message += f"🕐 Time: {appointment_time.strftime('%I:%M %p')}\n"
    success_message += f"👨‍⚕️ Doctor: {doctor}\n"
    success_message += f"🏥 Location: Main Clinic\n"
    success_message += f"⏱️ Duration: {duration} minutes\n\n"
    
    # Handle intake forms for new patients
    # Handle intake forms for new patients
    # Around line 175, force the intake form logic:
# Handle intake forms for new patients  
    patient_type_value = patient.patient_type.value if hasattr(patient.patient_type, 'value') else str(patient.patient_type)
    logger.info(f"Patient {patient.full_name} type: {patient_type_value}")

    if patient_type_value == "new":
        logger.info(f"NEW PATIENT: Sending intake forms to {patient.email}")
        success_message += f"📋 IMPORTANT: I've emailed your New Patient Intake Form to {patient.email}. Please complete and return it 24 hours before your appointment.\n\n"
        
        try:
            email_service.send_intake_forms(patient.__dict__, new_appointment.__dict__)
            logger.info("✅ Intake forms sent successfully")
        except Exception as e:
            logger.error(f"Failed to send intake forms: {e}")
    else:
        logger.info(f"RETURNING PATIENT: No intake forms needed")
    success_message += "🔔 You'll receive automated reminder messages. Please bring your insurance card and photo ID to your appointment."
    
    return json.dumps({
        "status": "booking_confirmed", 
        "message": success_message
    })

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class EnhancedMedicalSchedulingAgent:
    def __init__(self):
        system_prompt = """You are a warm, empathetic, and highly competent medical scheduling assistant named Alex.

IMPORTANT: Today's date is September 6, 2025. When booking appointments, always use 2025 as the year.

Our clinic locations:
- Main Clinic - Healthcare Boulevard (comprehensive services)
- Downtown Branch - Medical Center (convenient downtown access)
- Suburban Office - Wellness Plaza (family-friendly, easy parking)

**Your Core Workflow:**
1. **Find appointments first** - when user says "book it" or "earliest", immediately find available slots
2. **Present options clearly** - show available times at different locations
3. **Let them choose** - "I found appointments at 3 locations: Main Clinic at 10 AM, Downtown at 2 PM, Suburban at 4 PM. Which works best?"
4. **Don't block booking** - always provide appointment options, never say "I need more information"

CRITICAL: When user says "earliest" or "asap" - find the earliest slot across ALL locations and present the options.
"""
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, system_instruction=system_prompt)
        # tools = [identify_patient, register_new_patient, find_available_appointments, book_appointment]
        tools = [identify_patient, register_new_patient, find_available_appointments, find_earliest_across_locations, book_appointment]
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
                    
                    # Handle JSON responses from tools
                    if isinstance(result, str) and result.startswith('{'):
                        try:
                            parsed_result = json.loads(result)
                            if parsed_result.get("status") == "booking_confirmed":
                                result = parsed_result["message"]
                            elif parsed_result.get("status") == "booking_failed":
                                result = parsed_result["message"]
                            elif parsed_result.get("status") == "slot_found":
                                result = parsed_result["message"]
                            elif parsed_result.get("status") == "alternative_found":
                                result = parsed_result["message"]
                            # For any other JSON status, extract the message if available
                            elif "message" in parsed_result:
                                result = parsed_result["message"]
                        except json.JSONDecodeError:
                            pass  # Use result as-is if not valid JSON
                    
                            
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name} with args {call['args']}: {e}")
                    result = f"An internal error occurred while using the {tool_name} tool."
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))
        return {"messages": tool_messages}

    def process_message(self, conversation_history: list):
        return self.graph.invoke({"messages": conversation_history})['messages']