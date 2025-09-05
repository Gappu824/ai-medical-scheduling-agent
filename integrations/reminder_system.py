"""
Complete Automated Reminder System Implementation
RagaAI Assignment - 3-Tier Reminder System with Email/SMS and Action Tracking
"""

import os
import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum

from database.database import DatabaseManager
from database.models import Appointment, Patient, Reminder
from integrations.email_service import EmailService
from integrations.sms_service import SMSService

logger = logging.getLogger(__name__)

class ReminderType(Enum):
    """Types of automated reminders"""
    INITIAL = "initial"           # 7 days before - regular reminder
    FORM_CHECK = "form_check"     # 24 hours before - form completion check with actions
    FINAL = "final"               # 2 hours before - visit confirmation with actions

@dataclass
class ReminderAction:
    """Action required in reminder"""
    action_id: str
    question: str
    response_options: List[str]
    follow_up_required: bool = False

class AutomatedReminderSystem:
    """Complete automated reminder system with scheduling and tracking"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.is_running = False
        self.scheduler_thread = None
        
        # Set up reminder schedule
        self._setup_reminder_schedule()
        
        logger.info("Automated Reminder System initialized")
    
    def _setup_reminder_schedule(self):
        """Set up automated reminder checking schedule"""
        
        # Check for reminders every 30 minutes
        schedule.every(30).minutes.do(self._check_and_send_reminders)
        
        # Daily cleanup of old reminders
        schedule.every().day.at("23:00").do(self._cleanup_old_reminders)
        
        logger.info("Reminder schedule configured: every 30 minutes + daily cleanup")
    
    def schedule_appointment_reminders(self, appointment: Appointment, patient: Patient):
        """Schedule all 3 reminders for an appointment"""
        
        try:
            # Calculate reminder times
            reminder_times = {
                ReminderType.INITIAL: appointment.appointment_datetime - timedelta(days=7),
                ReminderType.FORM_CHECK: appointment.appointment_datetime - timedelta(days=1), 
                ReminderType.FINAL: appointment.appointment_datetime - timedelta(hours=2)
            }
            
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Schedule each reminder
            for reminder_type, reminder_time in reminder_times.items():
                # Skip if reminder time has already passed
                if reminder_time <= datetime.now():
                    logger.warning(f"Skipping {reminder_type.value} reminder for {appointment.id} - time has passed")
                    continue
                
                cursor.execute("""
                INSERT INTO reminders (appointment_id, reminder_type, scheduled_time, sent, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    appointment.id,
                    reminder_type.value,
                    reminder_time.isoformat(),
                    False,
                    datetime.now().isoformat()
                ))
                
                logger.info(f"Scheduled {reminder_type.value} reminder for {appointment.id} at {reminder_time}")
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to schedule reminders for appointment {appointment.id}: {e}")
            return False
    
    def _check_and_send_reminders(self):
        """Check for due reminders and send them"""
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Find reminders that are due (scheduled time <= now) and not sent
            cursor.execute("""
            SELECT r.id, r.appointment_id, r.reminder_type, r.scheduled_time,
                   a.appointment_datetime, a.doctor, a.location, a.duration,
                   p.first_name, p.last_name, p.email, p.phone
            FROM reminders r
            JOIN appointments a ON r.appointment_id = a.id
            JOIN patients p ON a.patient_id = p.id
            WHERE r.scheduled_time <= ? AND r.sent = FALSE
            ORDER BY r.scheduled_time ASC
            """, (datetime.now().isoformat(),))
            
            due_reminders = cursor.fetchall()
            
            logger.info(f"Found {len(due_reminders)} due reminders to process")
            
            for reminder_data in due_reminders:
                self._send_individual_reminder(reminder_data, cursor)
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    def _send_individual_reminder(self, reminder_data: tuple, cursor):
        """Send an individual reminder based on its type"""
        
        (reminder_id, appointment_id, reminder_type, scheduled_time,
         apt_datetime, doctor, location, duration,
         first_name, last_name, email, phone) = reminder_data
        
        try:
            # Parse appointment datetime
            appointment_dt = datetime.fromisoformat(apt_datetime)
            
            # Skip if appointment has passed
            if appointment_dt <= datetime.now():
                self._mark_reminder_sent(cursor, reminder_id, "Appointment time passed")
                return
            
            # Create reminder content based on type
            if reminder_type == ReminderType.INITIAL.value:
                success = self._send_initial_reminder(
                    email, phone, first_name, appointment_dt, doctor, location
                )
            elif reminder_type == ReminderType.FORM_CHECK.value:
                success = self._send_form_check_reminder(
                    email, phone, first_name, appointment_dt, doctor, location, appointment_id
                )
            elif reminder_type == ReminderType.FINAL.value:
                success = self._send_final_confirmation_reminder(
                    email, phone, first_name, appointment_dt, doctor, location, appointment_id
                )
            else:
                logger.warning(f"Unknown reminder type: {reminder_type}")
                success = False
            
            # Mark as sent if successful
            if success:
                self._mark_reminder_sent(cursor, reminder_id, "Sent successfully")
                logger.info(f"Successfully sent {reminder_type} reminder for appointment {appointment_id}")
            else:
                logger.error(f"Failed to send {reminder_type} reminder for appointment {appointment_id}")
                
        except Exception as e:
            logger.error(f"Error sending reminder {reminder_id}: {e}")
    
    def _send_initial_reminder(self, email: str, phone: str, first_name: str, 
                              appointment_dt: datetime, doctor: str, location: str) -> bool:
        """Send initial 7-day reminder (regular reminder)"""
        
        email_subject = "Appointment Reminder - 7 Days"
        email_body = f"""
        Dear {first_name},
        
        This is a friendly reminder about your upcoming appointment:
        
        📅 Date: {appointment_dt.strftime('%A, %B %d, %Y')}
        🕐 Time: {appointment_dt.strftime('%I:%M %p')}
        👩‍⚕️ Doctor: {doctor}
        🏢 Location: {location}
        
        What to remember:
        ✅ Patient intake forms will be sent 24 hours before your visit
        ✅ Please arrive 15 minutes early
        ✅ Bring your insurance card and photo ID
        
        If you need to reschedule or cancel, please call us at (555) 123-4567.
        
        We look forward to seeing you!
        
        Best regards,
        MediCare Allergy & Wellness Center
        """
        
        sms_body = f"Reminder: Appointment with {doctor} on {appointment_dt.strftime('%m/%d at %I:%M%p')} at {location}. Call (555) 123-4567 for changes."
        
        # Send email and SMS
        email_sent = self.email_service.send_email(email, email_subject, email_body)
        sms_sent = self.sms_service.send_sms(phone, sms_body)
        
        return email_sent and sms_sent
    
    def _send_form_check_reminder(self, email: str, phone: str, first_name: str,
                                 appointment_dt: datetime, doctor: str, location: str, 
                                 appointment_id: str) -> bool:
        """Send form completion check reminder with actions (24 hours before)"""
        
        # Generate unique action links for tracking
        form_check_url = f"https://medicare-clinic.com/form-status/{appointment_id}"
        complete_form_url = f"https://medicare-clinic.com/intake-form/{appointment_id}"
        
        email_subject = "Important: Complete Your Intake Form - Appointment Tomorrow"
        email_body = f"""
        Dear {first_name},
        
        Your appointment is TOMORROW! 🗓️
        
        📅 {appointment_dt.strftime('%A, %B %d, %Y')} at {appointment_dt.strftime('%I:%M %p')}
        👩‍⚕️ {doctor} at {location}
        
        🚨 IMPORTANT ACTION REQUIRED:
        
        1️⃣ Have you completed your patient intake form?
           👍 Yes, I completed it: {form_check_url}?status=completed
           👎 No, I need to complete it: {complete_form_url}
        
        2️⃣ Is your visit still confirmed?
           ✅ Yes, I'll be there: {form_check_url}?status=confirmed
           ❌ I need to cancel/reschedule: {form_check_url}?status=cancel
        
        ⏰ CRITICAL REMINDERS:
        • If allergy testing is planned, STOP antihistamines NOW (7 days before)
        • Arrive 15 minutes early tomorrow
        • Bring insurance card and photo ID
        
        Questions? Call (555) 123-4567
        
        Thank you!
        MediCare Allergy & Wellness Center
        """
        
        sms_body = f"TOMORROW: {doctor} at {appointment_dt.strftime('%I:%M%p')}. Have you completed intake form? Reply YES/NO. Confirm visit? Reply CONFIRM/CANCEL. Call (555) 123-4567"
        
        # Send email and SMS with action tracking
        email_sent = self.email_service.send_email(email, email_subject, email_body)
        sms_sent = self.sms_service.send_sms(phone, sms_body)
        
        # Log the action URLs for tracking
        if email_sent:
            self._log_reminder_actions(appointment_id, ReminderType.FORM_CHECK, {
                "form_check_url": form_check_url,
                "complete_form_url": complete_form_url,
                "email": email,
                "phone": phone
            })
        
        return email_sent and sms_sent
    
    def _send_final_confirmation_reminder(self, email: str, phone: str, first_name: str,
                                        appointment_dt: datetime, doctor: str, location: str,
                                        appointment_id: str) -> bool:
        """Send final confirmation reminder with actions (2 hours before)"""
        
        # Generate confirmation tracking URLs
        confirm_url = f"https://medicare-clinic.com/confirm/{appointment_id}"
        cancel_url = f"https://medicare-clinic.com/cancel/{appointment_id}"
        
        email_subject = "FINAL REMINDER: Your Appointment is in 2 Hours!"
        email_body = f"""
        Dear {first_name},
        
        🚨 YOUR APPOINTMENT IS IN 2 HOURS! 🚨
        
        📅 TODAY at {appointment_dt.strftime('%I:%M %p')}
        👩‍⚕️ {doctor}
        🏢 {location}
        
        🎯 FINAL CONFIRMATION REQUIRED:
        
        ✅ I'm coming to my appointment: {confirm_url}
        ❌ I need to cancel (please tell us why): {cancel_url}
        
        📋 LAST-MINUTE CHECKLIST:
        • ✅ Intake form completed?
        • ✅ Stopped antihistamines if having allergy testing?
        • ✅ Have insurance card and photo ID?
        • ✅ Know the location and parking?
        
        🗺️ DIRECTIONS:
        {location}
        456 Healthcare Boulevard, Suite 300
        Parking available in front of building
        
        ❗ If you don't confirm or cancel, we may need to charge a no-show fee.
        
        Questions? Call (555) 123-4567 - we're here to help!
        
        See you soon!
        MediCare Team
        """
        
        sms_body = f"FINAL REMINDER: Appointment with {doctor} in 2 HOURS at {appointment_dt.strftime('%I:%M%p')}! Reply CONFIRM or CANCEL with reason. Address: 456 Healthcare Blvd #300"
        
        # Send with high priority
        email_sent = self.email_service.send_email(email, email_subject, email_body, priority="high")
        sms_sent = self.sms_service.send_sms(phone, sms_body, priority="high")
        
        # Log the action URLs for tracking
        if email_sent:
            self._log_reminder_actions(appointment_id, ReminderType.FINAL, {
                "confirm_url": confirm_url,
                "cancel_url": cancel_url,
                "email": email,
                "phone": phone,
                "final_reminder": True
            })
        
        return email_sent and sms_sent
    
    def _log_reminder_actions(self, appointment_id: str, reminder_type: ReminderType, action_data: Dict):
        """Log reminder actions for tracking responses"""
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Store action data as JSON for later processing
            cursor.execute("""
            INSERT INTO reminder_actions (appointment_id, reminder_type, action_data, created_at)
            VALUES (?, ?, ?, ?)
            """, (
                appointment_id,
                reminder_type.value,
                json.dumps(action_data),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Logged reminder actions for {appointment_id}, type: {reminder_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to log reminder actions: {e}")
    
    def _mark_reminder_sent(self, cursor, reminder_id: int, response: str = ""):
        """Mark a reminder as sent in the database"""
        
        cursor.execute("""
        UPDATE reminders 
        SET sent = TRUE, response = ?, sent_at = ?
        WHERE id = ?
        """, (response, datetime.now().isoformat(), reminder_id))
    
    def _cleanup_old_reminders(self):
        """Clean up old reminders (older than 30 days)"""
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor.execute("""
            DELETE FROM reminders 
            WHERE created_at < ? AND sent = TRUE
            """, (cutoff_date,))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            logger.info(f"Cleaned up {deleted_count} old reminders")
            
        except Exception as e:
            logger.error(f"Error cleaning up old reminders: {e}")
    
    def handle_patient_response(self, appointment_id: str, response_type: str, response_data: Dict):
        """Handle patient responses to reminder actions"""
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Log the response
            cursor.execute("""
            INSERT INTO reminder_responses (appointment_id, response_type, response_data, received_at)
            VALUES (?, ?, ?, ?)
            """, (
                appointment_id,
                response_type,
                json.dumps(response_data),
                datetime.now().isoformat()
            ))
            
            # Take appropriate action based on response
            if response_type == "form_completed":
                self._handle_form_completion(appointment_id, cursor)
            elif response_type == "visit_confirmed":
                self._handle_visit_confirmation(appointment_id, cursor)
            elif response_type == "visit_cancelled":
                self._handle_visit_cancellation(appointment_id, response_data, cursor)
            elif response_type == "sms_response":
                self._handle_sms_response(appointment_id, response_data, cursor)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Processed patient response for {appointment_id}: {response_type}")
            
        except Exception as e:
            logger.error(f"Error handling patient response: {e}")
    
    def _handle_form_completion(self, appointment_id: str, cursor):
        """Handle form completion confirmation"""
        
        cursor.execute("""
        UPDATE appointments 
        SET notes = COALESCE(notes, '') || 'Form completed via reminder system. '
        WHERE id = ?
        """, (appointment_id,))
        
        logger.info(f"Marked form as completed for appointment {appointment_id}")
    
    def _handle_visit_confirmation(self, appointment_id: str, cursor):
        """Handle visit confirmation"""
        
        cursor.execute("""
        UPDATE appointments 
        SET status = 'confirmed', notes = COALESCE(notes, '') || 'Visit confirmed via reminder. '
        WHERE id = ?
        """, (appointment_id,))
        
        logger.info(f"Confirmed visit for appointment {appointment_id}")
    
    def _handle_visit_cancellation(self, appointment_id: str, response_data: Dict, cursor):
        """Handle visit cancellation with reason"""
        
        cancellation_reason = response_data.get("reason", "No reason provided")
        
        cursor.execute("""
        UPDATE appointments 
        SET status = 'cancelled', 
            notes = COALESCE(notes, '') || 'Cancelled via reminder: ' || ?
        WHERE id = ?
        """, (cancellation_reason, appointment_id))
        
        logger.info(f"Cancelled appointment {appointment_id}, reason: {cancellation_reason}")
    
    def _handle_sms_response(self, appointment_id: str, response_data: Dict, cursor):
        """Handle SMS responses (YES/NO, CONFIRM/CANCEL, etc.)"""
        
        sms_text = response_data.get("message", "").upper()
        
        if sms_text in ["YES", "COMPLETED", "DONE"]:
            self._handle_form_completion(appointment_id, cursor)
        elif sms_text in ["CONFIRM", "CONFIRMED", "YES"]:
            self._handle_visit_confirmation(appointment_id, cursor)
        elif sms_text.startswith("CANCEL"):
            reason = sms_text.replace("CANCEL", "").strip() or "SMS cancellation"
            self._handle_visit_cancellation(appointment_id, {"reason": reason}, cursor)
        
        logger.info(f"Processed SMS response for {appointment_id}: {sms_text}")
    
    def start_reminder_scheduler(self):
        """Start the automated reminder scheduler in a background thread"""
        
        if self.is_running:
            logger.warning("Reminder scheduler is already running")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("Starting automated reminder scheduler...")
            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Automated reminder scheduler started successfully")
    
    def stop_reminder_scheduler(self):
        """Stop the automated reminder scheduler"""
        
        self.is_running = False
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Automated reminder scheduler stopped")
    
    def get_reminder_statistics(self) -> Dict:
        """Get statistics about reminder system performance"""
        
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Get reminder stats
            cursor.execute("""
            SELECT 
                reminder_type,
                COUNT(*) as total,
                SUM(CASE WHEN sent = TRUE THEN 1 ELSE 0 END) as sent,
                SUM(CASE WHEN response IS NOT NULL THEN 1 ELSE 0 END) as responded
            FROM reminders 
            WHERE created_at > date('now', '-30 days')
            GROUP BY reminder_type
            """)
            
            reminder_stats = cursor.fetchall()
            
            # Get response stats
            cursor.execute("""
            SELECT response_type, COUNT(*) as count
            FROM reminder_responses 
            WHERE received_at > date('now', '-30 days')
            GROUP BY response_type
            """)
            
            response_stats = cursor.fetchall()
            
            conn.close()
            
            return {
                "reminder_stats": [
                    {
                        "type": row[0],
                        "total": row[1], 
                        "sent": row[2],
                        "responded": row[3],
                        "response_rate": f"{(row[3]/row[2]*100):.1f}%" if row[2] > 0 else "0%"
                    }
                    for row in reminder_stats
                ],
                "response_stats": [
                    {"type": row[0], "count": row[1]}
                    for row in response_stats
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting reminder statistics: {e}")
            return {"error": str(e)}

# Global reminder system instance
_reminder_system = None

def get_reminder_system() -> AutomatedReminderSystem:
    """Get the global reminder system instance"""
    global _reminder_system
    if _reminder_system is None:
        _reminder_system = AutomatedReminderSystem()
    return _reminder_system

def start_reminder_service():
    """Start the reminder service (call this when app starts)"""
    reminder_system = get_reminder_system()
    reminder_system.start_reminder_scheduler()
    return reminder_system

def stop_reminder_service():
    """Stop the reminder service (call this when app stops)"""
    global _reminder_system
    if _reminder_system:
        _reminder_system.stop_reminder_scheduler()
        _reminder_system = None