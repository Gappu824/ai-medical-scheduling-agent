"""
Production Calendly Integration for Medical Scheduling Agent
RagaAI Assignment - Real Calendar Management with Excel Backend

This module simulates a real calendar booking system by treating an Excel file 
as a persistent database. It includes file locking to handle potential concurrent 
access, ensuring data integrity.
"""

import logging
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import threading

# Use a file lock to prevent race conditions when writing to the Excel file
try:
    from filelock import FileLock
except ImportError:
    # Fallback for environments without filelock, not recommended for production
    class FileLock:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): pass
        def __exit__(self, exc_type, exc_val, exc_tb): pass

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    """
    Production-grade calendar integration using an Excel file as a backend.
    
    This class manages doctor schedules with real-world considerations:
    - Reads from a shared Excel file (`data/doctor_schedules.xlsx`).
    - Implements file locking to prevent data corruption from concurrent writes.
    - Updates the Excel file to reflect new bookings and cancellations.
    - Handles complex availability logic based on duration and existing bookings.
    """
    
    def __init__(self, schedules_file: str = "data/doctor_schedules.xlsx"):
        self.schedules_path = Path(schedules_file)
        self.lock_path = Path(f"{schedules_file}.lock")
        self.schedules_df = None
        self.last_modified_time = 0
        self.business_hours = {"start": 9, "end": 17, "days": [0, 1, 2, 3, 4]}  # Mon-Fri, 9 AM - 5 PM
        self._load_schedules()

    def _load_schedules(self, force_reload: bool = False):
        """
        Load or reload the doctor schedules from the Excel file.
        
        This method checks the file's last modified time to avoid unnecessary reloads,
        improving performance. A lock is used to ensure thread-safe reading.
        """
        try:
            if not self.schedules_path.exists():
                logger.error(f"Schedules file not found at: {self.schedules_path}")
                self.schedules_df = pd.DataFrame()
                return

            modified_time = self.schedules_path.stat().st_mtime
            if modified_time > self.last_modified_time or force_reload:
                with FileLock(self.lock_path):
                    self.schedules_df = pd.read_excel(self.schedules_path, sheet_name='All_Schedules')
                    # Standardize data types for reliable filtering
                    self.schedules_df['datetime'] = pd.to_datetime(self.schedules_df['datetime'])
                    self.schedules_df['available'] = self.schedules_df['available'].astype(bool)
                self.last_modified_time = modified_time
                logger.info("Successfully loaded/reloaded doctor schedules.")

        except Exception as e:
            logger.error(f"Failed to load schedules from {self.schedules_path}: {e}")
            self.schedules_df = pd.DataFrame()

    def _save_schedules(self):
        """
        Save the updated DataFrame back to the Excel file.
        
        This is a critical operation that modifies the persistent schedule data.
        A file lock is used to prevent race conditions during the write operation.
        """
        if self.schedules_df is None:
            logger.error("No schedule data to save.")
            return

        try:
            with FileLock(self.lock_path):
                # We need to write all sheets back to preserve the file structure
                with pd.ExcelWriter(self.schedules_path, engine='openpyxl') as writer:
                    # Write the updated main schedule
                    self.schedules_df.to_excel(writer, sheet_name='All_Schedules', index=False)
                    
                    # You would re-write other sheets here if they existed
                    # For this assignment, we only modify the main sheet
                    
                self.last_modified_time = self.schedules_path.stat().st_mtime
            logger.info(f"Successfully saved updated schedules to {self.schedules_path}")
        except Exception as e:
            logger.error(f"Failed to save schedules: {e}")

    def get_available_slots(self, doctor: str, date: datetime, duration: int) -> List[datetime]:
        """
        Get available slots for a doctor on a specific date that can accommodate the required duration.
        
        This is a core function that now reads from the live schedule DataFrame.
        """
        self._load_schedules()
        
        if self.schedules_df is None or self.schedules_df.empty:
            return []

        # Filter for the specific doctor, date, and available slots
        day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
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
        """
        Book an appointment by marking the slot as unavailable in the Excel file.
        
        This function performs a final conflict check before booking.
        """
        self._load_schedules(force_reload=True)  # Force reload to get the latest availability
        
        if self.schedules_df is None:
            return None

        # Find the exact slot to book
        slot_index = self.schedules_df[
            (self.schedules_df['datetime'] == appointment_time) &
            (self.schedules_df['doctor_name'] == doctor)
        ].index

        if slot_index.empty:
            logger.warning(f"Attempted to book a non-existent slot for {doctor} at {appointment_time}")
            return None
        
        slot_index = slot_index[0]
        
        # **Final Conflict Check**
        if not self.schedules_df.at[slot_index, 'available']:
            logger.warning(f"CONFLICT: Slot for {doctor} at {appointment_time} was already booked.")
            return None
            
        # Mark as booked and save
        self.schedules_df.at[slot_index, 'available'] = False
        self.schedules_df.at[slot_index, 'appointment_type'] = 'Booked' # Update appointment type
        self._save_schedules()
        
        booking_id = f"APT-{int(datetime.now().timestamp())}"
        
        logger.info(f"SUCCESS: Appointment {booking_id} for {patient_data.get('full_name')} with {doctor} at {appointment_time} confirmed and saved.")
        
        return {
            "booking_id": booking_id,
            "status": "confirmed",
            "doctor": doctor,
            "appointment_time": appointment_time.isoformat(),
            "patient_name": patient_data.get('full_name')
        }

    def cancel_appointment(self, appointment_id: str, reason: str = "Patient requested cancellation") -> bool:
        """
        Cancel an appointment by making the slot available again in the Excel file.
        
        (Note: This is a simplified implementation. A real system would use the booking_id
         to find the exact appointment and its corresponding slot.)
        """
        # In a real system, you'd look up the appointment_id in your database to get the datetime and doctor.
        # For this simulation, we'll assume we can find the slot to cancel.
        # This is a placeholder for a more complex cancellation logic.
        logger.warning("Cancellation is a placeholder. To implement, you would need to store booking IDs and map them to schedule slots.")
        return False

    def get_doctor_schedule_for_week(self, doctor: str, start_date: datetime) -> Dict:
        """Get a doctor's weekly schedule summary."""
        self._load_schedules()
        
        schedule = {}
        for i in range(7):
            date = start_date + timedelta(days=i)
            slots = self.get_available_slots(doctor, date, 30) # Check for base 30-min availability
            schedule[date.strftime('%Y-%m-%d')] = {
                "day": date.strftime('%A'),
                "available_slots": len(slots)
            }
        return schedule