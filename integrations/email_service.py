import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EmailService:
    """Production email service with SendGrid + 3-tier reminder templates"""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@medicare-clinic.com")
        
        self.email_enabled = bool(self.sendgrid_api_key and "your_sendgrid_key" not in self.sendgrid_api_key)
        
        if self.email_enabled:
            self.sg = SendGridAPIClient(self.sendgrid_api_key)
            logger.info("✅ SendGrid email service configured and enabled.")
        else:
            logger.warning("⚠️ SendGrid API key not found or is a placeholder - running in demo mode.")

    def _send_email(self, to_email: str, subject: str, html_content: str, attachment_path: Optional[Path] = None) -> bool:
        """Core email sending function with detailed error logging."""
        
        if not self.email_enabled:
            self._log_email_demo(to_email, subject, html_content, attachment_path)
            return True
        
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        if attachment_path and attachment_path.exists():
            with open(attachment_path, 'rb') as f:
                data = f.read()
            encoded_file = base64.b64encode(data).decode()
            attachedFile = Attachment(
                FileContent(encoded_file),
                FileName(attachment_path.name),
                FileType('application/pdf'),
                Disposition('attachment')
            )
            message.attachment = attachedFile

        try:
            response = self.sg.send(message)
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email sent successfully to {to_email} with status code {response.status_code}")
                return True
            else:
                logger.error(f"❌ Failed to send email to {to_email}. Status: {response.status_code}, Body: {response.body}")
                return False
        except Exception as e:
            logger.error(f"❌ Exception while sending email to {to_email}: {e}")
            return False

    def send_intake_forms(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Sends the new patient intake form."""
        to_email = patient_data.get('email')
        if not to_email:
            return False
            
        subject = "Your New Patient Intake Form from MediCare"
        html_content = f"""
        <h1>Welcome to MediCare, {patient_data.get('first_name')}!</h1>
        <p>Please find your new patient intake form attached. To ensure a smooth check-in process, please complete and return it to us at your earliest convenience.</p>
        <p>Your appointment is scheduled for {appointment_data.get('appointment_datetime')}.</p>
        """
        attachment_path = Path("forms/patient_intake_form.pdf")
        return self._send_email(to_email, subject, html_content, attachment_path)

    def _log_email_demo(self, to_email: str, subject: str, content: str, attachment: Optional[Path]):
        logger.info(f"DEMO EMAIL to {to_email}: {subject}")