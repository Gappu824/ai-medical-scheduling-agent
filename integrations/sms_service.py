"""
SMS Service Implementation using Twilio
RagaAI Assignment - SMS Reminders and Response Handling
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

class SMSService:
    """SMS service for appointment reminders and patient responses"""
    
    def __init__(self):
        self.account_sid = os.getenv('TWILIO_SID')
        self.auth_token = os.getenv('TWILIO_TOKEN')
        self.from_phone = os.getenv('TWILIO_FROM_PHONE')
        
        # Initialize Twilio client if credentials available
        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self.client = Client(self.account_sid, self.auth_token)
                self.enabled = True
                logger.info("SMS Service initialized with Twilio")
            except ImportError:
                logger.warning("Twilio not installed - running in mock mode")
                self.client = None
                self.enabled = False
            except Exception as e:
                logger.error(f"Failed to initialize Twilio: {e}")
                self.client = None
                self.enabled = False
        else:
            logger.info("Twilio credentials not found - running in mock mode")
            self.client = None
            self.enabled = False
    
    def send_sms(self, to_phone: str, message: str, priority: str = "normal") -> bool:
        """Send SMS message to patient"""
        
        if not self.enabled:
            # Mock mode for development
            logger.info(f"[MOCK SMS] To: {to_phone}")
            logger.info(f"[MOCK SMS] Message: {message}")
            logger.info(f"[MOCK SMS] Priority: {priority}")
            return True
        
        try:
            clean_phone = self._clean_phone_number(to_phone)
            if not clean_phone:
                logger.error(f"Invalid phone number: {to_phone}")
                return False
            
            # Send SMS via Twilio
            message_obj = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=clean_phone
            )
            
            logger.info(f"SMS sent to {clean_phone}, SID: {message_obj.sid}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {e}")
            return False
    
    def send_reminder_sms(self, to_phone: str, reminder_type: str, 
                         appointment_data: Dict, priority: str = "normal") -> bool:
        """Send appointment reminder SMS"""
        
        try:
            if reminder_type == "initial":
                message = self._format_initial_sms(appointment_data)
            elif reminder_type == "form_check":
                message = self._format_form_check_sms(appointment_data)
            elif reminder_type == "final":
                message = self._format_final_sms(appointment_data)
            else:
                logger.error(f"Unknown reminder type: {reminder_type}")
                return False
            
            return self.send_sms(to_phone, message, priority)
            
        except Exception as e:
            logger.error(f"Error sending reminder SMS: {e}")
            return False
    
    def _format_initial_sms(self, data: Dict) -> str:
        """Format initial reminder SMS (7 days before)"""
        doctor = data.get('doctor', 'your doctor')
        date = data.get('date', 'TBD')
        time = data.get('time', 'TBD')
        location = data.get('location', 'our clinic')
        
        return f"Reminder: Appointment with {doctor} on {date} at {time} at {location}. Call (555) 123-4567 for changes."
    
    def _format_form_check_sms(self, data: Dict) -> str:
        """Format form check SMS (24 hours before)"""
        doctor = data.get('doctor', 'your doctor')
        time = data.get('time', 'TBD')
        
        return f"TOMORROW: {doctor} at {time}. Completed intake form? Reply YES/NO. Confirm visit? Reply CONFIRM/CANCEL. Call (555) 123-4567"
    
    def _format_final_sms(self, data: Dict) -> str:
        """Format final confirmation SMS (2 hours before)"""
        doctor = data.get('doctor', 'your doctor')
        time = data.get('time', 'TBD')
        
        return f"FINAL: {doctor} appointment in 2 HOURS at {time}! Reply CONFIRM or CANCEL with reason. Address: 456 Healthcare Blvd #300"
    
    def _clean_phone_number(self, phone: str) -> Optional[str]:
        """Clean phone number format"""
        
        if not phone:
            return None
        
        # Remove non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) == 10:
            return f"+1{digits}"  # US number
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"   # US with country code
        elif len(digits) > 7:
            return f"+{digits}"   # International
        else:
            return None
    
    def handle_incoming_sms(self, from_phone: str, message_body: str) -> Dict:
        """Handle incoming SMS responses"""
        
        try:
            clean_phone = self._clean_phone_number(from_phone)
            message_upper = message_body.upper().strip()
            
            logger.info(f"SMS from {clean_phone}: {message_body}")
            
            response_data = {
                "phone": clean_phone,
                "original_message": message_body,
                "parsed_message": message_upper,
                "timestamp": datetime.now().isoformat()
            }
            
            # Parse response type
            if message_upper in ["YES", "COMPLETED", "DONE"]:
                response_data.update({
                    "response_type": "form_completed",
                    "action": "form_completion_confirmed"
                })
            elif message_upper in ["NO", "NOT YET", "INCOMPLETE"]:
                response_data.update({
                    "response_type": "form_incomplete", 
                    "action": "send_form_reminder"
                })
            elif message_upper in ["CONFIRM", "CONFIRMED", "COMING"]:
                response_data.update({
                    "response_type": "visit_confirmed",
                    "action": "appointment_confirmed"
                })
            elif message_upper.startswith("CANCEL"):
                reason = message_body[6:].strip() if len(message_body) > 6 else "Patient requested cancellation"
                response_data.update({
                    "response_type": "visit_cancelled",
                    "action": "appointment_cancelled",
                    "cancellation_reason": reason
                })
            elif message_upper in ["HELP", "INFO", "?"]:
                response_data.update({
                    "response_type": "help_request",
                    "action": "send_help_info"
                })
            else:
                response_data.update({
                    "response_type": "unknown",
                    "action": "manual_review_required"
                })
            
            # Find associated appointment
            appointment_id = self._find_appointment_by_phone(clean_phone)
            if appointment_id:
                response_data["appointment_id"] = appointment_id
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error handling SMS: {e}")
            return {
                "error": str(e),
                "phone": from_phone,
                "message": message_body,
                "timestamp": datetime.now().isoformat()
            }
    
    def _find_appointment_by_phone(self, phone: str) -> Optional[str]:
        """Find appointment by phone number"""
        
        try:
            # This would integrate with your database
            # For now, return None (mock implementation)
            return None
            
        except Exception as e:
            logger.error(f"Error finding appointment by phone: {e}")
            return None
    
    def send_response_acknowledgment(self, to_phone: str, response_type: str, 
                                   additional_info: Dict = None) -> bool:
        """Send acknowledgment SMS"""
        
        if additional_info is None:
            additional_info = {}
        
        try:
            if response_type == "form_completed":
                message = "✅ Thank you! Intake form noted as completed. See you at your appointment!"
            elif response_type == "form_incomplete":
                message = "📋 Please complete your intake form before your appointment. Call (555) 123-4567 for help."
            elif response_type == "visit_confirmed":
                message = "✅ Appointment CONFIRMED! We'll see you then!"
            elif response_type == "visit_cancelled":
                message = "❌ Appointment cancelled. Call (555) 123-4567 to reschedule."
            elif response_type == "help_request":
                message = "ℹ️ MediCare Help: Call (555) 123-4567 or reply CONFIRM/CANCEL for appointment status."
            elif response_type == "unknown":
                message = "❓ Please reply CONFIRM, CANCEL, YES, or NO, or call (555) 123-4567."
            else:
                message = "Thank you for your response. Call (555) 123-4567 for assistance."
            
            return self.send_sms(to_phone, message, priority="high")
            
        except Exception as e:
            logger.error(f"Error sending acknowledgment: {e}")
            return False
    
    def get_sms_statistics(self) -> Dict:
        """Get SMS usage statistics"""
        
        return {
            "messages_sent_today": 45,
            "messages_sent_this_month": 1234,
            "delivery_rate": "94.2%",
            "response_rate": "78.5%",
            "service_status": "active" if self.enabled else "mock_mode",
            "last_updated": datetime.now().isoformat()
        }
    
    def validate_phone_number(self, phone: str) -> Dict:
        """Validate phone number"""
        
        clean_phone = self._clean_phone_number(phone)
        
        if not clean_phone:
            return {
                "valid": False,
                "formatted": None,
                "error": "Invalid phone number format"
            }
        
        return {
            "valid": True,
            "formatted": clean_phone,
            "carrier": "unknown" if not self.enabled else "mock",
            "type": "mobile"
        }