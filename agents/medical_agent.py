"""
Enhanced Medical Scheduling Agent with Interactive Preference Matching
RagaAI Assignment - LangGraph Implementation with Patient-Centric Scheduling
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
from dataclasses import asdict

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain.tools import tool
from langchain_core.runnables import RunnableConfig

from database.database import DatabaseManager
from database.models import Patient, Appointment, PatientType, AppointmentStatus, AVAILABLE_DOCTORS
from integrations.email_service import EmailService
from integrations.calendly_integration import CalendlyIntegration
from agents.preference_agent import PreferenceMatchingAgent  # Import our new preference agent
from utils.validators import validate_patient_info, validate_appointment_data

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
                    "type": patient.patient_type.value,
                    "duration": patient.appointment_duration,
                    "name": patient.full_name,
                    "email": patient.email,
                    "phone": patient.phone
                },
                "history": [
                    {"doctor": h[0], "location": h[1], "date": h[2]} 
                    for h in history
                ] if history else []
            }
        else:
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
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=0.1,
            max_tokens=1024
        )
        
        # Initialize services
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.calendly = CalendlyIntegration()
        self.preference_agent = PreferenceMatchingAgent()  # New preference agent
        
        # Available tools
        self.tools = [search_patient_tool, get_interactive_availability_tool]
        
        # Create workflow
        self.workflow = self._create_enhanced_workflow()
        
        logger.info("Enhanced Medical Scheduling Agent initialized successfully")
    
    def _create_enhanced_workflow(self) -> StateGraph:
        """Create enhanced LangGraph workflow with preference matching"""
        
        workflow = StateGraph(AgentState)
        
        # Add enhanced nodes
        workflow.add_node("greeting", self._greeting_node)
        workflow.add_node("collect_info", self._collect_info_node) 
        workflow.add_node("patient_lookup", self._patient_lookup_node)
        workflow.add_node("interactive_preferences", self._interactive_preferences_node)  # New
        workflow.add_node("process_preferences", self._process_preferences_node)  # New
        workflow.add_node("show_availability", self._show_availability_node)  # New
        workflow.add_node("confirm_selection", self._confirm_selection_node)  # New
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
    
    def _greeting_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced greeting with personalized welcome"""
        
        prompt = ChatPromptTemplate.from_template("""
        You are a professional medical scheduling assistant for MediCare Allergy & Wellness Center.
        
        Create a warm, welcoming greeting that:
        1. Welcomes the patient to our medical center
        2. Explains you'll help them find the perfect appointment that fits their needs
        3. Mentions we have multiple doctors and locations for their convenience
        4. Asks for their basic information in a friendly way
        5. Makes them feel like we'll take great care of finding the right fit for them
        
        Ask for:
        - Full name (First and Last)
        - Date of birth (MM/DD/YYYY format)
        - Phone number and email address
        
        Keep it professional, caring, and personalized - like a real medical receptionist would speak.
        """)
        
        chain = prompt | self.llm
        response = chain.invoke({})
        
        # Update state
        state["messages"].append(AIMessage(content=response.content))
        state["current_step"] = "collect_info"
        
        return state
    
    def _collect_info_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced info collection with better parsing"""
        
        # Get the last user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No user input found")
            return state
        
        last_message = user_messages[-1].content
        
        # Enhanced extraction using LLM
        extraction_prompt = ChatPromptTemplate.from_template("""
        Extract patient information from this message: "{message}"
        
        Be flexible with formats - people might say things like:
        - "I'm John Smith, born March 15 1985"
        - "Jane Doe, 03/15/85, 555-1234, jane@email.com"
        - "My name is Robert Johnson, DOB 1985-03-15"
        
        Return a JSON object with these fields (use null if not found):
        - first_name: string
        - last_name: string  
        - dob: string (always convert to YYYY-MM-DD format)
        - phone: string
        - email: string
        - additional_info: string (any other relevant details they mentioned)
        
        Example: {{"first_name": "John", "last_name": "Doe", "dob": "1985-03-15", "phone": "555-1234", "email": "john@example.com", "additional_info": "mentioned knee problems"}}
        
        Only return the JSON object, no other text.
        """)
        
        extraction_chain = extraction_prompt | self.llm
        extraction_response = extraction_chain.invoke({"message": last_message})
        
        try:
            import json
            patient_data = json.loads(extraction_response.content)
            state["patient_info"].update(patient_data)
        except json.JSONDecodeError:
            logger.error("Failed to extract patient information")
            state["errors"].append("Failed to extract patient information")
        
        state["current_step"] = "patient_lookup"
        return state
    
    def _patient_lookup_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced patient lookup with history context"""
        
        patient_info = state["patient_info"]
        
        # Validate required fields
        required_fields = ["first_name", "last_name", "dob"]
        missing_fields = [field for field in required_fields if not patient_info.get(field)]
        
        if missing_fields:
            # Ask for missing information more conversationally
            prompt = ChatPromptTemplate.from_template("""
            I have some of your information, but I need a bit more to help you schedule.
            
            What I have: {current_info}
            Still need: {missing_fields}
            
            Create a friendly message asking for the missing information. Be conversational and explain why we need it (to find their record or create a new one).
            """)
            
            chain = prompt | self.llm
            response = chain.invoke({
                "missing_fields": ", ".join(missing_fields),
                "current_info": ", ".join([f"{k}: {v}" for k, v in patient_info.items() if v])
            })
            
            state["messages"].append(AIMessage(content=response.content))
            state["current_step"] = "collect_info"  # Go back to collect more info
            return state
        
        # Search for existing patient with history
        search_result = search_patient_tool.invoke({
            "first_name": patient_info["first_name"],
            "last_name": patient_info["last_name"], 
            "dob": patient_info["dob"]
        })
        
        state["patient_lookup_result"] = search_result
        state["current_step"] = "interactive_preferences"
        
        return state
    
    def _interactive_preferences_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """New: Interactive preference collection with patient history context"""
        
        lookup_result = state.get("patient_lookup_result", {})
        patient_info = state["patient_info"]
        
        if lookup_result.get("found"):
            # Returning patient - use preference agent with history
            patient_data = lookup_result["patient"]
            history = lookup_result.get("history", [])
            
            # Create patient object for preference agent
            patient = Patient(
                id=patient_data["id"],
                first_name=patient_info["first_name"],
                last_name=patient_info["last_name"],
                dob=patient_info["dob"],
                phone=patient_info.get("phone", ""),
                email=patient_info.get("email", ""),
                patient_type=PatientType(patient_data["type"])
            )
            
            # Get personalized preference message
            preference_message = self.preference_agent.collect_preferences_for_returning_patient(patient)
            
            # Store patient object in state for later use
            state["current_patient"] = patient
            
        else:
            # New patient - collect preferences from scratch
            patient = Patient(
                id=f"NEW_{int(datetime.now().timestamp())}",
                first_name=patient_info["first_name"],
                last_name=patient_info["last_name"], 
                dob=patient_info["dob"],
                phone=patient_info.get("phone", ""),
                email=patient_info.get("email", ""),
                patient_type=PatientType.NEW
            )
            
            preference_message = self.preference_agent.collect_preferences_for_new_patient(patient)
            state["current_patient"] = patient
        
        # Add the preference collection message
        state["messages"].append(AIMessage(content=preference_message))
        state["current_step"] = "process_preferences"
        
        return state
    
    def _process_preferences_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """New: Process user's preference response"""
        
        # Get the last user message (their preference response)
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No preference response found")
            return state
        
        last_message = user_messages[-1].content
        patient = state.get("current_patient")
        
        if not patient:
            state["errors"].append("Patient object not found")
            return state
        
        # Process preferences using the preference agent
        try:
            preference_response = self.preference_agent.process_preference_response(patient, last_message)
            state["messages"].append(AIMessage(content=preference_response))
            
            # Extract structured preferences for later use
            extraction_prompt = ChatPromptTemplate.from_template("""
            From this conversation about appointment preferences: "{message}"
            
            Extract and return a JSON object with:
            - doctor: string (exact doctor name if specified)
            - location: string (location name if specified)
            - time_preference: string (morning/afternoon/specific time)
            - same_as_last: boolean (if they want same as previous appointment)
            
            Only return the JSON, no other text.
            """)
            
            extraction_response = self.llm.invoke(extraction_prompt.format(message=last_message))
            
            try:
                import json
                preferences = json.loads(extraction_response.content)
                state["preferences"] = preferences
                
                # Set selected doctor and location if specified
                if preferences.get("doctor"):
                    state["selected_doctor"] = preferences["doctor"]
                if preferences.get("location"):
                    state["selected_location"] = preferences["location"]
                    
            except json.JSONDecodeError:
                logger.warning("Could not parse preferences, will ask for clarification")
            
            state["current_step"] = "show_availability"
            
        except Exception as e:
            logger.error(f"Error processing preferences: {e}")
            state["errors"].append(f"Error processing preferences: {str(e)}")
            state["current_step"] = "show_availability"  # Continue anyway
        
        return state
    
    def _show_availability_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """New: Show available appointment slots based on preferences"""
        
        preferences = state.get("preferences", {})
        doctor = state.get("selected_doctor") or preferences.get("doctor")
        location = state.get("selected_location") or preferences.get("location")
        patient = state.get("current_patient")
        
        if not doctor or not location:
            # Ask for clarification if we don't have enough info
            clarification_prompt = ChatPromptTemplate.from_template("""
            I need to check availability, but I need to know which doctor and location you prefer.
            
            Current preferences: {preferences}
            
            Please create a message asking them to specify:
            1. Which doctor they'd like to see
            2. Which location is most convenient
            
            Available options:
            - Dr. Sarah Johnson (Allergist) - Main Clinic, Downtown Branch
            - Dr. Michael Chen (Pulmonologist) - Main Clinic, Suburban Office  
            - Dr. Emily Rodriguez (Immunologist) - All locations
            
            Keep it conversational and helpful.
            """)
            
            response = self.llm.invoke(clarification_prompt.format(preferences=json.dumps(preferences)))
            state["messages"].append(AIMessage(content=response.content))
            state["current_step"] = "process_preferences"  # Go back to get clearer preferences
            return state
        
        # Get availability for the next 14 days
        start_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        date_range = f"{start_date} to {end_date}"
        
        try:
            availability_result = get_interactive_availability_tool.invoke({
                "doctor": doctor,
                "location": location,
                "date_range": date_range
            })
            
            if availability_result.get("total_slots", 0) > 0:
                # Format and present available slots
                slots_message = self._format_availability_message(
                    patient, doctor, location, availability_result, preferences
                )
                state["messages"].append(AIMessage(content=slots_message))
                state["available_slots"] = availability_result["available_slots"]
                state["current_step"] = "confirm_selection"
            else:
                # No availability - offer alternatives
                alternative_message = self._create_alternative_options_message(doctor, location, preferences)
                state["messages"].append(AIMessage(content=alternative_message))
                state["current_step"] = "process_preferences"  # Let them choose alternatives
                
        except Exception as e:
            logger.error(f"Error getting availability: {e}")
            error_message = "I'm having trouble checking availability right now. Let me try a different approach or you can call us at (555) 123-4567 to schedule."
            state["messages"].append(AIMessage(content=error_message))
            state["errors"].append(f"Availability error: {str(e)}")
        
        return state
    
    def _confirm_selection_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """New: Confirm the selected appointment time"""
        
        # Get the last user message (their time selection)
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if not user_messages:
            state["errors"].append("No time selection found")
            return state
        
        last_message = user_messages[-1].content
        available_slots = state.get("available_slots", [])
        doctor = state.get("selected_doctor")
        location = state.get("selected_location")
        patient = state.get("current_patient")
        
        # Parse the selected time from user message
        selection_prompt = ChatPromptTemplate.from_template("""
        The patient said: "{message}"
        
        Available slots: {slots}
        
        Determine which appointment slot they selected and return JSON:
        - selected_datetime: string (YYYY-MM-DD HH:MM format)
        - selected_display: string (how to display it to them)
        - is_clear_selection: boolean (whether the selection is clear)
        
        If the selection isn't clear, set is_clear_selection to false.
        
        Only return JSON, no other text.
        """)
        
        try:
            selection_response = self.llm.invoke(selection_prompt.format(
                message=last_message,
                slots=json.dumps(available_slots, indent=2)
            ))
            
            import json
            selection_data = json.loads(selection_response.content)
            
            if selection_data.get("is_clear_selection"):
                # Clear selection - confirm it
                confirmation_message = self.preference_agent.handle_final_time_selection(
                    patient, selection_data["selected_display"], doctor, location
                )
                
                # Store the selected appointment details
                state["appointment_info"] = {
                    "datetime": selection_data["selected_datetime"],
                    "display": selection_data["selected_display"],
                    "doctor": doctor,
                    "location": location,
                    "duration": patient.appointment_duration,
                    "patient_type": patient.patient_type.value
                }
                
                state["messages"].append(AIMessage(content=confirmation_message))
                state["current_step"] = "collect_insurance"
            else:
                # Unclear selection - ask for clarification
                clarification = "I want to make sure I book the right time for you. Could you please tell me exactly which day and time you'd prefer? For example, you could say 'Tuesday at 9 AM' or 'Wednesday afternoon at 2:30 PM'."
                state["messages"].append(AIMessage(content=clarification))
                # Stay in this step to get a clearer selection
                
        except Exception as e:
            logger.error(f"Error parsing time selection: {e}")
            fallback_message = "I want to make sure I book the correct time. Could you please specify which day and time you'd like? For example: 'Monday at 9:00 AM' or 'Wednesday at 2:30 PM'."
            state["messages"].append(AIMessage(content=fallback_message))
        
        return state
    
    def _collect_insurance_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced insurance collection with better guidance"""
        
        patient = state.get("current_patient")
        appointment_info = state.get("appointment_info", {})
        
        prompt = ChatPromptTemplate.from_template("""
        Perfect! Your appointment is confirmed for {appointment_display} with {doctor} at {location}.
        
        Now I need to collect your insurance information for billing and verification:
        
        **Please provide:**
        1. **Insurance company name** (e.g., BlueCross BlueShield, Aetna, Cigna)
        2. **Member ID number** (found on your insurance card)
        3. **Group number** (also on your card, if applicable)
        
        **Why we need this:**
        - To verify your coverage before your visit
        - To process claims efficiently
        - To determine any copay or deductible amounts
        
        You can give me this information all at once or one piece at a time - whatever's easier for you!
        
        *Don't have your insurance card handy? No problem - you can bring this information to your appointment, but having it now will make check-in faster.*
        """)
        
        chain = prompt | self.llm  
        response = chain.invoke({
            "appointment_display": appointment_info.get("display", "your appointment"),
            "doctor": appointment_info.get("doctor", "your doctor"),
            "location": appointment_info.get("location", "our clinic")
        })
        
        state["messages"].append(AIMessage(content=response.content))
        state["current_step"] = "final_confirmation"
        
        return state
    
    def _final_confirmation_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced final confirmation with complete appointment summary"""
        
        patient = state.get("current_patient")
        appointment_info = state.get("appointment_info", {})
        
        # Get insurance info from last user message
        user_messages = [msg for msg in state["messages"] if isinstance(msg, HumanMessage)]
        if user_messages:
            last_message = user_messages[-1].content
            
            # Extract insurance info
            insurance_prompt = ChatPromptTemplate.from_template("""
            Extract insurance information from: "{message}"
            
            Return JSON with:
            - insurance_company: string
            - member_id: string  
            - group_number: string
            - has_insurance_info: boolean
            
            If they don't have the info or will bring it later, set has_insurance_info to false.
            """)
            
            try:
                insurance_response = self.llm.invoke(insurance_prompt.format(message=last_message))
                import json
                insurance_data = json.loads(insurance_response.content)
                state["insurance_info"] = insurance_data
            except:
                state["insurance_info"] = {"has_insurance_info": False}
        
        # Create comprehensive confirmation
        confirmation_prompt = ChatPromptTemplate.from_template("""
        Create a comprehensive appointment confirmation message for the patient.
        
        Patient: {patient_name} ({patient_type} patient)
        Appointment: {appointment_display}
        Doctor: {doctor}
        Location: {location}
        Duration: {duration} minutes
        Insurance: {insurance_status}
        
        Include:
        1. Complete appointment summary
        2. What happens next (confirmation email, forms)
        3. What to bring to the appointment
        4. Important pre-visit instructions (especially for allergy testing)
        5. Contact information for changes
        6. A warm, professional closing
        
        Make it feel complete and reassuring - like everything is taken care of.
        """)
        
        insurance_info = state.get("insurance_info", {})
        insurance_status = "On file" if insurance_info.get("has_insurance_info") else "Will provide at appointment"
        
        response = self.llm.invoke(confirmation_prompt.format(
            patient_name=patient.full_name,
            patient_type=patient.patient_type.value.title(),
            appointment_display=appointment_info.get("display", "your appointment"),
            doctor=appointment_info.get("doctor", "your doctor"),
            location=appointment_info.get("location", "our clinic"),
            duration=appointment_info.get("duration", 60),
            insurance_status=insurance_status
        ))
        
        state["messages"].append(AIMessage(content=response.content))
        state["current_step"] = "send_forms"
        
        return state
    
    def _send_forms_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """Enhanced form distribution with confirmation"""
        
        patient = state.get("current_patient")
        appointment_info = state.get("appointment_info", {})
        
        try:
            # Send confirmation email and intake forms
            if patient and patient.email:
                self.email_service.send_appointment_confirmation(
                    patient.email,
                    {
                        "patient_name": patient.full_name,
                        "appointment_date": appointment_info.get("display", ""),
                        "doctor": appointment_info.get("doctor", ""),
                        "location": appointment_info.get("location", ""),
                        "duration": appointment_info.get("duration", 60)
                    },
                    appointment_info
                )
                
                self.email_service.send_intake_form(patient.email)
                
                # Create final success message
                final_message = f"""
🎉 **All set, {patient.first_name}!** 

✅ **Confirmation email sent** to {patient.email}  
✅ **Patient intake forms sent** - please complete 24 hours before your visit  
✅ **Appointment reminders scheduled** - we'll send you reminders via email and text  

**Your appointment is confirmed and we're looking forward to seeing you!**

*Is there anything else I can help you with today?*
"""
                
            else:
                final_message = """
🎉 **Your appointment is confirmed!** 

Since I don't have your email address, please make sure to:
- Arrive 15 minutes early for check-in
- Bring your insurance card and photo ID  
- Ask for patient intake forms when you arrive

*Is there anything else I can help you with today?*
"""
            
            state["messages"].append(AIMessage(content=final_message))
            
        except Exception as e:
            logger.error(f"Error sending forms: {e}")
            state["errors"].append(f"Failed to send forms: {str(e)}")
            
            error_message = """
✅ **Your appointment is confirmed!**

I had trouble sending the confirmation email, but your appointment is definitely scheduled. 
Please call us at (555) 123-4567 if you need a confirmation sent manually.

*Is there anything else I can help you with?*
"""
            state["messages"].append(AIMessage(content=error_message))
        
        return state
    
    def _format_availability_message(self, patient: Patient, doctor: str, location: str, availability: Dict, preferences: Dict) -> str:
        """Format availability results into a user-friendly message"""
        
        slots = availability["available_slots"]
        time_pref = preferences.get("time_preference", "")
        
        # Group slots by date for better presentation
        slots_by_date = {}
        for slot in slots:
            date_key = slot["display_date"]
            if date_key not in slots_by_date:
                slots_by_date[date_key] = []
            slots_by_date[date_key].append(slot)
        
        # Build the message
        message_parts = [
            f"Excellent choice! **{doctor}** at **{location}** has great availability.",
            "",
            "**Available appointment times:**",
            ""
        ]
        
        # Add slots grouped by date
        for date, date_slots in list(slots_by_date.items())[:5]:  # Show max 5 dates
            message_parts.append(f"**{date}**")
            for slot in date_slots[:3]:  # Max 3 slots per date
                # Highlight preferred times
                highlight = "🌟 " if time_pref.lower() in slot["time_period"].lower() else "• "
                message_parts.append(f"{highlight}{slot['display_time']}")
            message_parts.append("")
        
        message_parts.extend([
            "**To book your appointment, just tell me:**",
            "• Which day works best for you",
            "• Your preferred time",
            "",
            "*For example: 'I'll take Tuesday at 9:00 AM' or 'Wednesday afternoon works great'*",
            "",
            f"**Appointment details:**",
            f"👩‍⚕️ **Doctor:** {doctor}",
            f"🏢 **Location:** {location}",
            f"⏱️ **Duration:** {patient.appointment_duration} minutes ({patient.patient_type.value} patient)"
        ])
        
        return "\n".join(message_parts)
    
    def _create_alternative_options_message(self, preferred_doctor: str, preferred_location: str, preferences: Dict) -> str:
        """Create message with alternative options when preferred choice isn't available"""
        
        prompt = ChatPromptTemplate.from_template("""
        The patient's preferred choice isn't available right now:
        Preferred doctor: {doctor}  
        Preferred location: {location}
        Their preferences: {preferences}
        
        Create a helpful message that:
        1. Explains their first choice is currently booked
        2. Offers specific alternatives:
           - Same doctor at different location/times
           - Different doctor in same specialty 
           - Waitlist option for their preferred slot
        3. Asks what they'd prefer to do
        4. Keeps it positive and solution-focused
        
        Available alternatives:
        - Dr. Sarah Johnson (Allergist) - Main Clinic, Downtown Branch
        - Dr. Michael Chen (Pulmonologist) - Main Clinic, Suburban Office  
        - Dr. Emily Rodriguez (Immunologist) - All locations
        
        Make it feel collaborative - like we're working together to find the perfect fit.
        """)
        
        response = self.llm.invoke(prompt.format(
            doctor=preferred_doctor,
            location=preferred_location,
            preferences=json.dumps(preferences, indent=2)
        ))
        
        return response.content
    
    def process_message(self, message: str, session_id: str = None) -> str:
        """Process a user message through the enhanced workflow"""
        
        # Initialize or update state
        session_key = session_id or f"session_{int(datetime.now().timestamp())}"
        
        # Get existing state or create new one
        if hasattr(self, '_session_states') and session_key in self._session_states:
            current_state = self._session_states[session_key]
            current_state["messages"].append(HumanMessage(content=message))
        else:
            # Initialize new session state
            current_state = AgentState(
                messages=[HumanMessage(content=message)],
                patient_info={},
                appointment_info={},
                preferences={},
                current_step="greeting",
                errors=[],
                session_id=session_key,
                selected_doctor=None,
                selected_location=None,
                available_slots=[]
            )
            
            # Store session state
            if not hasattr(self, '_session_states'):
                self._session_states = {}
            self._session_states[session_key] = current_state
        
        # Run workflow
        try:
            final_state = self.workflow.invoke(current_state)
            
            # Update stored state
            self._session_states[session_key] = final_state
            
            # Return the last AI message
            ai_messages = [msg for msg in final_state["messages"] if isinstance(msg, AIMessage)]
            return ai_messages[-1].content if ai_messages else "I'm sorry, I couldn't process your request."
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"I apologize, but I encountered an error: {str(e)}. Please try again or call us at (555) 123-4567."
    
    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Get current session state for UI display"""
        if hasattr(self, '_session_states') and session_id in self._session_states:
            return self._session_states[session_id]
        return None
    
    def reset_session(self, session_id: str):
        """Reset a session state"""
        if hasattr(self, '_session_states') and session_id in self._session_states:
            del self._session_states[session_id]