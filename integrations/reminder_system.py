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
import schedule
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class ReminderSystem:
    """Complete 3-tier reminder system with automation"""
    
    def __init__(self, db_path: str = "medical_scheduling.db"):
        self.db_path = db_path
        self.is_running = False
        self.check_interval = 60  # Check every minute
        self.worker_thread = None
        
        # Initialize services
        self._init_services()
        
        # Initialize database tables
        self.init_reminder_tables()
        
        logger.info("Complete Reminder System initialized")
    
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
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Main reminders table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id)
            )
            """)
            
            # Reminder responses table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminder_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL,
                reminder_id INTEGER,
                response_type TEXT NOT NULL,
                response_channel TEXT NOT NULL,
                response_content TEXT,
                action_taken TEXT,
                processed BOOLEAN DEFAULT FALSE,
                received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id),
                FOREIGN KEY (reminder_id) REFERENCES reminders (id)
            )
            """)
            
            # Reminder log for debugging and analytics
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminder_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                success BOOLEAN DEFAULT FALSE,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Performance indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON reminders (scheduled_time, sent)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_appointment ON reminders (appointment_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_responses_appointment ON reminder_responses (appointment_id)")
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Reminder database tables initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing reminder tables: {e}")
    
    def schedule_appointment_reminders(self, appointment_id: str, appointment_datetime: datetime, 
                                     patient_email: str, patient_phone: str = None) -> bool:
        """
        THE MAIN INTEGRATION POINT: Schedule 3-tier reminders after booking
        This is called from the medical agent after successful appointment booking
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate reminder times based on assignment requirements
            apt_datetime = appointment_datetime
            
            reminders_to_create = [
                {
                    'type': 'initial',
                    'scheduled_time': apt_datetime - timedelta(days=7),
                    'description': '7-day initial reminder (regular)'
                },
                {
                    'type': 'form_check', 
                    'scheduled_time': apt_datetime - timedelta(hours=24),
                    'description': '24-hour form check (with actions: forms filled? visit confirmed?)'
                },
                {
                    'type': 'final_confirmation',
                    'scheduled_time': apt_datetime - timedelta(hours=2),
                    'description': '2-hour final confirmation (with cancellation reason if needed)'
                }
            ]
            
            created_count = 0
            current_time = datetime.now()
            
            for reminder in reminders_to_create:
                # Schedule reminder (even if time has passed - we'll process immediately)
                cursor.execute("""
                INSERT INTO reminders 
                (appointment_id, reminder_type, scheduled_time, patient_email, patient_phone)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    appointment_id,
                    reminder['type'],
                    reminder['scheduled_time'].isoformat(),
                    patient_email,
                    patient_phone
                ))
                
                reminder_id = cursor.lastrowid
                
                # Log the reminder creation
                cursor.execute("""
                INSERT INTO reminder_log
                (appointment_id, reminder_type, action, details, success)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    appointment_id,
                    reminder['type'],
                    'scheduled',
                    json.dumps({
                        'reminder_id': reminder_id,
                        'scheduled_for': reminder['scheduled_time'].isoformat(),
                        'description': reminder['description'],
                        'patient_email': patient_email,
                        'patient_phone': patient_phone
                    }),
                    True
                ))
                
                created_count += 1
                logger.info(f"📅 Scheduled {reminder['description']} for appointment {appointment_id}")
                
                # If reminder time has already passed, process it immediately
                if reminder['scheduled_time'] <= current_time:
                    logger.info(f"⏰ Reminder due immediately, processing now...")
                    self._process_single_reminder_immediate(
                        reminder_id, appointment_id, reminder['type'],
                        patient_email, patient_phone, apt_datetime
                    )
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Successfully scheduled {created_count} reminders for appointment {appointment_id}")
            
            # Start the reminder service if not running
            if not self.is_running:
                self.start_reminder_service()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error scheduling reminders for {appointment_id}: {e}")
            return False
    
    def _process_single_reminder_immediate(self, reminder_id: int, appointment_id: str, 
                                         reminder_type: str, patient_email: str, 
                                         patient_phone: str, appointment_datetime: datetime):
        """Process a single reminder immediately"""
        try:
            # Get appointment and patient details
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT a.doctor, a.location, p.first_name, p.last_name
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.id = ?
            """, (appointment_id,))
            
            result = cursor.fetchone()
            
            if not result:
                logger.error(f"Could not find appointment details for {appointment_id}")
                return
            
            doctor, location, first_name, last_name = result
            
            # Prepare data for email/SMS
            patient_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': patient_email,
                'phone': patient_phone
            }
            
            appointment_data = {
                'id': appointment_id,
                'doctor': doctor,
                'location': location,
                'date': appointment_datetime.strftime('%A, %B %d'),
                'time': appointment_datetime.strftime('%I:%M %p'),
                'duration': 60  # Default
            }
            
            # Send email and SMS based on reminder type
            email_sent = False
            sms_sent = False
            
            if patient_email and self.email_service:
                if reminder_type == "initial":
                    email_sent = self.email_service.send_initial_reminder(patient_data, appointment_data)
                elif reminder_type == "form_check":
                    email_sent = self.email_service.send_form_check_reminder(patient_data, appointment_data)
                elif reminder_type == "final_confirmation":
                    email_sent = self.email_service.send_final_confirmation(patient_data, appointment_data)
            
            if patient_phone and self.sms_service:
                if reminder_type == "initial":
                    sms_sent = self.sms_service.send_initial_reminder_sms(patient_data, appointment_data)
                elif reminder_type == "form_check":
                    sms_sent = self.sms_service.send_form_check_sms(patient_data, appointment_data)
                elif reminder_type == "final_confirmation":
                    sms_sent = self.sms_service.send_final_confirmation_sms(patient_data, appointment_data)
            
            # Update reminder status
            cursor.execute("""
            UPDATE reminders 
            SET sent = TRUE, email_sent = ?, sms_sent = ?, 
                attempts = attempts + 1, last_attempt = ?
            WHERE id = ?
            """, (email_sent, sms_sent, datetime.now().isoformat(), reminder_id))
            
            # Log the action
            cursor.execute("""
            INSERT INTO reminder_log
            (appointment_id, reminder_type, action, details, success)
            VALUES (?, ?, ?, ?, ?)
            """, (
                appointment_id,
                reminder_type,
                'sent',
                json.dumps({
                    'email_sent': email_sent,
                    'sms_sent': sms_sent,
                    'timestamp': datetime.now().isoformat()
                }),
                email_sent or sms_sent
            ))
            
            conn.commit()
            conn.close()
            
            if email_sent or sms_sent:
                logger.info(f"✅ Sent {reminder_type} reminder for appointment {appointment_id}")
            else:
                logger.error(f"❌ Failed to send {reminder_type} reminder for {appointment_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing immediate reminder: {e}")
    
    def start_reminder_service(self):
        """Start the automated reminder service"""
        if self.is_running:
            logger.warning("Reminder service already running")
            return
        
        self.is_running = True
        
        def reminder_worker():
            """Background worker for processing reminders"""
            logger.info("🚀 Reminder service worker started")
            
            while self.is_running:
                try:
                    # Process due reminders
                    self.process_due_reminders()
                    
                    # Sleep for check interval
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"❌ Error in reminder worker: {e}")
                    time.sleep(120)  # Wait longer on error
            
            logger.info("🛑 Reminder service worker stopped")
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=reminder_worker, daemon=True)
        self.worker_thread.start()
        
        logger.info("✅ Reminder service started successfully")
    
    def stop_reminder_service(self):
        """Stop the reminder service"""
        logger.info("🛑 Stopping reminder service...")
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
        
        logger.info("✅ Reminder service stopped")
    
    def process_due_reminders(self):
        """Process all reminders that are currently due"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find due reminders
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
            SELECT r.id, r.appointment_id, r.reminder_type, r.scheduled_time,
                   r.patient_email, r.patient_phone,
                   a.appointment_datetime, a.doctor, a.location,
                   p.first_name, p.last_name
            FROM reminders r
            JOIN appointments a ON r.appointment_id = a.id
            JOIN patients p ON a.patient_id = p.id
            WHERE r.scheduled_time <= ?
            AND r.sent = FALSE
            AND a.status NOT IN ('cancelled', 'completed')
            ORDER BY r.scheduled_time
            """, (current_time,))
            
            due_reminders = cursor.fetchall()
            
            if due_reminders:
                logger.info(f"📬 Processing {len(due_reminders)} due reminders")
                
                for reminder in due_reminders:
                    self._process_single_due_reminder(reminder, cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error processing due reminders: {e}")
    
    def _process_single_due_reminder(self, reminder_data: tuple, cursor):
        """Process a single due reminder"""
        try:
            (reminder_id, appointment_id, reminder_type, scheduled_time,
             patient_email, patient_phone, appointment_datetime, doctor, location,
             first_name, last_name) = reminder_data
            
            # Parse appointment datetime
            apt_datetime = datetime.fromisoformat(appointment_datetime)
            
            # Skip if appointment has already passed
            if apt_datetime <= datetime.now():
                cursor.execute("""
                UPDATE reminders 
                SET sent = TRUE, last_attempt = ?
                WHERE id = ?
                """, (datetime.now().isoformat(), reminder_id))
                logger.info(f"⏭️ Skipped expired appointment reminder {reminder_id}")
                return
            
            # Prepare reminder data
            patient_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': patient_email,
                'phone': patient_phone
            }
            
            appointment_data = {
                'id': appointment_id,
                'doctor': doctor,
                'location': location,
                'date': apt_datetime.strftime('%A, %B %d'),
                'time': apt_datetime.strftime('%I:%M %p'),
                'duration': 60  # Default
            }
            
            # Send email and SMS
            email_sent = False
            sms_sent = False
            
            if patient_email and self.email_service:
                if reminder_type == "initial":
                    email_sent = self.email_service.send_initial_reminder(patient_data, appointment_data)
                elif reminder_type == "form_check":
                    email_sent = self.email_service.send_form_check_reminder(patient_data, appointment_data)
                elif reminder_type == "final_confirmation":
                    email_sent = self.email_service.send_final_confirmation(patient_data, appointment_data)
            
            if patient_phone and self.sms_service:
                if reminder_type == "initial":
                    sms_sent = self.sms_service.send_initial_reminder_sms(patient_data, appointment_data)
                elif reminder_type == "form_check":
                    sms_sent = self.sms_service.send_form_check_sms(patient_data, appointment_data)
                elif reminder_type == "final_confirmation":
                    sms_sent = self.sms_service.send_final_confirmation_sms(patient_data, appointment_data)
            
            # Update reminder status
            overall_sent = email_sent or sms_sent
            
            cursor.execute("""
            UPDATE reminders 
            SET sent = ?, email_sent = ?, sms_sent = ?, 
                attempts = attempts + 1, last_attempt = ?
            WHERE id = ?
            """, (
                overall_sent, email_sent, sms_sent,
                datetime.now().isoformat(), reminder_id
            ))
            
            if overall_sent:
                logger.info(f"✅ Sent {reminder_type} reminder for appointment {appointment_id}")
            else:
                logger.error(f"❌ Failed to send {reminder_type} reminder for {appointment_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing reminder: {e}")
    
    def record_patient_response(self, appointment_id: str, response_type: str, 
                               response_channel: str, response_content: str = None) -> bool:
        """Record patient response to reminders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Determine action based on response
            action_map = {
                'form_completed': 'mark_forms_complete',
                'form_incomplete': 'send_form_help',
                'visit_confirmed': 'mark_visit_confirmed',
                'visit_cancelled': 'process_cancellation',
                'help_request': 'send_help_info'
            }
            
            action_taken = action_map.get(response_type, 'manual_review_required')
            
            cursor.execute("""
            INSERT INTO reminder_responses 
            (appointment_id, response_type, response_channel, response_content, action_taken)
            VALUES (?, ?, ?, ?, ?)
            """, (
                appointment_id,
                response_type,
                response_channel,
                response_content,
                action_taken
            ))
            
            # Update reminder as having received response
            cursor.execute("""
            UPDATE reminders 
            SET response_received = TRUE,
                response_data = ?
            WHERE appointment_id = ?
            AND sent = TRUE
            """, (
                json.dumps({
                    'type': response_type,
                    'channel': response_channel,
                    'content': response_content,
                    'timestamp': datetime.now().isoformat()
                }),
                appointment_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📝 Recorded {response_type} response for appointment {appointment_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording patient response: {e}")
            return False
    
    def get_reminder_statistics(self) -> Dict:
        """Get comprehensive reminder system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Basic reminder stats
            cursor.execute("""
            SELECT 
                reminder_type,
                COUNT(*) as total,
                SUM(CASE WHEN sent = TRUE THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN email_sent = TRUE THEN 1 ELSE 0 END) as email_sent,
                SUM(CASE WHEN sms_sent = TRUE THEN 1 ELSE 0 END) as sms_sent,
                SUM(CASE WHEN response_received = TRUE THEN 1 ELSE 0 END) as responses
            FROM reminders 
            WHERE created_at > date('now', '-30 days')
            GROUP BY reminder_type
            """)
            
            reminder_stats = []
            for row in cursor.fetchall():
                stats = {
                    'type': row[0],
                    'total': row[1],
                    'sent': row[2],
                    'email_sent': row[3],
                    'sms_sent': row[4],
                    'responses': row[5],
                    'send_rate': f"{(row[2]/row[1]*100):.1f}%" if row[1] > 0 else "0%",
                    'response_rate': f"{(row[5]/row[2]*100):.1f}%" if row[2] > 0 else "0%"
                }
                reminder_stats.append(stats)
            
            # Response breakdown
            cursor.execute("""
            SELECT response_type, COUNT(*) as count
            FROM reminder_responses 
            WHERE received_at > date('now', '-30 days')
            GROUP BY response_type
            """)
            
            response_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
            
            conn.close()
            
            return {
                'reminder_statistics': reminder_stats,
                'response_breakdown': response_breakdown,
                'service_status': 'active' if self.is_running else 'stopped',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting reminder statistics: {e}")
            return {
                'error': str(e),
                'service_status': 'error',
                'last_updated': datetime.now().isoformat()
            }

# Global instance management
_reminder_system_instance = None

def get_reminder_system() -> ReminderSystem:
    """Get the global reminder system instance"""
    global _reminder_system_instance
    if _reminder_system_instance is None:
        _reminder_system_instance = ReminderSystem()
    return _reminder_system_instance

def start_reminder_service() -> ReminderSystem:
    """Start the reminder service"""
    reminder_system = get_reminder_system()
    reminder_system.start_reminder_service()
    logger.info("🚀 Reminder service started")
    return reminder_system

def stop_reminder_service():
    """Stop the reminder service"""
    global _reminder_system_instance
    if _reminder_system_instance:
        _reminder_system_instance.stop_reminder_service()
        _reminder_system_instance = None
        logger.info("🛑 Reminder service stopped")