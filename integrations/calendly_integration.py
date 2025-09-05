"""
Calendly Integration for Medical Scheduling Agent
RagaAI Assignment - Mock Calendar Management
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    """Mock Calendly integration for demo purposes - reads from Excel schedules"""
    
    def __init__(self):
        self.schedules_file = Path("data/doctor_schedules.xlsx")
        self.business_hours = {
            "start": 9,  # 9 AM
            "end": 17,   # 5 PM
            "days": [0, 1, 2, 3, 4]  # Monday to Friday (0=Monday)
        }
        
    def get_available_slots(self, doctor: str, date: datetime, duration: int = 60) -> List[datetime]:
        """Get available appointment slots for a specific doctor and date"""
        try:
            available_slots = []
            
            # Check if it's a business day
            if date.weekday() not in self.business_hours["days"]:
                logger.info(f"No slots available - {date.strftime('%A')} is not a business day")
                return available_slots
            
            # Load doctor schedules from Excel
            if self.schedules_file.exists():
                schedules_df = pd.read_excel(self.schedules_file, sheet_name="All_Schedules")
                
                # Filter for specific doctor and date
                doctor_schedule = schedules_df[
                    (schedules_df["Doctor"].str.contains(doctor, case=False, na=False)) &
                    (schedules_df["Date"] == date.strftime("%Y-%m-%d"))
                ]
                
                if not doctor_schedule.empty:
                    # Use actual schedule from Excel
                    for _, slot in doctor_schedule.iterrows():
                        if slot["Available"] == "Yes":
                            slot_time = datetime.strptime(f"{date.strftime('%Y-%m-%d')} {slot['Time']}", "%Y-%m-%d %H:%M")
                            available_slots.append(slot_time)
                else:
                    # Generate mock slots if no Excel data
                    available_slots = self._generate_mock_slots(date, doctor, duration)
            else:
                # Generate mock slots if no Excel file
                available_slots = self._generate_mock_slots(date, doctor, duration)
            
            logger.info(f"Found {len(available_slots)} available slots for {doctor} on {date.strftime('%Y-%m-%d')}")
            return available_slots[:6]  # Return max 6 slots for UI
            
        except Exception as e:
            logger.error(f"Error getting available slots: {e}")
            return self._generate_mock_slots(date, doctor, duration)
    
    def _generate_mock_slots(self, date: datetime, doctor: str, duration: int) -> List[datetime]:
        """Generate mock available slots for demo purposes"""
        
        available_slots = []
        
        # Generate slots from 9 AM to 5 PM with 30-minute intervals
        current_time = datetime.combine(date, datetime.min.time().replace(hour=self.business_hours["start"]))
        end_time = datetime.combine(date, datetime.min.time().replace(hour=self.business_hours["end"]))
        
        slot_interval = timedelta(minutes=30)
        slot_duration = timedelta(minutes=duration)
        
        while current_time + slot_duration <= end_time:
            # Simulate 75% availability (skip some slots randomly)
            import random
            if random.random() < 0.75:
                available_slots.append(current_time)
            current_time += slot_interval
        
        # Ensure we have at least 3 slots for demo
        if len(available_slots) < 3:
            available_slots = [
                datetime.combine(date, datetime.min.time().replace(hour=9, minute=0)),
                datetime.combine(date, datetime.min.time().replace(hour=10, minute=30)),
                datetime.combine(date, datetime.min.time().replace(hour=14, minute=0))
            ]
        
        return available_slots[:6]  # Return max 6 slots
    
    def book_appointment(self, doctor: str, appointment_time: datetime, patient_data: Dict, duration: int = 60) -> Dict:
        """Book an appointment slot (mock implementation)"""
        try:
            # In real implementation, this would call Calendly API
            booking_data = {
                "booking_id": f"apt_{int(appointment_time.timestamp())}",
                "doctor": doctor,
                "patient_name": f"{patient_data.get('first_name', '')} {patient_data.get('last_name', '')}",
                "appointment_time": appointment_time.isoformat(),
                "duration": duration,
                "status": "confirmed",
                "location": patient_data.get('location', 'Main Clinic'),
                "booking_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Appointment booked: {booking_data['booking_id']}")
            return booking_data
            
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            return {"error": str(e)}
    
    def get_doctor_availability(self, doctor: str, start_date: datetime, days: int = 7) -> Dict:
        """Get doctor availability for the next N days"""
        try:
            availability = {}
            current_date = start_date
            
            for day in range(days):
                if current_date.weekday() in self.business_hours["days"]:
                    slots = self.get_available_slots(doctor, current_date)
                    availability[current_date.strftime("%Y-%m-%d")] = {
                        "date": current_date.strftime("%A, %B %d, %Y"),
                        "slots": [slot.strftime("%I:%M %p") for slot in slots],
                        "available_count": len(slots)
                    }
                current_date += timedelta(days=1)
            
            return availability
            
        except Exception as e:
            logger.error(f"Error getting doctor availability: {e}")
            return {}
    
    def get_all_doctors(self) -> List[Dict]:
        """Get list of all available doctors"""
        try:
            doctors = [
                {
                    "id": "dr_johnson",
                    "name": "Dr. Sarah Johnson",
                    "specialty": "Allergist/Immunologist",
                    "location": "Main Clinic",
                    "description": "Specializes in food allergies, environmental allergens, and asthma management"
                },
                {
                    "id": "dr_chen",
                    "name": "Dr. Michael Chen",
                    "specialty": "Pulmonologist", 
                    "location": "Downtown Clinic",
                    "description": "Expert in respiratory conditions, sleep disorders, and complex lung diseases"
                },
                {
                    "id": "dr_rodriguez",
                    "name": "Dr. Maria Rodriguez",
                    "specialty": "Pediatric Allergist",
                    "location": "Family Center",
                    "description": "Pediatric allergy specialist focusing on childhood asthma and food allergies"
                }
            ]
            
            return doctors
            
        except Exception as e:
            logger.error(f"Error getting doctors list: {e}")
            return []
    
    def check_appointment_conflicts(self, doctor: str, appointment_time: datetime, duration: int = 60) -> bool:
        """Check if appointment time conflicts with existing bookings"""
        try:
            # Mock conflict checking - in real implementation, check against calendar API
            # For demo, simulate occasional conflicts
            import random
            has_conflict = random.random() < 0.1  # 10% chance of conflict
            
            if has_conflict:
                logger.warning(f"Conflict detected for {doctor} at {appointment_time}")
            
            return has_conflict
            
        except Exception as e:
            logger.error(f"Error checking conflicts: {e}")
            return False
    
    def get_next_available_slot(self, doctor: str, preferred_time: datetime, duration: int = 60) -> Optional[datetime]:
        """Find next available slot after preferred time"""
        try:
            # Check next 14 days for availability
            for days_ahead in range(14):
                check_date = preferred_time + timedelta(days=days_ahead)
                available_slots = self.get_available_slots(doctor, check_date, duration)
                
                if available_slots:
                    # Return first slot that's after preferred time
                    for slot in available_slots:
                        if slot >= preferred_time:
                            return slot
            
            logger.warning(f"No available slots found for {doctor} in next 14 days")
            return None
            
        except Exception as e:
            logger.error(f"Error finding next available slot: {e}")
            return None