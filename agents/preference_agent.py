"""
Interactive Preference Matching Agent
RagaAI Assignment - Enhanced Patient Preference Collection
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.tools import tool

from database.database import DatabaseManager
from database.models import AVAILABLE_DOCTORS, CLINIC_LOCATIONS, Patient, PatientType

logger = logging.getLogger(__name__)

@tool
def get_patient_history_tool(patient_id: str) -> str:
    """Get patient's appointment history for preference matching"""
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT doctor, location, appointment_datetime, status
        FROM appointments 
        WHERE patient_id = ? 
        ORDER BY appointment_datetime DESC 
        LIMIT 5
        """, (patient_id,))
        
        history = cursor.fetchall()
        conn.close()
        
        if history:
            formatted_history = []
            for record in history:
                formatted_history.append({
                    "doctor": record[0],
                    "location": record[1],
                    "date": record[2],
                    "status": record[3]
                })
            
            return {
                "has_history": True,
                "appointments": formatted_history,
                "last_doctor": history[0][0],
                "last_location": history[0][1],
                "total_visits": len(history)
            }
        else:
            return {"has_history": False, "message": "No previous appointment history found"}
            
    except Exception as e:
        logger.error(f"Error getting patient history: {e}")
        return {"has_history": False, "error": str(e)}

@tool  
def check_doctor_availability_tool(doctor_name: str, preferred_dates: List[str]) -> str:
    """Check specific doctor's availability for preferred dates"""
    try:
        from integrations.calendly_integration import CalendlyIntegration
        
        calendly = CalendlyIntegration()
        availability_results = []
        
        for date_str in preferred_dates:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            slots = calendly.get_available_slots(date_obj, doctor_name, 30)  # Check 30-min slots
            
            availability_results.append({
                "date": date_str,
                "available_slots": [slot.strftime("%H:%M") for slot in slots],
                "total_slots": len(slots)
            })
        
        return {
            "doctor": doctor_name,
            "availability": availability_results,
            "has_availability": any(result["total_slots"] > 0 for result in availability_results)
        }
        
    except Exception as e:
        logger.error(f"Error checking doctor availability: {e}")
        return {"error": str(e)}

