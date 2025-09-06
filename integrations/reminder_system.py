"""
Complete 3-Tier Reminder System Implementation
RagaAI Assignment - Automated reminder processing with response tracking
"""
import os
import logging
import sqlite3
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ReminderSystem:
    def __init__(self, db_path: str = "medical_scheduling.db"):
        self.db_path = db_path
        # ... (rest of __init__ is the same)
        self.is_running = False
        self.worker_thread = None
        self._init_services()
        self.init_reminder_tables()
        logger.info("Complete Reminder System initialized")


    def _get_db_conn(self):
        """Creates a new database connection for the current thread."""
        return sqlite3.connect(self.db_path, timeout=10) # Added timeout to help with locking

    # ... (all other methods should be modified to use self._get_db_conn())
    # Fix in integrations/reminder_system.py - schedule_appointment_reminders function
# Replace the entire function:

    def schedule_appointment_reminders(self, appointment_id: str, appointment_datetime: datetime, 
                                patient_email: str, patient_phone: str = None) -> bool:
        """Schedules the 3-tier reminders with proper status tracking."""
        conn = self._get_db_conn()
        try:
            with conn:
                cursor = conn.cursor()
                
                # Create 3 reminders with proper datetime formatting
                reminders_to_create = [
                    {
                        'type': 'initial', 
                        'scheduled_time': (appointment_datetime - timedelta(days=7)).isoformat(),
                        'description': '7-day reminder'
                    },
                    {
                        'type': 'form_check', 
                        'scheduled_time': (appointment_datetime - timedelta(hours=24)).isoformat(),
                        'description': '24-hour form check'
                    },
                    {
                        'type': 'final_confirmation', 
                        'scheduled_time': (appointment_datetime - timedelta(hours=2)).isoformat(),
                        'description': '2-hour final confirmation'
                    }
                ]
                
                for reminder in reminders_to_create:
                    cursor.execute("""
                    INSERT INTO reminders (
                        appointment_id, reminder_type, scheduled_time, 
                        patient_email, patient_phone, sent, email_sent, sms_sent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        appointment_id, 
                        reminder['type'], 
                        reminder['scheduled_time'],
                        patient_email, 
                        patient_phone or '', 
                        0,  # sent = False
                        0,  # email_sent = False  
                        0   # sms_sent = False
                    ))
                
                # Verify the insertions
                cursor.execute("SELECT COUNT(*) FROM reminders WHERE appointment_id = ?", (appointment_id,))
                count = cursor.fetchone()[0]
                
                logger.info(f"✅ Successfully inserted {count} reminders for appointment {appointment_id}")
                return count == 3
                
        except sqlite3.Error as e:
            logger.error(f"❌ DB Error scheduling reminders for {appointment_id}: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    # ... (Ensure all other database-interacting methods follow this pattern)
    def _init_services(self):
        """Initialize email and SMS services"""
        try:
            from integrations.email_service import EmailService
            from integrations.sms_service import SMSService
            
            self.email_service = EmailService()
            self.sms_service = SMSService()
            
            logger.info("✅ Email and SMS services initialized")
        except ImportError as e:
            logger.error(f"❌ Failed to import services: {e}")
            self.email_service = None
            self.sms_service = None

    def init_reminder_tables(self):
        """Initialize all reminder-related database tables"""
        conn = self._get_db_conn()
        try:
            with conn:
                cursor = conn.cursor()
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
                    response_data TEXT,
                    attempts INTEGER DEFAULT 0,
                    last_attempt TIMESTAMP,
                    patient_email TEXT,
                    patient_phone TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
        except sqlite3.Error as e:
            logger.error(f"Error initializing reminder tables: {e}")
        finally:
            if conn:
                conn.close()

# Global instance management
_reminder_system_instance = None

def get_reminder_system() -> ReminderSystem:
    """Get the global reminder system instance"""
    global _reminder_system_instance
    if _reminder_system_instance is None:
        _reminder_system_instance = ReminderSystem()
    return _reminder_system_instance