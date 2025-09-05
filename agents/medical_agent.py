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

logger = logging.getLogger(__name__)

# --- Enhanced Tools with Reminder Integration ---

@tool
def get_date_for_relative_request(relative_date_request: str) -> str:
    """Calculate actual date (YYYY-MM-DD) for relative requests like 'tomorrow', 'next Wednesday'"""
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
            
    return "Error: Could not determine date. Please ask user to clarify."

@tool
def find_available_appointments(doctor_specialty: str, desired_date: str) -> str:
    """Find available slots for doctor specialty on specific date"""
    print(f"--- TOOL: Finding slots for {doctor_specialty} on {desired_date} ---")
    calendar = CalendlyIntegration()
    doctor_map = {
        "pulmonologist": "Dr. Michael Chen", 
        "allergist": "Dr. Sarah Johnson", 
        "immunologist": "Dr. Emily Rodriguez"
    }
    doctor_name = next((name for spec, name in doctor_map.items() if spec in doctor_specialty.lower()), None)
    
    if not doctor_name:
        return f"Error: '{doctor_specialty}' not recognized. Available: Pulmonologist, Allergist, Immunologist."

    try:
        check_date = datetime.strptime(desired_date, "%Y-%m-%d")
        if check_date.weekday() > 4:
             return f"Clinic closed weekends. No appointments on {desired_date}."

        slots = calendar.get_available_slots(doctor_name, check_date, 30)
        if slots:
            slot_strings = [s.strftime('%I:%M %p') for s in slots]
            return f"On {check_date.strftime('%A, %B %d')}, available for {doctor_name} ({doctor_specialty}): {', '.join(slot_strings)}"
        return f"No slots available for {doctor_name} on {desired_date}. Try different day?"
    except Exception as e:
        return f"Error finding slots: {str(e)}. Date format must be YYYY-MM-DD."

@tool
def search_for_patient(first_name: str, last_name: str, dob: str) -> str:
    """Search database for existing patient using name and DOB"""
    print(f"--- TOOL: Searching for patient: {first_name} {last_name}, DOB: {dob} ---")
    db = DatabaseManager()
    try:
        # Normalize DOB format
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
            return f"Patient Found: {patient.full_name}, Type={patient.patient_type.value}. Returning patient - 30 minute appointment."
        return "Patient Not Found. New patient - 60 minute appointment."
    except Exception as e:
        return f"Error searching patient: {e}"

@tool
def book_appointment(doctor: str, iso_datetime: str, patient_full_name: str, duration: int) -> str:
    """
    Book appointment AND automatically trigger reminder system
    This is the key integration point!
    """
    print(f"--- TOOL: Booking appointment for {patient_full_name} with {doctor} at {iso_datetime} for {duration} mins ---")
    calendar = CalendlyIntegration()
    
    try:
        appointment_time = datetime.fromisoformat(iso_datetime)
        patient_data = {"full_name": patient_full_name}
        
        # Book the appointment
        booking_result = calendar.book_appointment(doctor, appointment_time, patient_data, duration)
        
        if booking_result and booking_result.get("status") == "confirmed":
            appointment_id = booking_result.get("booking_id")
            
            # *** CRITICAL: Trigger reminder system after successful booking ***
            success_message = f"Success! Appointment for {patient_full_name} with {doctor} at {appointment_time.strftime('%A, %B %d at %I:%M %p')} is confirmed."
            
            # Get patient details for reminders
            db = DatabaseManager()
            name_parts = patient_full_name.split(' ', 1)
            if len(name_parts) >= 2:
                first_name, last_name = name_parts[0], name_parts[1]
                
                # Find patient to get email/phone
                patient = db.find_patient(first_name, last_name, "")  # We'd need DOB for exact match
                
                if patient and patient.email:
                    # Trigger the reminder system
                    reminder_success = trigger_appointment_reminders(
                        appointment_id, 
                        appointment_time,
                        patient.email,
                        patient.phone
                    )
                    
                    if reminder_success:
                        success_message += " 3-tier reminder system activated (7-day, 24-hour, 2-hour reminders)."
                    else:
                        success_message += " Appointment booked but reminder setup had issues."
                else:
                    success_message += " Appointment booked. Please provide patient email for reminders."
            
            success_message += " Please ask for insurance information to complete the process."
            return success_message
        else:
            return "Error: Could not book appointment. Slot may be taken. Please try alternative times."
    except Exception as e:
        return f"Booking error: {e}"