class PreferenceMatchingAgent:
    """Agent for interactive preference collection and matching"""
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro",
            temperature=0.2,  # Slightly higher for more conversational responses
            max_tokens=1024
        )
        self.db = DatabaseManager()
    
    def collect_preferences_for_returning_patient(self, patient: Patient) -> str:
        """Collect preferences for returning patients with history context"""
        
        # Get patient's appointment history
        history_result = get_patient_history_tool.invoke(patient.id)
        
        if history_result.get("has_history"):
            # Patient has history - ask about continuing with same preferences
            last_doctor = history_result["last_doctor"]
            last_location = history_result["last_location"]
            total_visits = history_result["total_visits"]
            
            prompt = ChatPromptTemplate.from_template("""
            You are helping a returning patient schedule their appointment. They have a history with our clinic.
            
            Patient: {patient_name}
            Previous appointments: {total_visits}
            Last doctor: {last_doctor}
            Last location: {last_location}
            
            Create a warm, personalized message that:
            1. Welcomes them back personally
            2. Mentions their previous doctor and location
            3. Asks if they'd like to continue with the same doctor/location OR try someone new
            4. If they want the same doctor, ask for preferred dates/times
            5. If they want to try someone new, present the other available options
            6. Keep it conversational and friendly
            
            Available doctors if they want to switch:
            - Dr. Sarah Johnson (Allergist) - Main Clinic, Downtown Branch
            - Dr. Michael Chen (Pulmonologist) - Main Clinic, Suburban Office  
            - Dr. Emily Rodriguez (Immunologist) - All locations
            
            Available locations:
            - Main Clinic - Healthcare Boulevard
            - Downtown Branch - Medical Center
            - Suburban Office - Wellness Plaza
            """)
            
            response = self.llm.invoke(prompt.format(
                patient_name=patient.first_name,
                total_visits=total_visits,
                last_doctor=last_doctor,
                last_location=last_location
            ))
            
            return response.content
            
        else:
            # Returning patient but no history found
            return self.collect_preferences_for_new_patient(patient, is_returning=True)
    
    def collect_preferences_for_new_patient(self, patient: Patient, is_returning: bool = False) -> str:
        """Collect preferences for new patients with detailed options"""
        
        prompt = ChatPromptTemplate.from_template("""
        You are helping a {patient_type} patient schedule their first appointment with us.
        
        Patient: {patient_name}
        Appointment duration: {duration} minutes
        
        Create a helpful, informative message that:
        1. Welcomes them to our clinic
        2. Explains we have multiple doctors and locations for their convenience
        3. Asks them to choose their preferences by presenting options clearly
        4. For each doctor, explain their specialty and what conditions they treat
        5. For each location, mention the address and any special features
        6. Ask for their preferred days of the week and time preferences
        7. Keep it professional but warm and welcoming
        
        Available doctors and their specialties:
        
        🔬 **Dr. Sarah Johnson - Allergist**
        - Specializes in: Food allergies, environmental allergies, asthma, eczema
        - Locations: Main Clinic, Downtown Branch
        - Best for: Allergy testing, immunotherapy, chronic allergy management
        
        🫁 **Dr. Michael Chen - Pulmonologist** 
        - Specializes in: Asthma, COPD, lung function testing, breathing disorders
        - Locations: Main Clinic, Suburban Office
        - Best for: Respiratory issues, chronic cough, shortness of breath
        
        🧬 **Dr. Emily Rodriguez - Immunologist**
        - Specializes in: Immune system disorders, autoimmune conditions, complex allergies
        - Locations: All three locations (most flexible)
        - Best for: Complex immune issues, medication allergies, rare conditions
        
        Available locations:
        
        🏢 **Main Clinic - Healthcare Boulevard**
        - Address: 456 Healthcare Boulevard, Suite 300
        - Features: Full diagnostic lab, allergy testing suite, parking available
        
        🏙️ **Downtown Branch - Medical Center** 
        - Address: 789 Medical Center Drive, Suite 150
        - Features: Convenient downtown location, public transport access
        
        🏘️ **Suburban Office - Wellness Plaza**
        - Address: 321 Wellness Plaza, Suite 200  
        - Features: Quiet suburban setting, easy parking, family-friendly
        
        Ask them:
        1. Which doctor/specialty interests them most based on their needs?
        2. Which location is most convenient for them?
        3. What days of the week work best? (Mon-Fri)
        4. What time of day do they prefer? (Morning 9-12, Afternoon 1-5)
        5. Any dates they definitely want to avoid?
        
        Make it feel like a conversation, not a form to fill out.
        """)
        
        patient_type = "returning" if is_returning else "new"
        duration = 30 if is_returning else 60
        
        response = self.llm.invoke(prompt.format(
            patient_type=patient_type,
            patient_name=patient.first_name,
            duration=duration
        ))
        
        return response.content
    
    def process_preference_response(self, patient: Patient, user_response: str) -> str:
        """Process user's preference response and provide next steps"""
        
        extraction_prompt = ChatPromptTemplate.from_template("""
        Extract appointment preferences from this patient response: "{response}"
        
        Return a JSON object with these fields (use null if not mentioned):
        - preferred_doctor: string (exact doctor name if mentioned)
        - preferred_location: string (location name if mentioned)  
        - preferred_days: array of strings (e.g., ["Monday", "Tuesday"])
        - preferred_times: string (e.g., "morning", "afternoon", "specific time")
        - special_requests: string (any specific needs or constraints)
        - same_as_before: boolean (if they want same doctor/location as last time)
        
        Example: {{"preferred_doctor": "Dr. Sarah Johnson", "preferred_location": "Main Clinic", "preferred_days": ["Monday", "Wednesday"], "preferred_times": "morning", "special_requests": null, "same_as_before": false}}
        
        Only return the JSON object, no other text.
        """)
        
        extraction_response = self.llm.invoke(extraction_prompt.format(response=user_response))
        
        try:
            import json
            preferences = json.loads(extraction_response.content)
            
            # Generate response based on extracted preferences
            return self.generate_availability_response(patient, preferences)
            
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return self.ask_for_clarification(user_response)
    
    def generate_availability_response(self, patient: Patient, preferences: Dict) -> str:
        """Generate response with availability based on preferences"""
        
        preferred_doctor = preferences.get("preferred_doctor")
        preferred_location = preferences.get("preferred_location")
        same_as_before = preferences.get("same_as_before", False)
        
        if same_as_before:
            # Get their last doctor/location from history
            history = get_patient_history_tool.invoke(patient.id)
            if history.get("has_history"):
                preferred_doctor = history["last_doctor"]
                preferred_location = history["last_location"]
        
        # Check availability for their preferences
        if preferred_doctor:
            # Get next 7 days for availability check
            check_dates = []
            for i in range(1, 8):  # Next 7 days
                date = datetime.now().date() + timedelta(days=i)
                if date.weekday() < 5:  # Monday-Friday only
                    check_dates.append(date.strftime("%Y-%m-%d"))
            
            availability = check_doctor_availability_tool.invoke({
                "doctor_name": preferred_doctor,
                "preferred_dates": check_dates
            })
            
            if availability.get("has_availability"):
                return self.format_availability_response(
                    patient, preferred_doctor, preferred_location, availability, preferences
                )
            else:
                return self.offer_alternatives(patient, preferred_doctor, preferences)
        else:
            # Ask them to be more specific about doctor choice
            return self.ask_for_doctor_clarification(preferences)
    
    def format_availability_response(self, patient: Patient, doctor: str, location: str, availability: Dict, preferences: Dict) -> str:
        """Format the availability response with specific time slots"""
        
        prompt = ChatPromptTemplate.from_template("""
        Great! Based on the patient's preferences, create a response that:
        
        Patient: {patient_name}
        Preferred doctor: {doctor}
        Preferred location: {location}
        Patient preferences: {preferences}
        
        Available slots: {availability}
        
        Create a response that:
        1. Confirms their choice of doctor and location
        2. Shows specific available time slots in a clear, easy-to-read format
        3. Highlights slots that match their time preferences (morning/afternoon)
        4. Asks them to select their preferred appointment time
        5. Mentions what to expect at the appointment (duration, what to bring)
        6. Keeps it conversational and helpful
        
        Format the time slots nicely, like:
        **Tuesday, September 10th**
        • 9:00 AM ✅ Available
        • 10:30 AM ✅ Available
        
        Make it easy for them to just say "I'll take Tuesday at 9 AM" or similar.
        """)
        
        response = self.llm.invoke(prompt.format(
            patient_name=patient.first_name,
            doctor=doctor,
            location=location, 
            preferences=json.dumps(preferences, indent=2),
            availability=json.dumps(availability, indent=2)
        ))
        
        return response.content
    
    def offer_alternatives(self, patient: Patient, preferred_doctor: str, preferences: Dict) -> str:
        """Offer alternative doctors/times when preferred choice isn't available"""
        
        prompt = ChatPromptTemplate.from_template("""
        The patient's preferred doctor ({preferred_doctor}) doesn't have availability that matches their preferences.
        
        Patient: {patient_name}
        Preferences: {preferences}
        
        Create a helpful response that:
        1. Explains that their preferred doctor is currently booked
        2. Offers specific alternatives:
           - Same doctor but different times/dates
           - Different doctor in same specialty at preferred times
           - Different location with their preferred doctor
        3. Asks what they'd prefer to do
        4. Keeps it positive and solution-focused
        5. Mentions they can also join a waitlist for their preferred slot
        
        Available alternatives:
        - Dr. Sarah Johnson (Allergist) - Main Clinic, Downtown Branch
        - Dr. Michael Chen (Pulmonologist) - Main Clinic, Suburban Office  
        - Dr. Emily Rodriguez (Immunologist) - All locations
        
        Make it feel like we're working together to find the best solution for them.
        """)
        
        response = self.llm.invoke(prompt.format(
            preferred_doctor=preferred_doctor,
            patient_name=patient.first_name,
            preferences=json.dumps(preferences, indent=2)
        ))
        
        return response.content
    
    def ask_for_doctor_clarification(self, preferences: Dict) -> str:
        """Ask for clarification when doctor preference isn't clear"""
        
        prompt = ChatPromptTemplate.from_template("""
        The patient hasn't clearly specified which doctor they'd like to see.
        
        Their response mentioned: {preferences}
        
        Create a helpful clarification message that:
        1. Acknowledges what they did tell us (location, timing, etc.)
        2. Explains we need to know which doctor/specialty they need
        3. Briefly re-presents the doctor options with their specialties
        4. Asks them to choose based on their specific health needs
        5. Keeps it friendly and not repetitive
        
        Doctors:
        - Dr. Sarah Johnson (Allergist) - for allergies, asthma, eczema
        - Dr. Michael Chen (Pulmonologist) - for breathing issues, lung problems
        - Dr. Emily Rodriguez (Immunologist) - for immune system and complex allergies
        
        Make it easy for them to just say "I need the allergist" or "breathing problems" etc.
        """)
        
        response = self.llm.invoke(prompt.format(
            preferences=json.dumps(preferences, indent=2)
        ))
        
        return response.content
    
    def ask_for_clarification(self, user_response: str) -> str:
        """Ask for clarification when the response isn't clear"""
        
        prompt = ChatPromptTemplate.from_template("""
        The patient said: "{user_response}"
        
        This response isn't clear enough to proceed with scheduling. Create a friendly message that:
        1. Acknowledges their response
        2. Explains what specific information we still need
        3. Asks clear, specific questions to get the missing details
        4. Provides examples of how they can respond
        5. Keeps it conversational, not like a form
        
        We need to know:
        - Which doctor/specialty they need
        - Which location works best for them
        - Their preferred days/times
        
        Make it easy for them to give us what we need.
        """)
        
        response = self.llm.invoke(prompt.format(user_response=user_response))
        return response.content

    def handle_final_time_selection(self, patient: Patient, selected_slot: str, doctor: str, location: str) -> str:
        """Handle final appointment time selection and confirmation"""
        
        prompt = ChatPromptTemplate.from_template("""
        Perfect! The patient has selected their appointment time.
        
        Patient: {patient_name}
        Selected: {selected_slot}
        Doctor: {doctor}
        Location: {location}
        
        Create a confirmation message that:
        1. Confirms all the appointment details clearly
        2. Explains what happens next (insurance info, forms, etc.)
        3. Mentions what to bring to the appointment
        4. Gives them a chance to change anything if needed
        5. Sounds professional but warm
        
        Include important details like:
        - Arrive 15 minutes early
        - Bring insurance card and ID
        - Intake forms will be emailed
        - Medication instructions (if allergy testing)
        
        Make it feel like everything is taken care of and they can relax.
        """)
        
        response = self.llm.invoke(prompt.format(
            patient_name=patient.first_name,
            selected_slot=selected_slot,
            doctor=doctor,
            location=location
        ))
        
        return response.content