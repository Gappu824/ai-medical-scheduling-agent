"""
Fixed Medical Agent with Complete Reminder Integration
RagaAI Assignment - All 7 Features + 3-Tier Reminder System
"""

from datetime import datetime, timedelta
from typing import TypedDict, Annotated, List
import sqlite3
import json
import logging

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from database.database import DatabaseManager
from integrations.calendly_integration import CalendlyIntegration
# FIX: Added missing Patient and PatientType imports
from database.models import Appointment, AppointmentStatus, Patient, PatientType

logger = logging.getLogger(__name__)

# --- Enhanced Tools with Full Backend Integration ---

@tool
def search_for_patient(first_name: str, last_name: str, dob: str) -> str:
    """
    Searches the database for an existing patient using their first name, last name, and date of birth.
    Returns 'Patient Not Found' if no record exists.
    """
    print(f"--- TOOL: Searching for patient: {first_name} {last_name}, DOB: {dob} ---")
    db = DatabaseManager()
    try:
        # Normalize DOB format
        for fmt in ("%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"):
            try:
                normalized_dob = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
        else:
            normalized_dob = dob
            
        patient = db.find_patient(first_name=first_name, last_name=last_name, dob=normalized_dob)
        if patient:
            return f"Patient Found: {patient.full_name}, Type={patient.patient_type.value}. This is a returning patient."
        return "Patient Not Found. This is a new patient. You must register them before booking."
    except Exception as e:
        return f"Error searching patient: {e}"

@tool
def register_new_patient(first_name: str, last_name: str, dob: str, phone: str, email: str) -> str:
    """
    Registers a new patient in the database. This tool MUST be called for any new patient
    before attempting to book an appointment. It requires full name, DOB, phone, and email.
    """
    print(f"--- TOOL: Registering new patient: {first_name} {last_name} ---")
    db = DatabaseManager()
    
    # Normalize DOB
    for fmt in ("%d-%m-%Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            normalized_dob = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
            break
        except ValueError:
            pass
    else:
        normalized_dob = dob
        
    patient_data = {
        "first_name": first_name,
        "last_name": last_name,
        "dob": normalized_dob,
        "phone": phone,
        "email": email
    }
    
    try:
        new_patient = db.create_patient(patient_data)
        if new_patient:
            return f"Successfully registered new patient: {new_patient.full_name}. You can now proceed with booking their appointment."
        else:
            return "Failed to register new patient. Please check the details and try again."
    except Exception as e:
        logger.error(f"Error registering new patient: {e}")
        return f"An error occurred during patient registration: {e}"

@tool
def find_available_appointments(doctor_specialty: str, desired_date: str = "earliest") -> str:
    """
    Finds available appointment slots. If the desired_date is 'earliest' or not provided, 
    it will find the very next available appointment.
    """
    print(f"--- TOOL: Finding slots for {doctor_specialty} on {desired_date} ---")
    calendar = CalendlyIntegration()
    doctor_map = {
        "pulmonologist": "Dr. Michael Chen", 
        "allergist": "Dr. Sarah Johnson", 
        "immunologist": "Dr. Emily Rodriguez"
    }
    doctor_name = next((name for spec, name in doctor_map.items() if spec in doctor_specialty.lower()), None)
    
    if not doctor_name:
        return f"Error: '{doctor_specialty}' is not a recognized specialty. Please choose from Pulmonologist, Allergist, or Immunologist."

    try:
        if desired_date.lower() in ["earliest", "soonest", "whenever available", ""]:
            earliest_slot = calendar.get_earliest_slot(doctor_name, datetime.now())
            if earliest_slot:
                slot_date = earliest_slot.strftime('%A, %B %d, %Y')
                slot_time = earliest_slot.strftime('%I:%M %p')
                return f"I found the earliest available appointment for a {doctor_specialty} ({doctor_name}) is on {slot_date} at {slot_time}. Does this time work for you?"
            else:
                return f"I'm sorry, there are no available appointments for {doctor_name} in the next 30 days."
        else:
            check_date = datetime.strptime(desired_date, "%Y-%m-%d")
            slots = calendar.get_available_slots(doctor_name, check_date, 30)
            if slots:
                slot_strings = [s.strftime('%I:%M %p') for s in slots]
                return f"On {check_date.strftime('%A, %B %d')}, these time slots are available for {doctor_name} ({doctor_specialty}): {', '.join(slot_strings)}"
            return f"No slots were found for {doctor_name} on {desired_date}. Would you like to try a different day?"
    except Exception as e:
        return f"Error finding slots: {e}"
        
@tool
def book_appointment(doctor: str, iso_datetime: str, patient_full_name: str) -> str:
    """
    Books an appointment for a REGISTERED patient. Requires the patient's full name.
    This tool will fail if the patient is not already in the database.
    """
    print(f"--- TOOL: Booking appointment for {patient_full_name} with {doctor} at {iso_datetime} ---")
    calendar = CalendlyIntegration()
    db = DatabaseManager()
    
    try:
        appointment_time = datetime.fromisoformat(iso_datetime)
        
        name_parts = patient_full_name.split(' ', 1)
        if len(name_parts) < 2:
            return "Error: Please provide both first and last name for the patient."
            
        patient = db.find_patient(name_parts[0], name_parts[1], "") 
        
        if not patient:
            return f"Error: Patient '{patient_full_name}' is not registered. You MUST register the patient before booking."

        duration = 60 if patient.patient_type == PatientType.NEW else 30
        
        booking_result = calendar.book_appointment(doctor, appointment_time, {"full_name": patient_full_name}, duration)
        
        if not (booking_result and booking_result.get("status") == "confirmed"):
            return "Error: Could not book in calendar. The slot may be taken."

        appointment_id = booking_result.get("booking_id")
        
        new_appointment = Appointment(
            id=appointment_id,
            patient_id=patient.id,
            doctor=doctor,
            location=booking_result.get("location", "Main Clinic"),
            appointment_datetime=appointment_time,
            duration=duration,
            status=AppointmentStatus.SCHEDULED
        )
        db.create_appointment(new_appointment)

        from integrations.reminder_system import get_reminder_system
        reminder_system = get_reminder_system()
        reminder_system.schedule_appointment_reminders(
            appointment_id, appointment_time, patient.email, patient.phone
        )
        
        return f"Success! Appointment for {patient_full_name} confirmed with {doctor} on {appointment_time.strftime('%A, %B %d at %I:%M %p')}. The reminder system is active."

    except Exception as e:
        logger.error(f"Booking tool error: {e}")
        return f"A critical error occurred during booking: {e}"

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class EnhancedMedicalSchedulingAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
        tools = [search_for_patient, register_new_patient, find_available_appointments, book_appointment]
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
            tool_to_call = next((t for t in [search_for_patient, register_new_patient, find_available_appointments, book_appointment] if t.name == tool_name), None)
            if tool_to_call:
                try:
                    result = tool_to_call.invoke(call['args'])
                except Exception as e:
                    result = f"Error executing tool {tool_name}: {e}"
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))
        return {"messages": tool_messages}

    def process_message(self, conversation_history: list):
        return self.graph.invoke({"messages": conversation_history})['messages']

# Compatibility
MedicalSchedulingAgent = EnhancedMedicalSchedulingAgent