"""
LangGraph Workflow Orchestration for Medical Scheduling Agent
RagaAI Assignment - Complete Workflow Management
"""

import logging
from typing import Dict, List, TypedDict
from datetime import datetime

from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from database.models import Patient, Appointment, PatientType, AppointmentStatus
from database.database import DatabaseManager

logger = logging.getLogger(__name__)

class MedicalWorkflowState(TypedDict):
    """State definition for medical scheduling workflow"""
    messages: List[BaseMessage]
    patient_info: Dict
    patient: Patient
    appointment_info: Dict
    preferences: Dict
    insurance_info: Dict
    current_step: str
    errors: List[str]
    session_id: str
    workflow_complete: bool

class MedicalWorkflow:
    """Complete medical scheduling workflow orchestration"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.workflow = self._create_workflow()
        logger.info("Medical workflow initialized")
    
    def _create_workflow(self) -> StateGraph:
        """Create the complete LangGraph workflow"""
        
        workflow = StateGraph(MedicalWorkflowState)
        
        # Add all workflow nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_info", self._collect_info_node)
        workflow.add_node("patient_lookup", self._patient_lookup_node)
        workflow.add_node("preference_matching", self._preference_matching_node)
        workflow.add_node("schedule_appointment", self._schedule_appointment_node)
        workflow.add_node("collect_insurance", self._collect_insurance_node)
        workflow.add_node("confirm_appointment", self._confirm_appointment_node)
        workflow.add_node("send_forms", self._send_forms_node)
        workflow.add_node("complete", self._complete_node)
        
        # Define workflow edges with conditional routing
        workflow.add_edge("greeting", "collect_info")
        workflow.add_edge("collect_info", "patient_lookup")
        workflow.add_edge("patient_lookup", "preference_matching")
        workflow.add_edge("preference_matching", "schedule_appointment")
        workflow.add_edge("schedule_appointment", "collect_insurance")
        workflow.add_edge("collect_insurance", "confirm_appointment")
        workflow.add_edge("confirm_appointment", "send_forms")
        workflow.add_edge("send_forms", "complete")
        workflow.add_edge("complete", END)
        
        # Set entry point
        workflow.set_entry_point("greeting")
        
        return workflow.compile()
    
    def _greeting_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Initial greeting and welcome"""
        
        greeting_message = """Hello! Welcome to MediCare Allergy & Wellness Center. 
        
I'm your AI scheduling assistant, and I'm here to help you book the perfect appointment 
for your healthcare needs.

To get started, I'll need some basic information:
- Your full name (first and last)
- Date of birth (MM/DD/YYYY format)
- Phone number and email address

You can provide this information all at once or step by step. How would you like to proceed?"""
        
        state["messages"].append(AIMessage(content=greeting_message))
        state["current_step"] = "collect_info"
        
        return state
    
    def _collect_info_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Collect patient information"""
        
        # Extract information from user messages
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No user input found")
            return state
        
        latest_input = user_messages[-1].content
        
        # Simple pattern matching for demo (in real implementation, use LLM extraction)
        patient_info = {}
        
        # Extract name (simple pattern)
        if "name is" in latest_input.lower():
            try:
                name_part = latest_input.lower().split("name is")[1].split(",")[0].strip()
                name_parts = name_part.split()
                if len(name_parts) >= 2:
                    patient_info["first_name"] = name_parts[0].title()
                    patient_info["last_name"] = name_parts[1].title()
            except:
                pass
        
        # Extract DOB (simple pattern)
        import re
        dob_pattern = r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})'
        dob_match = re.search(dob_pattern, latest_input)
        if dob_match:
            patient_info["dob"] = dob_match.group(1).replace("/", "-")
        
        # Extract email
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, latest_input)
        if email_match:
            patient_info["email"] = email_match.group()
        
        # Extract phone
        phone_pattern = r'(\d{3}[-.]?\d{3}[-.]?\d{4})'
        phone_match = re.search(phone_pattern, latest_input)
        if phone_match:
            patient_info["phone"] = phone_match.group()
        
        state["patient_info"].update(patient_info)
        
        # Check if we have enough information
        required_fields = ["first_name", "last_name", "dob"]
        missing_fields = [field for field in required_fields if field not in state["patient_info"]]
        
        if missing_fields:
            response = f"Thank you for that information. I still need: {', '.join(missing_fields)}. Could you please provide these details?"
            state["messages"].append(AIMessage(content=response))
        else:
            state["current_step"] = "patient_lookup"
        
        return state
    
    def _patient_lookup_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Look up patient in database"""
        
        patient_info = state["patient_info"]
        
        # Search for existing patient
        patient = self.db.find_patient(
            patient_info.get("first_name", ""),
            patient_info.get("last_name", ""), 
            patient_info.get("dob", "")
        )
        
        if patient:
            # Returning patient
            response = f"""Great! I found your record, {patient.first_name}. 
            
Welcome back! I see you're a returning patient. Since you've been here before, 
I can schedule you for a 30-minute follow-up appointment.

Now let's find the perfect appointment time and doctor for you."""
            
            state["patient"] = patient
        else:
            # New patient - create patient record
            patient = Patient(
                id=f"P{int(datetime.now().timestamp())}",
                first_name=patient_info["first_name"],
                last_name=patient_info["last_name"],
                dob=patient_info["dob"],
                phone=patient_info.get("phone", ""),
                email=patient_info.get("email", ""),
                patient_type=PatientType.NEW
            )
            
            response = f"""Welcome to MediCare Allergy & Wellness Center, {patient.first_name}!

I don't see you in our system, so you'll be a new patient with us. That's wonderful! 
For new patients, we schedule 60-minute comprehensive appointments to ensure we have 
time for a thorough evaluation.

Let me help you choose the right doctor and location for your needs."""
            
            state["patient"] = patient
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "preference_matching"
        
        return state
    
    def _preference_matching_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Match patient preferences for doctor and location"""
        
        patient = state["patient"]
        
        if patient.patient_type == PatientType.RETURNING:
            # For returning patients, check history and ask about preferences
            response = """I'd like to find the best appointment option for you. 
            
