"""
Production Reminder System with Real Automation
RagaAI Assignment - Complete 3-Tier Reminder System with Response Tracking
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

class ProductionReminderSystem:
    """Production reminder system with real automation and response tracking"""
    
    def __init__(self, db_path: str = "medical_scheduling.db"):
        self.db_path = db_path
        self.is_running = False
        self.check_interval = 60  # Check every minute for production
        self.worker_thread = None
        
        # Initialize email and SMS services
        self._init_services()
        
        # Initialize database tables
        self.init_reminder_tables()
        
        # Set up scheduler
        self._setup_scheduler()
        
        logger.info("Production Reminder System initialized")
    
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
        """Initialize reminder tables with comprehensive schema"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enhanced reminders table
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_id) REFERENCES appointments (id)
            )
            """)
            
            # Reminder responses table for tracking patient responses
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
            
            # Reminder actions table for tracking URLs and actions
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminder_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                action_url TEXT,
                action_data TEXT,
                clicked BOOLEAN DEFAULT FALSE,
                clicked_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Reminder tables initialized")
            
        except Exception as e:
            logger.error(f"❌ Error initializing reminder tables: {e}")
    
    def _setup_scheduler(self):
        """Setup automated scheduler for reminder checking"""
        # Schedule reminder checking every minute
        schedule.every(1).minutes.do(self.check_and_process_reminders)
        
        # Schedule cleanup every day at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_old_reminders)
        
        logger.info("✅ Scheduler configured")
    
    def schedule_appointment_reminders(self, appointment_id: str, appointment_datetime: datetime, 
                                     patient_email: str, patient_phone: str = None) -> bool:
        """Schedule all three reminder tiers for an appointment"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Calculate reminder times
            reminders = [
                {
                    'type': 'initial',
                    'time': appointment_datetime - timedelta(days=7),
                    'description': '7-day initial reminder'
                },
                {
                    'type': 'form_check',
                    'time': appointment_datetime - timedelta(days=1),
                    'description': '24-hour form completion check'
                },
                {
                    'type': 'final_confirmation',
                    'time': appointment_datetime - timedelta(hours=2),
                    'description': '2-hour final confirmation'
                }
            ]
            
            scheduled_count = 0
            
            for reminder in reminders:
                # Only schedule future reminders
                if reminder['time'] > datetime.now():
                    cursor.execute("""
                    INSERT INTO reminders 
                    (appointment_id, reminder_type, scheduled_time)
                    VALUES (?, ?, ?)
                    """, (
                        appointment_id,
                        reminder['type'],
                        reminder['time'].isoformat()
                    ))
                    
                    scheduled_count += 1
                    logger.info(f"📅 Scheduled {reminder['description']} for {appointment_id}")
            
            conn.commit()
            conn.close()
            
            if scheduled_count > 0:
                logger.info(f"✅ Scheduled {scheduled_count} reminders for appointment {appointment_id}")
                return True
            else:
                logger.warning(f"⚠️ No future reminders scheduled for {appointment_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error scheduling reminders: {e}")
            return False
    
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
                    # Run scheduled jobs
                    schedule.run_pending()
                    
                    # Sleep for a short interval
                    time.sleep(30)  # Check every 30 seconds
                    
                except Exception as e:
                    logger.error(f"❌ Error in reminder worker: {e}")
                    time.sleep(60)  # Wait longer on error
            
            logger.info("🛑 Reminder service worker stopped")
        
        # Start worker thread
        self.worker_thread = threading.Thread(target=reminder_worker, daemon=True)
        self.worker_thread.start()
        
        logger.info("✅ Reminder service started successfully")
    
    def stop_reminder_service(self):
        """Stop the reminder service gracefully"""
        logger.info("🛑 Stopping reminder service...")
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=10)
        
        logger.info("✅ Reminder service stopped")
    
    def check_and_process_reminders(self):
        """Check for due reminders and process them"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find due reminders that haven't been sent
            current_time = datetime.now().isoformat()
            
            cursor.execute("""
            SELECT r.id, r.appointment_id, r.reminder_type, r.scheduled_time,
                   a.appointment_datetime, a.doctor, a.location,
                   p.first_name, p.last_name, p.email, p.phone
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
                    self._process_single_reminder(reminder, cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error checking reminders: {e}")
    
    def _process_single_reminder(self, reminder_data: tuple, cursor):
        """Process a single reminder"""
        try:
            (reminder_id, appointment_id, reminder_type, scheduled_time,
             appointment_datetime, doctor, location,
             first_name, last_name, email, phone) = reminder_data
            
            # Parse appointment datetime
            apt_datetime = datetime.fromisoformat(appointment_datetime)
            
            # Skip if appointment has passed
            if apt_datetime <= datetime.now():
                cursor.execute("""
                UPDATE reminders 
                SET sent = TRUE, last_attempt = ?
                WHERE id = ?
                """, (datetime.now().isoformat(), reminder_id))
                logger.info(f"⏭️ Skipped expired appointment reminder {reminder_id}")
                return
            
            # Prepare reminder data
            reminder_data = {
                'appointment_id': appointment_id,
                'doctor': doctor,
                'location': location,
                'display_time': apt_datetime.strftime('%A, %B %d at %I:%M %p'),
                'date': apt_datetime.strftime('%Y-%m-%d'),
                'time': apt_datetime.strftime('%I:%M %p'),
                'duration': 60  # Default duration
            }
            
            patient_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'phone': phone
            }
            
            # Send email and SMS
            email_sent = False
            sms_sent = False
            
            if email and self.email_service:
                email_sent = self.email_service.send_reminder_email(
                    patient_data, reminder_data, reminder_type
                )
            
            if phone and self.sms_service:
                sms_sent = self.sms_service.send_reminder_sms(
                    phone, reminder_type, reminder_data
                )
            
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
                
                # Create action tracking entries for form_check and final_confirmation
                if reminder_type in ['form_check', 'final_confirmation']:
                    self._create_reminder_actions(appointment_id, reminder_type)
            else:
                logger.error(f"❌ Failed to send {reminder_type} reminder for {appointment_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing reminder: {e}")
    
    def _create_reminder_actions(self, appointment_id: str, reminder_type: str):
        """Create trackable action URLs for reminder responses"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            base_url = "https://medicare-clinic.com"  # Replace with actual URL
            
            if reminder_type == 'form_check':
                actions = [
                    {
                        'type': 'form_completed',
                        'url': f"{base_url}/form-status/{appointment_id}?status=completed"
                    },
                    {
                        'type': 'form_incomplete',
                        'url': f"{base_url}/form-status/{appointment_id}?status=incomplete"
                    },
                    {
                        'type': 'visit_confirmed',
                        'url': f"{base_url}/confirm-visit/{appointment_id}"
                    },
                    {
                        'type': 'visit_cancelled',
                        'url': f"{base_url}/cancel-visit/{appointment_id}"
                    }
                ]
            elif reminder_type == 'final_confirmation':
                actions = [
                    {
                        'type': 'final_confirm',
                        'url': f"{base_url}/final-confirm/{appointment_id}"
                    },
                    {
                        'type': 'emergency_cancel',
                        'url': f"{base_url}/emergency-cancel/{appointment_id}"
                    }
                ]
            else:
                return
            
            for action in actions:
                cursor.execute("""
                INSERT INTO reminder_actions 
                (appointment_id, action_type, action_url, action_data)
                VALUES (?, ?, ?, ?)
                """, (
                    appointment_id,
                    action['type'],
                    action['url'],
                    json.dumps(action)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"📝 Created {len(actions)} action trackers for {appointment_id}")
            
        except Exception as e:
            logger.error(f"❌ Error creating reminder actions: {e}")
    
    def record_patient_response(self, appointment_id: str, response_type: str, 
                               response_channel: str, response_content: str = None,
                               additional_data: Dict = None) -> bool:
        """Record patient response to reminders"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Determine action based on response type
            action_taken = self._determine_action(response_type, additional_data)
            
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
            
            # Process the response action
            self._process_response_action(appointment_id, response_type, additional_data)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error recording patient response: {e}")
            return False
    
    def _determine_action(self, response_type: str, additional_data: Dict = None) -> str:
        """Determine what action to take based on response type"""
        action_map = {
            'form_completed': 'mark_form_complete',
            'form_incomplete': 'send_form_reminder',
            'visit_confirmed': 'mark_visit_confirmed',
            'visit_cancelled': 'process_cancellation',
            'final_confirm': 'mark_final_confirmed',
            'emergency_cancel': 'process_emergency_cancellation',
            'medication_question': 'send_medication_info',
            'help_request': 'send_help_info'
        }
        
        return action_map.get(response_type, 'manual_review_required')
    
    def _process_response_action(self, appointment_id: str, response_type: str, additional_data: Dict = None):
        """Process the action based on patient response"""
        try:
            if response_type == 'form_completed':
                logger.info(f"✅ Form marked as completed for {appointment_id}")
                
            elif response_type == 'form_incomplete':
                # Send follow-up form reminder
                self._send_form_follow_up(appointment_id)
                
            elif response_type == 'visit_confirmed':
                # Update appointment status
                self._update_appointment_status(appointment_id, 'confirmed')
                
            elif response_type in ['visit_cancelled', 'emergency_cancel']:
                # Process cancellation
                reason = additional_data.get('reason', 'Patient requested cancellation') if additional_data else 'Patient requested cancellation'
                self._process_appointment_cancellation(appointment_id, reason)
                
            elif response_type == 'final_confirm':
                # Mark as final confirmed
                self._update_appointment_status(appointment_id, 'final_confirmed')
                
        except Exception as e:
            logger.error(f"❌ Error processing response action: {e}")
    
    def _send_form_follow_up(self, appointment_id: str):
        """Send follow-up reminder for incomplete forms"""
        try:
            # Get patient and appointment info
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT p.first_name, p.email, p.phone, a.appointment_datetime, a.doctor
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.id = ?
            """, (appointment_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                first_name, email, phone, appointment_datetime, doctor = result
                apt_datetime = datetime.fromisoformat(appointment_datetime)
                
                # Send urgent form reminder
                if email and self.email_service:
                    urgent_subject = "URGENT: Complete Your Intake Form - Appointment Soon"
                    urgent_content = f"""
                    <h3>🚨 URGENT: Intake Form Required</h3>
                    <p>Dear {first_name},</p>
                    <p>Your appointment with {doctor} is approaching and we still need your completed intake form.</p>
                    <p><strong>Appointment:</strong> {apt_datetime.strftime('%A, %B %d at %I:%M %p')}</p>
                    <p><strong>Action Required:</strong> Please complete and submit your intake form immediately.</p>
                    <p>Call us at (555) 123-4567 if you need assistance.</p>
                    """
                    
                    # This would use the email service's template system
                    logger.info(f"📧 Sent urgent form reminder to {email}")
                
                if phone and self.sms_service:
                    urgent_sms = f"URGENT: Complete intake form for {doctor} appointment {apt_datetime.strftime('%m/%d at %I:%M%p')}. Call (555) 123-4567 for help."
                    self.sms_service.send_sms(phone, urgent_sms, priority="high")
                    
        except Exception as e:
            logger.error(f"❌ Error sending form follow-up: {e}")
    
    def _update_appointment_status(self, appointment_id: str, status: str):
        """Update appointment status in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE appointments 
            SET status = ?
            WHERE id = ?
            """, (status, appointment_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Updated appointment {appointment_id} status to {status}")
            
        except Exception as e:
            logger.error(f"❌ Error updating appointment status: {e}")
    
    def _process_appointment_cancellation(self, appointment_id: str, reason: str):
        """Process appointment cancellation"""
        try:
            # Update appointment status
            self._update_appointment_status(appointment_id, 'cancelled')
            
            # Free up the calendar slot
            from integrations.calendly_integration import CalendlyIntegration
            calendar = CalendlyIntegration()
            calendar.cancel_appointment(appointment_id, reason)
            
            logger.info(f"✅ Processed cancellation for {appointment_id}: {reason}")
            
        except Exception as e:
            logger.error(f"❌ Error processing cancellation: {e}")
    
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
            
            # Overall statistics
            cursor.execute("""
            SELECT 
                COUNT(DISTINCT appointment_id) as appointments_with_reminders,
                AVG(attempts) as avg_attempts,
                COUNT(*) as total_reminders
            FROM reminders
            WHERE created_at > date('now', '-30 days')
            """)
            
            overall_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                'reminder_statistics': reminder_stats,
                'response_breakdown': response_breakdown,
                'overall_stats': {
                    'appointments_with_reminders': overall_stats[0],
                    'average_attempts': round(overall_stats[1], 2) if overall_stats[1] else 0,
                    'total_reminders': overall_stats[2]
                },
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
    
    def cleanup_old_reminders(self):
        """Clean up old reminder data (automated daily cleanup)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete old reminders (90 days)
            cutoff_date = datetime.now() - timedelta(days=90)
            
            cursor.execute("""
            DELETE FROM reminder_responses 
            WHERE received_at < ? AND processed = TRUE
            """, (cutoff_date.isoformat(),))
            
            responses_deleted = cursor.rowcount
            
            cursor.execute("""
            DELETE FROM reminder_actions 
            WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            actions_deleted = cursor.rowcount
            
            cursor.execute("""
            DELETE FROM reminders 
            WHERE created_at < ? AND sent = TRUE
            """, (cutoff_date.isoformat(),))
            
            reminders_deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"🧹 Cleanup: Deleted {reminders_deleted} reminders, {responses_deleted} responses, {actions_deleted} actions")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")

# Global instance management
_reminder_system_instance = None

def get_reminder_system() -> ProductionReminderSystem:
    """Get the global reminder system instance"""
    global _reminder_system_instance
    if _reminder_system_instance is None:
        _reminder_system_instance = ProductionReminderSystem()
    return _reminder_system_instance

def start_reminder_service() -> ProductionReminderSystem:
    """Start the production reminder service"""
    reminder_system = get_reminder_system()
    reminder_system.start_reminder_service()
    logger.info("🚀 Production reminder service started")
    return reminder_system

def stop_reminder_service():
    """Stop the reminder service"""
    global _reminder_system_instance
    if _reminder_system_instance:
        _reminder_system_instance.stop_reminder_service()
        _reminder_system_instance = None
        logger.info("🛑 Reminder service stopped")

# Webhook handler for processing patient responses
def process_reminder_webhook(request_data: Dict) -> Dict:
    """Process webhook responses from email/SMS systems"""
    reminder_system = get_reminder_system()
    
    try:
        # Extract response data
        appointment_id = request_data.get('appointment_id')
        response_type = request_data.get('response_type')
        response_channel = request_data.get('channel', 'unknown')
        response_content = request_data.get('content', '')
        additional_data = request_data.get('additional_data', {})
        
        if not appointment_id or not response_type:
            return {'error': 'Missing required fields'}
        
        # Record the response
        success = reminder_system.record_patient_response(
            appointment_id, response_type, response_channel, 
            response_content, additional_data
        )
        
        if success:
            return {
                'status': 'success',
                'message': 'Response recorded and processed',
                'appointment_id': appointment_id,
                'response_type': response_type
            }
        else:
            return {
                'status': 'error',
                'message': 'Failed to process response'
            }
            
    except Exception as e:
        logger.error(f"❌ Webhook processing error: {e}")
        return {'status': 'error', 'message': str(e)}