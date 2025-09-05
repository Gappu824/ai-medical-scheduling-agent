"""
Production-Grade AI Medical Scheduling Agent
RagaAI Assignment - Final, Stateful, and Truly Interactive Implementation
"""
from datetime import datetime, timedelta
from typing import TypedDict, Annotated, List

from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from database.database import DatabaseManager
from integrations.calendly_integration import CalendlyIntegration

# --- 1. Define More Flexible and Intelligent Tools ---

@tool
def get_date_for_relative_request(relative_date_request: str) -> str:
    """
    Calculates the actual date (YYYY-MM-DD) for a relative request like "tomorrow", "next Wednesday", or "in two weeks".
    """
    today = datetime.now()
    request = relative_date_request.lower()
    
    if "today" in request:
        return today.strftime("%Y-%m-%d")
    if "tomorrow" in request:
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for i, day in enumerate(weekdays):
        if day in request:
            days_ahead = i - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            return (today + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
            
    return "Error: Could not determine a specific date. Please ask the user to clarify."

@tool
def find_available_appointments(doctor_specialty: str, desired_date: str) -> str:
    """
    Finds available appointment slots for a specific doctor specialty (e.g., 'Pulmonologist', 'Allergist') on a specific date (YYYY-MM-DD).
    Returns a list of available slots as a string.
    """
    print(f"--- TOOL: Finding slots for {doctor_specialty} on {desired_date} ---")
    calendar = CalendlyIntegration()
    doctor_map = {"pulmonologist": "Dr. Michael Chen", "allergist": "Dr. Sarah Johnson", "immunologist": "Dr. Emily Rodriguez"}
    doctor_name = next((name for spec, name in doctor_map.items() if spec in doctor_specialty.lower()), None)
    
    if not doctor_name:
        return f"Error: The specialty '{doctor_specialty}' is not recognized. Available specialties are Pulmonologist, Allergist, Immunologist."

    try:
        check_date = datetime.strptime(desired_date, "%Y-%m-%d")
        if check_date.weekday() > 4: # Saturday or Sunday
             return f"The clinic is closed on weekends. No appointments are available on {desired_date}."

        slots = calendar.get_available_slots(doctor_name, check_date, 30)
        if slots:
            slot_strings = [s.strftime('%I:%M %p') for s in slots]
            return f"On {check_date.strftime('%A, %B %d')}, the following slots are available for {doctor_name} ({doctor_specialty}): {', '.join(slot_strings)}"
        return f"No available slots were found for {doctor_name} on {desired_date}. Please ask the user if they'd like to try a different day."
    except Exception as e:
        return f"Error finding slots: {str(e)}. The date format must be YYYY-MM-DD."

@tool
def search_for_patient(first_name: str, last_name: str, dob: str) -> str:
    """
    Searches the database for an existing patient using their first name, last_name, and date of birth (YYYY-MM-DD).
    Returns a string with patient details if found, or a message indicating the patient is new.
    """
    print(f"--- TOOL: Searching for patient: {first_name} {last_name}, DOB: {dob} ---")
    db = DatabaseManager()
    try:
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%B %d, %Y"):
            try:
                normalized_dob = datetime.strptime(dob, fmt).strftime("%Y-%m-%d")
                break
            except ValueError:
                pass
        else:
            normalized_dob = dob
            
        patient = db.find_patient(first_name=first_name, last_name=last_name, dob=normalized_dob)
        if patient:
            return f"Patient Found: Name={patient.full_name}, Type={patient.patient_type.value}. This is a returning patient. The appointment duration will be 30 minutes."
        return "Patient Not Found. This is a new patient. The appointment duration will be 60 minutes."
    except Exception as e:
        return f"Error searching for patient: {e}"

@tool
def book_appointment(doctor: str, iso_datetime: str, patient_full_name: str, duration: int) -> str:
    """
    Books the selected appointment slot for the patient. Use the full ISO datetime string for the appointment and the correct duration (60 for new patients, 30 for returning).
    """
    print(f"--- TOOL: Booking appointment for {patient_full_name} with {doctor} at {iso_datetime} for {duration} mins ---")
    calendar = CalendlyIntegration()
    try:
        appointment_time = datetime.fromisoformat(iso_datetime)
        patient_data = {"full_name": patient_full_name}
        
        booking_result = calendar.book_appointment(doctor, appointment_time, patient_data, duration)
        if booking_result and booking_result.get("status") == "confirmed":
            return f"Success! The appointment for {patient_full_name} with {doctor} at {appointment_time.strftime('%A, %B %d at %I:%M %p')} is confirmed. You should now ask for insurance information to finalize the process."
        else:
            return "Error: Could not book the appointment. The slot may have been taken. Please offer the user alternative times."
    except Exception as e:
        return f"An error occurred while booking: {e}"

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class MedicalSchedulingAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
        tools = [search_for_patient, find_available_appointments, get_date_for_relative_request, book_appointment]
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
            tool_to_call = next((t for t in [search_for_patient, find_available_appointments, get_date_for_relative_request, book_appointment] if t.name == tool_name), None)
            if tool_to_call:
                try:
                    result = tool_to_call.invoke(call['args'])
                except Exception as e:
                    result = f"Error executing tool {tool_name}: {e}"
                tool_messages.append(ToolMessage(content=str(result), tool_call_id=call['id']))
        return {"messages": tool_messages}

    def process_message(self, conversation_history: list):
        final_state = self.graph.invoke({"messages": conversation_history})
        return final_state['messages']

EnhancedMedicalSchedulingAgent = MedicalSchedulingAgent