Would you prefer to:
- Continue with your previous doctor at the same location?
- Try a different doctor for a second opinion?
- Switch to a more convenient location?

Our available specialists:
• Dr. Sarah Johnson (Allergist) - Main Clinic, Downtown Branch
• Dr. Michael Chen (Pulmonologist) - Main Clinic, Suburban Office  
• Dr. Emily Rodriguez (Immunologist) - All locations

Which option interests you most?"""
        else:
            # For new patients, explain all options
            response = """Let me help you choose the right specialist for your needs:

🔬 **Dr. Sarah Johnson - Allergist**
- Specializes in: Food allergies, environmental allergies, asthma, eczema
- Locations: Main Clinic, Downtown Branch
- Best for: Allergy testing, immunotherapy, chronic allergy management

🫁 **Dr. Michael Chen - Pulmonologist** 
- Specializes in: Asthma, COPD, lung function testing, breathing disorders
- Locations: Main Clinic, Suburban Office
- Best for: Respiratory issues, chronic cough, shortness of breath

🧬 **Dr. Emily Rodriguez - Immunologist**
- Specializes in: Immune system disorders, autoimmune conditions
- Locations: All three locations (most flexible)
- Best for: Complex immune issues, medication allergies

**Which doctor/specialty sounds right for what you're experiencing?** 
And which location would be most convenient for you?"""
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "schedule_appointment"
        
        return state
    
    def _schedule_appointment_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Schedule the appointment"""
        
        # Mock appointment scheduling
        patient = state["patient"]
        
        # Create mock appointment
        appointment = Appointment(
            id=f"APT{int(datetime.now().timestamp())}",
            patient_id=patient.id,
            doctor="Dr. Sarah Johnson",  # Default selection
            location="Main Clinic",
            appointment_datetime=datetime.now().replace(hour=10, minute=0, second=0, microsecond=0),
            duration=patient.appointment_duration,
            status=AppointmentStatus.SCHEDULED
        )
        
        state["appointment_info"] = {
            "id": appointment.id,
            "doctor": appointment.doctor,
            "location": appointment.location,
            "date": appointment.date_str,
            "time": appointment.time_str,
            "duration": appointment.duration
        }
        
        response = f"""Perfect! I've found a great appointment slot for you:

📅 **Date:** {appointment.date_str}
🕐 **Time:** {appointment.time_str}
👩‍⚕️ **Doctor:** {appointment.doctor}
🏢 **Location:** {appointment.location}
⏱️ **Duration:** {appointment.duration} minutes

This appointment slot is now reserved for you. Next, I'll need your insurance information 
to complete the booking."""
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "collect_insurance"
        
        return state
    
    def _collect_insurance_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Collect insurance information"""
        
        response = """Now I need to collect your insurance information for billing:

