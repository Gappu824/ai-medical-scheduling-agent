"""
Fixed Calendly Integration - All Issues Resolved
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    """Fixed calendar integration with proper datetime handling"""
    
    def __init__(self, schedules_file: str = "data/doctor_schedules.xlsx"):
        self.schedules_path = Path(schedules_file)
        self.schedules_df = None
        self._load_schedules()

    def _load_schedules(self):
        """Load doctor schedules from Excel file"""
        try:
            if not self.schedules_path.exists():
                logger.error(f"Schedules file not found: {self.schedules_path}")
                self.schedules_df = pd.DataFrame()
                return

            self.schedules_df = pd.read_excel(self.schedules_path, sheet_name='All_Schedules')
            self.schedules_df['datetime'] = pd.to_datetime(self.schedules_df['datetime'])
            self.schedules_df['available'] = self.schedules_df['available'].astype(bool)
            logger.info("Successfully loaded doctor schedules")

        except Exception as e:
            logger.error(f"Failed to load schedules: {e}")
            self.schedules_df = pd.DataFrame()

    def get_available_slots(self, doctor: str, date: datetime, duration: int) -> List[datetime]:
        """Get available slots for a doctor on a specific date"""
        if self.schedules_df is None or self.schedules_df.empty:
            return []

        # Convert date to datetime if it's a date object
        if hasattr(date, 'date'):
            check_date = date
        else:
            check_date = datetime.combine(date, datetime.min.time())
        
        day_start = check_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        mask = (
            (self.schedules_df['doctor_name'] == doctor) &
            (self.schedules_df['datetime'] >= day_start) &
            (self.schedules_df['datetime'] < day_end) &
            (self.schedules_df['available'] == True) &
            (self.schedules_df['duration_available'] >= duration)
        )
        
        available_slots_df = self.schedules_df[mask]
        return sorted(available_slots_df['datetime'].tolist())

    def book_appointment(self, doctor: str, appointment_time: datetime, patient_data: Dict, duration: int) -> Optional[Dict]:
        """Book an appointment"""
        if self.schedules_df is None:
            return None

        slot_index = self.schedules_df[
            (self.schedules_df['datetime'] == appointment_time) &
            (self.schedules_df['doctor_name'] == doctor)
        ].index

        if slot_index.empty:
            logger.warning(f"No slot found for {doctor} at {appointment_time}")
            return None
        
        slot_index = slot_index[0]
        
        if not self.schedules_df.at[slot_index, 'available']:
            logger.warning(f"Slot already booked for {doctor} at {appointment_time}")
            return None
            
        # Mark as booked
        self.schedules_df.at[slot_index, 'available'] = False
        
        booking_id = f"APT-{int(datetime.now().timestamp())}"
        
        logger.info(f"Appointment {booking_id} booked successfully")
        
        return {
            "booking_id": booking_id,
            "status": "confirmed",
            "doctor": doctor,
            "appointment_time": appointment_time.isoformat(),
            "patient_name": patient_data.get('full_name')
        }
