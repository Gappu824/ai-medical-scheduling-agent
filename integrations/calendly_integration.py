"""
Database-Backed Calendly Integration for Persistent State
RagaAI Assignment - Solves booking failures by using a reliable DB backend.
"""

import logging
import sqlite3
from datetime import datetime
from typing import Dict, Optional

try:
    from database.database import DatabaseManager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from database.database import DatabaseManager

logger = logging.getLogger(__name__)

class CalendlyIntegration:
    """
    A mock Calendly integration that uses the application's SQLite database
    for persistent storage of appointment availability.
    """
    
    def __init__(self):
        # We don't need a full DB manager instance here, just the path to the DB.
        self.db_path = "medical_scheduling.db"
        logger.info("Database-backed CalendlyIntegration initialized.")

    def _get_db_conn(self):
        """Creates a new connection for this module's use."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_earliest_slot(self, doctor: str, start_after: datetime) -> Optional[datetime]:
        """Finds the earliest available slot for a doctor from the database."""
        conn = self._get_db_conn()
        try:
            query = """
                SELECT datetime FROM doctor_schedules
                WHERE doctor_name = ? AND datetime > ? AND available = 1
                ORDER BY datetime ASC
                LIMIT 1
            """
            row = conn.execute(query, (doctor, start_after.isoformat())).fetchone()
            if row:
                return datetime.fromisoformat(row['datetime'])
            return None
        finally:
            conn.close()

    def book_appointment(self, doctor: str, appointment_time: datetime, patient_data: Dict, duration: int) -> Optional[Dict]:
        """
        Books an appointment by marking a slot as unavailable in the database.
        This operation is atomic and persistent.
        """
        conn = self._get_db_conn()
        iso_time = appointment_time.isoformat()
        
        try:
            with conn:
                # Check if the slot exists and is available
                cursor = conn.execute(
                    "SELECT id FROM doctor_schedules WHERE doctor_name = ? AND datetime = ? AND available = 1",
                    (doctor, iso_time)
                )
                slot = cursor.fetchone()
                
                if not slot:
                    logger.warning(f"Attempted to book an unavailable/non-existent slot for {doctor} at {iso_time}")
                    return None # Slot is not available or doesn't exist

                # Mark the slot as unavailable
                conn.execute(
                    "UPDATE doctor_schedules SET available = 0 WHERE id = ?",
                    (slot['id'],)
                )

            booking_id = f"APT-DB-{int(datetime.now().timestamp())}"
            logger.info(f"Successfully booked appointment {booking_id} in the database for {doctor} at {iso_time}")
            
            return {
                "booking_id": booking_id,
                "status": "confirmed",
                "doctor": doctor,
                "appointment_time": appointment_time.isoformat(),
                "patient_name": patient_data.get('full_name'),
                "location": "Main Clinic" # Assuming a default location
            }
        except sqlite3.Error as e:
            logger.error(f"Database error during booking: {e}")
            return None
        finally:
            conn.close()