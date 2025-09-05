"""
Enhanced SMS Service for 3-Tier Reminder System
RagaAI Assignment - Real SMS with Response Handling
"""

import os
import logging
import re
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class SMSService:
    """Production SMS service with Twilio, phone number validation, and demo fallback"""
    
    def __init__(self):
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        
        self.twilio_enabled = bool(self.twilio_sid and self.twilio_token and self.twilio_phone and "your_twilio" not in self.twilio_sid)
        
        self.twilio_client = None
        if self.twilio_enabled:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(self.twilio_sid, self.twilio_token)
                logger.info("✅ Twilio SMS service configured and enabled.")
            except ImportError:
                logger.warning("Twilio library not installed. SMS service will run in demo mode.")
                self.twilio_enabled = False
            except Exception as e:
                logger.error(f"Twilio initialization failed: {e}. Running in demo mode.")
                self.twilio_enabled = False
        else:
            logger.warning("⚠️ Twilio credentials not found or are placeholders - running in demo mode.")

    def _validate_and_format_phone(self, phone_number: str) -> Optional[str]:
        """Validates and formats a phone number to E.164 format."""
        if not phone_number or not isinstance(phone_number, str):
            return None
        # Remove all non-digit characters
        cleaned_number = re.sub(r'\D', '', phone_number)
        
        # Check if it's a valid international number already
        if phone_number.startswith('+') and len(cleaned_number) > 7:
            return phone_number

        # Assume Indian number if 10 digits
        if len(cleaned_number) == 10:
            return f"+91{cleaned_number}"
        # Handle cases where + is missing but country code is present
        elif len(cleaned_number) > 10:
             return f"+{cleaned_number}"

        logger.warning(f"Could not format invalid phone number: {phone_number}")
        return None

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Send SMS using Twilio, with robust validation and logging."""
        
        formatted_phone = self._validate_and_format_phone(to_phone)
        if not formatted_phone:
            logger.error(f"Invalid phone number provided: {to_phone}. Cannot send SMS.")
            return False
            
        if not self.twilio_enabled:
            self._log_sms_demo("OUTGOING SMS (DEMO)", formatted_phone, message)
            return True
        
        try:
            message_obj = self.twilio_client.messages.create(
                body=message,
                from_=self.twilio_phone,
                to=formatted_phone
            )
            logger.info(f"✅ Twilio SMS sent to {formatted_phone}, SID: {message_obj.sid}")
            return True
        except Exception as e:
            logger.error(f"❌ Twilio SMS failed: {e}")
            return False
            
    def _log_sms_demo(self, sms_type: str, phone: str, message: str):
        """Log SMS details in demo mode"""
        logger.info("=" * 50)
        logger.info(f"📱 {sms_type}")
        logger.info("=" * 50)
        logger.info(f"📞 To Phone: {phone}")
        logger.info(f"📝 Message: {message}")
        logger.info("=" * 50)

    def send_initial_reminder_sms(self, patient_data: Dict, appointment_data: Dict) -> bool:
        phone = patient_data.get('phone')
        if not phone: return False
        message = f"🏥 MediCare: Reminder for your appointment on {appointment_data.get('date')} at {appointment_data.get('time')}. Call (555) 123-4567 with questions."
        return self.send_sms(phone, message)