def trigger_appointment_reminders(appointment_id: str, appointment_datetime: datetime, 
                                patient_email: str, patient_phone: str = None) -> bool:
    """
    THE MISSING PIECE: Trigger 3-tier reminder system after booking
    This creates reminders in database AND processes immediate sends
    """
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        # Ensure reminders table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL CHECK(reminder_type IN ('initial', 'form_check', 'final_confirmation')),
            scheduled_time TEXT NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            email_sent BOOLEAN DEFAULT FALSE,
            sms_sent BOOLEAN DEFAULT FALSE,
            response_received BOOLEAN DEFAULT FALSE,
            patient_email TEXT,
            patient_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Create 3-tier reminder schedule
        reminders = [
            {
                'type': 'initial',
                'time': appointment_datetime - timedelta(days=7),
                'description': '7-day initial reminder'
            },
            {
                'type': 'form_check',
                'time': appointment_datetime - timedelta(hours=24), 
                'description': '24-hour form completion check'
            },
            {
                'type': 'final_confirmation',
                'time': appointment_datetime - timedelta(hours=2),
                'description': '2-hour final confirmation'
            }
        ]
        
        created_count = 0
        current_time = datetime.now()
        
        for reminder in reminders:
            # Insert reminder into database
            cursor.execute("""
            INSERT INTO reminders 
            (appointment_id, reminder_type, scheduled_time, patient_email, patient_phone)
            VALUES (?, ?, ?, ?, ?)
            """, (
                appointment_id,
                reminder['type'],
                reminder['time'].isoformat(),
                patient_email,
                patient_phone
            ))
            
            created_count += 1
            logger.info(f"📅 Scheduled {reminder['description']} for {appointment_id}")
            
            # If reminder time has already passed, send immediately
            if reminder['time'] <= current_time:
                send_immediate_reminder(
                    appointment_id, 
                    reminder['type'],
                    patient_email,
                    patient_phone,
                    appointment_datetime
                )
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created {created_count} reminders for appointment {appointment_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error creating reminders: {e}")
        return False

def send_immediate_reminder(appointment_id: str, reminder_type: str, 
                          patient_email: str, patient_phone: str,
                          appointment_datetime: datetime):
    """Send reminder immediately if due"""
    try:
        # Try to import and use email service
        try:
            from integrations.email_service import EmailService
            email_service = EmailService()
            
            email_content = create_reminder_email_content(reminder_type, appointment_datetime)
            email_sent = email_service.send_reminder_email(patient_email, email_content)
            
            if email_sent:
                logger.info(f"📧 Sent {reminder_type} email reminder to {patient_email}")
        except ImportError:
            logger.warning("Email service not available")
            email_sent = False
        
        # Try to send SMS
        try:
            from integrations.sms_service import SMSService
            sms_service = SMSService()
            
            sms_content = create_reminder_sms_content(reminder_type, appointment_datetime)
            sms_sent = sms_service.send_sms(patient_phone, sms_content)
            
            if sms_sent:
                logger.info(f"📱 Sent {reminder_type} SMS reminder to {patient_phone}")
        except ImportError:
            logger.warning("SMS service not available")
            sms_sent = False
        
        # Update reminder as sent
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE reminders 
        SET sent = TRUE, email_sent = ?, sms_sent = ?
        WHERE appointment_id = ? AND reminder_type = ?
        """, (email_sent, sms_sent, appointment_id, reminder_type))
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ Error sending immediate reminder: {e}")

def create_reminder_email_content(reminder_type: str, appointment_datetime: datetime) -> str:
    """Create email content based on reminder type"""
    
    if reminder_type == "initial":
        return f"""
        🏥 MediCare Appointment Reminder
        
        Your appointment is scheduled for {appointment_datetime.strftime('%A, %B %d at %I:%M %p')}.
        
        Please mark your calendar and we'll send you forms to complete soon.
        
        Call (555) 123-4567 if you need to reschedule.
        """
    
    elif reminder_type == "form_check":
        return f"""
        🏥 MediCare - Action Required!
        
        Your appointment is TOMORROW: {appointment_datetime.strftime('%A, %B %d at %I:%M %p')}
        
        ✅ Please confirm:
        1. Have you completed your intake forms?
        2. Will you be attending your appointment?
        
        Reply to this email or call (555) 123-4567.
        
        If you need to cancel, please let us know immediately.
        """
    
    elif reminder_type == "final_confirmation":
        return f"""
        🚨 MediCare - Final Reminder!
        
        Your appointment is in 2 HOURS: {appointment_datetime.strftime('%I:%M %p TODAY')}
        
        📍 Location: Main Clinic - 456 Healthcare Blvd
        ⏰ Please arrive 15 minutes early
        📋 Bring: Insurance card, ID, completed forms
        
        Last chance to cancel: (555) 123-4567
        """

def create_reminder_sms_content(reminder_type: str, appointment_datetime: datetime) -> str:
    """Create SMS content based on reminder type"""
    
    if reminder_type == "initial":
        return f"🏥 MediCare: Appointment reminder {appointment_datetime.strftime('%m/%d at %I:%M%p')}. Forms coming soon. Call (555) 123-4567 to reschedule."
    
    elif reminder_type == "form_check": 
        return f"🏥 MediCare: Appointment TOMORROW {appointment_datetime.strftime('%I:%M%p')}. Completed forms? Reply YES/NO. Confirm visit? Reply CONFIRM/CANCEL."
    
    elif reminder_type == "final_confirmation":
        return f"🚨 MediCare: Appointment in 2 HOURS at {appointment_datetime.strftime('%I:%M%p')}! Arrive 15min early. 456 Healthcare Blvd. Cancel: (555) 123-4567"

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

class EnhancedMedicalSchedulingAgent:
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

# Compatibility
MedicalSchedulingAgent = EnhancedMedicalSchedulingAgent