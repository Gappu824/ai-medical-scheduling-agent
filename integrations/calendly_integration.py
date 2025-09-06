"""
FIXED: Database-Backed Calendly Integration - Solves DateTime Format Issues
RagaAI Assignment - Consistent datetime handling for reliable booking
"""

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Optional, List

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
    Fixed Calendly integration that handles datetime formatting consistently
    and uses the application's SQLite database for persistent state.
    """
    
    def __init__(self):
        self.db_path = "medical_scheduling.db"
        self._ensure_doctor_schedules_table()
        self._populate_initial_schedule_if_empty()
        logger.info("Fixed CalendlyIntegration initialized with consistent datetime handling.")

    def _get_db_conn(self):
        """Creates a new connection for this module's use."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_doctor_schedules_table(self):
        """Ensure the doctor_schedules table exists with proper schema"""
        conn = self._get_db_conn()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS doctor_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_name TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT 1,
                    location TEXT DEFAULT 'Main Clinic',
                    UNIQUE(doctor_name, datetime)
                )
                """)
                # Create index for faster lookups
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_doctor_schedules_lookup 
                ON doctor_schedules (doctor_name, datetime, available)
                """)
        finally:
            conn.close()

    def _populate_initial_schedule_if_empty(self):
        """Populate initial schedule if the table is empty"""
        conn = self._get_db_conn()
        try:
            cursor = conn.cursor()
            
            # Check if we have any schedules
            cursor.execute("SELECT COUNT(*) FROM doctor_schedules")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("Populating initial doctor schedules...")
                self._create_initial_schedules(cursor)
                conn.commit()
                logger.info("Initial schedules created successfully")
        finally:
            conn.close()

    def _create_initial_schedules(self, cursor):
        """Create initial schedule for all doctors"""
        doctors = ["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez"]
        
        # Create schedules for next 30 days
        base_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        schedules = []
        for day_offset in range(30):
            current_date = base_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Create slots from 9 AM to 5 PM, every 30 minutes
            for hour in range(9, 17):
                for minute in [0, 30]:
                    slot_time = current_date.replace(hour=hour, minute=minute)
                    
                    # Skip lunch hour (12-1 PM)
                    if slot_time.hour == 12:
                        continue
                    
                    for doctor in doctors:
                        # Use consistent ISO format without microseconds
                        iso_time = slot_time.strftime("%Y-%m-%dT%H:%M:%S")
                        schedules.append((doctor, iso_time, 1, 'Main Clinic'))
        
        # Insert all schedules
        cursor.executemany(
            "INSERT OR IGNORE INTO doctor_schedules (doctor_name, datetime, available, location) VALUES (?, ?, ?, ?)",
            schedules
        )

    def _normalize_datetime(self, dt) -> str:
        """
        CRITICAL FIX: Normalize datetime to consistent format without microseconds
        This prevents the booking mismatch issue
        """
        if isinstance(dt, str):
            try:
                # Parse the string and reformat consistently
                parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return parsed.strftime("%Y-%m-%dT%H:%M:%S")
            except ValueError:
                return dt
        elif isinstance(dt, datetime):
            # Always format without microseconds
            return dt.strftime("%Y-%m-%dT%H:%M:%S")
        else:
            return str(dt)

    def get_earliest_slot(self, doctor: str, start_after: datetime) -> Optional[datetime]:
        """Finds the earliest available slot for a doctor from the database."""
        conn = self._get_db_conn()
        try:
            # Normalize the start_after datetime
            start_after_str = self._normalize_datetime(start_after)
            
            query = """
                SELECT datetime FROM doctor_schedules
                WHERE doctor_name = ? AND datetime > ? AND available = 1
                ORDER BY datetime ASC
                LIMIT 1
            """
            row = conn.execute(query, (doctor, start_after_str)).fetchone()
            if row:
                return datetime.fromisoformat(row['datetime'])
            return None
        finally:
            conn.close()

    def get_available_slots(self, date_obj, doctor: str = None, duration: int = 30) -> List[datetime]:
        """
        Get available slots for a specific date, optionally filtered by doctor
        FIXED: Consistent datetime handling throughout
        """
        conn = self._get_db_conn()
        try:
            # Handle different input types for date_obj
            if isinstance(date_obj, datetime):
                target_date = date_obj.date()
            else:
                target_date = date_obj
            
            # Create start and end of day in consistent format
            day_start = datetime.combine(target_date, datetime.min.time())
            day_end = day_start + timedelta(days=1)
            
            day_start_str = self._normalize_datetime(day_start)
            day_end_str = self._normalize_datetime(day_end)
            
            if doctor:
                query = """
                    SELECT datetime FROM doctor_schedules
                    WHERE doctor_name = ? AND datetime >= ? AND datetime < ? AND available = 1
                    ORDER BY datetime ASC
                """
                params = (doctor, day_start_str, day_end_str)
            else:
                query = """
                    SELECT datetime FROM doctor_schedules
                    WHERE datetime >= ? AND datetime < ? AND available = 1
                    ORDER BY datetime ASC
                """
                params = (day_start_str, day_end_str)
            
            rows = conn.execute(query, params).fetchall()
            return [datetime.fromisoformat(row['datetime']) for row in rows]
            
        finally:
            conn.close()

    def book_appointment(self, doctor: str, appointment_time: datetime, patient_data: Dict, duration: int) -> Optional[Dict]:
        """
        CRITICAL FIX: Books an appointment with consistent datetime formatting
        This solves the "unavailable/non-existent slot" error
        """
        conn = self._get_db_conn()
        
        # CRITICAL: Use the same normalization for both lookup and booking
        normalized_time = self._normalize_datetime(appointment_time)
        
        try:
            with conn:
                cursor = conn.cursor()
                
                # Check if the slot exists and is available using EXACT same format
                cursor.execute(
                    "SELECT id FROM doctor_schedules WHERE doctor_name = ? AND datetime = ? AND available = 1",
                    (doctor, normalized_time)
                )
                slot = cursor.fetchone()
                
                if not slot:
                    logger.warning(f"No available slot found for {doctor} at {normalized_time}")
                    logger.warning(f"Original appointment_time: {appointment_time}")
                    logger.warning(f"Normalized time: {normalized_time}")
                    
                    # Debug: Show what slots ARE available for this doctor around this time
                    debug_start = (appointment_time - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
                    debug_end = (appointment_time + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%S")
                    
                    cursor.execute(
                        "SELECT datetime, available FROM doctor_schedules WHERE doctor_name = ? AND datetime BETWEEN ? AND ? ORDER BY datetime",
                        (doctor, debug_start, debug_end)
                    )
                    nearby_slots = cursor.fetchall()
                    logger.warning(f"Nearby slots for {doctor}: {[(row['datetime'], row['available']) for row in nearby_slots]}")
                    
                    return None

                # Mark the slot as unavailable
                cursor.execute(
                    "UPDATE doctor_schedules SET available = 0 WHERE id = ?",
                    (slot['id'],)
                )

            booking_id = f"APT-{int(datetime.now().timestamp())}"
            logger.info(f"✅ Successfully booked appointment {booking_id} for {doctor} at {normalized_time}")
            
            return {
                "booking_id": booking_id,
                "status": "confirmed",
                "doctor": doctor,
                "appointment_time": normalized_time,  # Return the normalized format
                "patient_name": patient_data.get('full_name'),
                "location": "Main Clinic"
            }
            
        except sqlite3.Error as e:
            logger.error(f"❌ Database error during booking: {e}")
            return None
        finally:
            conn.close()

    def get_doctor_availability_summary(self, doctor: str, days_ahead: int = 7) -> Dict:
        """Get a summary of doctor's availability for the next N days"""
        conn = self._get_db_conn()
        try:
            start_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            end_time = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%dT%H:%M:%S")
            
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    DATE(datetime) as date,
                    COUNT(*) as total_slots,
                    SUM(CASE WHEN available = 1 THEN 1 ELSE 0 END) as available_slots
                FROM doctor_schedules 
                WHERE doctor_name = ? AND datetime BETWEEN ? AND ?
                GROUP BY DATE(datetime)
                ORDER BY date
            """, (doctor, start_time, end_time))
            
            results = cursor.fetchall()
            return {
                row['date']: {
                    'total': row['total_slots'],
                    'available': row['available_slots']
                }
                for row in results
            }
        finally:
            conn.close()

    def release_appointment_slot(self, doctor: str, appointment_time: datetime) -> bool:
        """Release a booked slot back to availability (for cancellations)"""
        conn = self._get_db_conn()
        try:
            normalized_time = self._normalize_datetime(appointment_time)
            
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE doctor_schedules SET available = 1 WHERE doctor_name = ? AND datetime = ?",
                    (doctor, normalized_time)
                )
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Released appointment slot for {doctor} at {normalized_time}")
                    return True
                else:
                    logger.warning(f"⚠️ No slot found to release for {doctor} at {normalized_time}")
                    return False
        except sqlite3.Error as e:
            logger.error(f"❌ Error releasing slot: {e}")
            return False
        finally:
            conn.close()