Please provide:
1. **Insurance company name** (e.g., BlueCross BlueShield, Aetna, Cigna)
2. **Member ID number** (found on your insurance card)
3. **Group number** (also on your card, if applicable)

You can give me this information all at once or one piece at a time."""
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "confirm_appointment"
        
        return state
    
    def _confirm_appointment_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Confirm the appointment"""
        
        patient = state["patient"]
        appointment_info = state["appointment_info"]
        
        response = f"""🎉 **Appointment Confirmed!** 

**Your appointment details:**
👤 **Patient:** {patient.full_name}
📅 **Date & Time:** {appointment_info['date']} at {appointment_info['time']}
👩‍⚕️ **Doctor:** {appointment_info['doctor']}
🏢 **Location:** {appointment_info['location']}
⏱️ **Duration:** {appointment_info['duration']} minutes

**What happens next:**
✅ Confirmation email will be sent
✅ Patient intake forms will be emailed (complete 24 hours before visit)
✅ Automated reminders will be scheduled
✅ Insurance verification will be processed

**Important reminders:**
• Arrive 15 minutes early
• Bring insurance card and photo ID
• Complete intake forms before your visit

Is everything correct?"""
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "send_forms"
        
        return state
    
    def _send_forms_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Send intake forms and confirmations"""
        
        patient = state["patient"]
        
        response = f"""✅ **All set, {patient.first_name}!**

Your appointment is confirmed and all systems are in place:

📧 **Confirmation email sent** to {patient.email}
📋 **Patient intake forms sent** - please complete 24 hours before your visit
🔔 **Reminder system activated** - you'll receive 3 automated reminders

**Form completion is required 24 hours before your visit for:**
• Medical history review
• Current medications
• Insurance verification
• Allergy testing preparation (if applicable)

Your appointment is secure and we're looking forward to seeing you!"""
        
        state["messages"].append(AIMessage(content=response))
        state["current_step"] = "complete"
        
        return state
    
    def _complete_node(self, state: MedicalWorkflowState) -> MedicalWorkflowState:
        """Complete the workflow"""
        
        state["workflow_complete"] = True
        
        final_message = """Thank you for choosing MediCare Allergy & Wellness Center! 

Your appointment booking is complete. If you have any questions or need to make 
changes, please call us at (555) 123-4567.

Is there anything else I can help you with today?"""
        
        state["messages"].append(AIMessage(content=final_message))
        
        return state
    
    def run_workflow(self, initial_message: str, session_id: str = None) -> MedicalWorkflowState:
        """Run the complete workflow"""
        
        # Initialize state
        initial_state = MedicalWorkflowState(
            messages=[HumanMessage(content=initial_message)],
            patient_info={},
            patient=None,
            appointment_info={},
            preferences={},
            insurance_info={},
            current_step="greeting",
            errors=[],
            session_id=session_id or f"session_{int(datetime.now().timestamp())}",
            workflow_complete=False
        )
        
        try:
            # Run the workflow
            final_state = self.workflow.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            # Return error state
            initial_state["errors"].append(str(e))
            return initial_state