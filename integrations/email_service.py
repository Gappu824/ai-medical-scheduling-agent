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
        
        # ... (attachment logic remains the same)

        try:
            response = self.sg.send(message)
            if response.status_code in [200, 202]:
                logger.info(f"✅ Email sent successfully to {to_email} with status code {response.status_code}")
                return True
            else:
                logger.error(f"❌ Failed to send email to {to_email}. Status: {response.status_code}, Body: {response.body}")
                if response.status_code == 403:
                    logger.error("="*50)
                    logger.error("TROUBLESHOOTING 403 FORBIDDEN ERROR:")
                    logger.error("1. VERIFY API KEY: Ensure your SENDGRID_API_KEY in the .env file is correct.")
                    logger.error("2. CHECK PERMISSIONS: In SendGrid, ensure your API key has FULL ACCESS to 'Mail Send'.")
                    logger.error(f"3. VERIFY SENDER: Make sure the 'FROM_EMAIL' ('{self.from_email}') is a verified Single Sender in your SendGrid account.")
                    logger.error("="*50)
                return False
        except Exception as e:
            logger.error(f"❌ Exception while sending email to {to_email}: {e}")
            return False

    # ... (the rest of your email service methods remain the same)
    def _log_email_demo(self, to_email: str, subject: str, content: str, attachment: Optional[Path]):
        logger.info(f"DEMO EMAIL to {to_email}: {subject}")
