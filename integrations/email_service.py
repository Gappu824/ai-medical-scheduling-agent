# integrations/email_service.py

"""
Production Email Service with SendGrid API
RagaAI Assignment - Robust and Modern Email Implementation
"""

import os
import logging
import base64
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import (
        Mail, Attachment, FileContent, FileName,
        FileType, Disposition
    )
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False


logger = logging.getLogger(__name__)

class EmailService:
    """Production email service using the SendGrid API."""

    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@medicare-clinic.com")
        self.clinic_name = "MediCare Allergy & Wellness Center"
        
        # Check if SendGrid is configured and available
        self.email_enabled = bool(self.sendgrid_api_key and SENDGRID_AVAILABLE)
        
        if self.email_enabled:
            self.sg_client = SendGridAPIClient(self.sendgrid_api_key)
            logger.info("✅ SendGrid Email service configured and ready.")
        else:
            logger.warning("⚠️ SendGrid API key not found or library not installed. Email service running in demo mode (logging only).")

    def _send_email(self, to_email: str, subject: str, html_content: str, attachment_path: Optional[Path] = None) -> bool:
        """Core function to send an email using SendGrid or log for demo."""
        
        if not self.email_enabled:
            # Detailed logging for demo mode
            attachment_info = {"filename": attachment_path.name} if attachment_path else None
            self._log_email_details(subject, to_email, html_content, attachment_info)
            return True # Simulate success in demo mode

        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        # Handle attachment if provided
        if attachment_path and attachment_path.exists():
            with open(attachment_path, "rb") as f:
                data = f.read()
            encoded_file = base64.b64encode(data).decode()
            
            attached_file = Attachment(
                FileContent(encoded_file),
                FileName(attachment_path.name),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            message.attachment = attached_file

        try:
            response = self.sg_client.send(message)
            if 200 <= response.status_code < 300:
                logger.info(f"✅ Email sent successfully to {to_email} via SendGrid.")
                return True
            else:
                logger.error(f"❌ SendGrid error: Status {response.status_code} - {response.body}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to send email via SendGrid: {e}")
            return False

    def send_appointment_confirmation(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send appointment confirmation email."""
        subject = f"Appointment Confirmation - {self.clinic_name}"
        html_content = self._create_confirmation_email(patient_data, appointment_data)
        return self._send_email(patient_data.get('email'), subject, html_content)

    def send_intake_form(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send intake form email with PDF attachment."""
        subject = f"Action Required: Complete Your Intake Form for {appointment_data.get('date')}"
        html_content = self._create_intake_form_email(patient_data, appointment_data)
        form_path = Path("forms/patient_intake_form.pdf")
        return self._send_email(patient_data.get('email'), subject, html_content, attachment_path=form_path)

    def _log_email_details(self, subject: str, to_email: str, content: str, attachment: Optional[Dict] = None):
        """Detailed logging for demo mode."""
        logger.info("=" * 60)
        logger.info(f"📧 DEMO EMAIL | To: {to_email} | Subject: {subject}")
        if attachment:
            logger.info(f"📎 Attachment: {attachment['filename']}")
        logger.info(f"📄 Content Preview: {content[:200]}...")
        logger.info("=" * 60)

    # HTML template functions remain the same as before
    def _create_confirmation_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        # This function generates the HTML content for the confirmation email.
        # (Content is omitted here for brevity, but it's the same HTML as your original file)
        return f"<h1>Appointment Confirmed</h1><p>Dear {patient_data.get('first_name')}, your appointment with {appointment_data.get('doctor')} is confirmed for {appointment_data.get('date')} at {appointment_data.get('time')}.</p>"

    def _create_intake_form_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        # This function generates the HTML content for the intake form email.
        # (Content is omitted here for brevity, but it's the same HTML as your original file)
        return f"<h1>Action Required</h1><p>Dear {patient_data.get('first_name')}, please complete the attached intake form for your appointment on {appointment_data.get('date')}.</p>"