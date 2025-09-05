"""
Enhanced Email Service for 3-Tier Reminder System
RagaAI Assignment - Real Email Templates with Action Links
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class EmailService:
    """Production email service with Gmail SMTP + 3-tier reminder templates"""
    
    def __init__(self):
        # Email configuration
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = os.getenv("GMAIL_USER", "noreply@medicare-clinic.com")
        self.email_password = os.getenv("GMAIL_APP_PASSWORD", "")
        
        # Clinic information
        self.clinic_name = "MediCare Allergy & Wellness Center"
        self.clinic_phone = "(555) 123-4567"
        self.clinic_address = "456 Healthcare Boulevard, Suite 300"
        self.clinic_website = "www.medicare-clinic.com"
        
        # Check if email is configured
        self.email_enabled = bool(self.email_user and self.email_password)
        
        if self.email_enabled:
            logger.info("✅ Gmail SMTP email service configured")
        else:
            logger.warning("⚠️ Email credentials not found - running in demo mode")
    
    def send_reminder_email(self, to_email: str, reminder_content: str) -> bool:
        """Send a reminder email (used by the agent)"""
        subject = f"Appointment Reminder - {self.clinic_name}"
        return self._send_email(to_email, subject, reminder_content)
    
    def send_appointment_confirmation(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send appointment confirmation email after booking"""
        subject = f"Appointment Confirmed - {self.clinic_name}"
        html_content = self._create_confirmation_email(patient_data, appointment_data)
        return self._send_email(patient_data.get('email'), subject, html_content)
    
    def send_intake_forms(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send intake forms email with PDF attachment"""
        subject = f"Complete Your Intake Forms - Appointment {appointment_data.get('date')}"
        html_content = self._create_intake_forms_email(patient_data, appointment_data)
        
        # Attach the intake form PDF
        form_path = Path("forms/patient_intake_form.pdf")
        return self._send_email(
            patient_data.get('email'), 
            subject, 
            html_content, 
            attachment_path=form_path
        )
    
    def send_initial_reminder(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send 7-day initial reminder (Tier 1)"""
        subject = f"Appointment Reminder - {appointment_data.get('date')}"
        html_content = self._create_initial_reminder_email(patient_data, appointment_data)
        return self._send_email(patient_data.get('email'), subject, html_content)
    
    def send_form_check_reminder(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send 24-hour form check reminder with actions (Tier 2)"""
        subject = f"ACTION REQUIRED: Appointment Tomorrow - {appointment_data.get('date')}"
        html_content = self._create_form_check_email(patient_data, appointment_data)
        return self._send_email(patient_data.get('email'), subject, html_content)
    
    def send_final_confirmation(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send 2-hour final confirmation (Tier 3)"""
        subject = f"FINAL REMINDER: Appointment in 2 Hours!"
        html_content = self._create_final_confirmation_email(patient_data, appointment_data)
        return self._send_email(patient_data.get('email'), subject, html_content)
    
    def _send_email(self, to_email: str, subject: str, html_content: str, 
                   attachment_path: Optional[Path] = None) -> bool:
        """Core email sending function"""
        
        if not self.email_enabled:
            # Demo mode - log the email instead of sending
            self._log_email_demo(to_email, subject, html_content, attachment_path)
            return True
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add HTML content
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Add attachment if provided
            if attachment_path and attachment_path.exists():
                with open(attachment_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment_path.name}',
                )
                msg.attach(part)
            
            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"✅ Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {e}")
            return False
    
    def _log_email_demo(self, to_email: str, subject: str, content: str, attachment: Optional[Path]):
        """Log email details in demo mode"""
        logger.info("=" * 60)
        logger.info(f"📧 DEMO EMAIL SENT")
        logger.info("=" * 60)
        logger.info(f"📬 To: {to_email}")
        logger.info(f"📝 Subject: {subject}")
        if attachment:
            logger.info(f"📎 Attachment: {attachment.name}")
        logger.info(f"📄 Content Preview: {content[:200]}...")
        logger.info("=" * 60)
    
    def _create_confirmation_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        """Create appointment confirmation email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2E8B57; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .appointment-box {{ background: white; padding: 15px; border-left: 4px solid #2E8B57; margin: 15px 0; }}
                .button {{ background: #2E8B57; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏥 {self.clinic_name}</h1>
                    <h2>Appointment Confirmed!</h2>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <p>Your appointment has been successfully scheduled. Here are your details:</p>
                    
                    <div class="appointment-box">
                        <h3>📅 Appointment Details</h3>
                        <p><strong>Doctor:</strong> {appointment_data.get('doctor', 'TBD')}</p>
                        <p><strong>Date & Time:</strong> {appointment_data.get('date', 'TBD')} at {appointment_data.get('time', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_data.get('location', 'TBD')}</p>
                        <p><strong>Duration:</strong> {appointment_data.get('duration', 60)} minutes</p>
                        <p><strong>Appointment ID:</strong> {appointment_data.get('id', 'TBD')}</p>
                    </div>
                    
                    <h3>📋 What's Next?</h3>
                    <ul>
                        <li>✅ You'll receive intake forms to complete (due 24 hours before appointment)</li>
                        <li>✅ We'll send 3 automated reminders (7 days, 24 hours, 2 hours before)</li>
                        <li>✅ Insurance verification will be processed</li>
                    </ul>
                    
                    <h3>📍 Important Information</h3>
                    <ul>
                        <li><strong>Arrive 15 minutes early</strong> for check-in</li>
                        <li><strong>Bring:</strong> Insurance card, photo ID, completed forms</li>
                        <li><strong>Parking:</strong> Free parking available on-site</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="https://medicare-clinic.com/confirm/{appointment_data.get('id')}" class="button">
                            ✅ Confirm Appointment
                        </a>
                        <a href="https://medicare-clinic.com/reschedule/{appointment_data.get('id')}" class="button" style="background: #dc3545;">
                            📅 Reschedule
                        </a>
                    </div>
                </div>
                <div class="footer">
                    <p>📞 Questions? Call us at {self.clinic_phone}</p>
                    <p>📍 {self.clinic_address}</p>
                    <p>🌐 {self.clinic_website}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_intake_forms_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        """Create intake forms email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2E8B57; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .urgent {{ background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .button {{ background: #2E8B57; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 Intake Forms Required</h1>
                    <h2>{self.clinic_name}</h2>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <div class="urgent">
                        <h3>⚠️ Action Required</h3>
                        <p><strong>Please complete the attached intake forms before your appointment on {appointment_data.get('date')}.</strong></p>
                    </div>
                    
                    <h3>📎 Attached Documents</h3>
                    <ul>
                        <li>Patient Intake Form (PDF)</li>
                        <li>Medical History Questionnaire</li>
                        <li>Insurance Information Form</li>
                    </ul>
                    
                    <h3>📋 Instructions</h3>
                    <ol>
                        <li><strong>Download</strong> the attached PDF form</li>
                        <li><strong>Complete</strong> all sections thoroughly</li>
                        <li><strong>Submit</strong> completed forms 24 hours before your appointment</li>
                    </ol>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="https://medicare-clinic.com/forms/upload/{appointment_data.get('id')}" class="button">
                            📤 Upload Completed Forms
                        </a>
                    </div>
                    
                    <p><strong>Need Help?</strong> Call us at {self.clinic_phone} if you have questions about the forms.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_initial_reminder_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        """Create 7-day initial reminder email (Tier 1)"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #2E8B57; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .reminder-box {{ background: white; padding: 15px; border-left: 4px solid #2E8B57; margin: 15px 0; }}
                .button {{ background: #2E8B57; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📅 Appointment Reminder</h1>
                    <h2>{self.clinic_name}</h2>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <p>This is a friendly reminder about your upcoming appointment:</p>
                    
                    <div class="reminder-box">
                        <h3>📅 Your Appointment</h3>
                        <p><strong>Doctor:</strong> {appointment_data.get('doctor', 'TBD')}</p>
                        <p><strong>Date & Time:</strong> {appointment_data.get('date', 'TBD')} at {appointment_data.get('time', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_data.get('location', 'TBD')}</p>
                        <p><strong>Duration:</strong> {appointment_data.get('duration', 60)} minutes</p>
                    </div>
                    
                    <h3>📋 What to Expect</h3>
                    <ul>
                        <li>📧 You'll receive intake forms in the next few days</li>
                        <li>📱 We'll send additional reminders closer to your appointment</li>
                        <li>🚗 Free parking is available on-site</li>
                    </ul>
                    
                    <div style="text-align: center; margin: 20px 0;">
                        <a href="https://medicare-clinic.com/confirm/{appointment_data.get('id')}" class="button">
                            ✅ Confirm Appointment
                        </a>
                        <a href="https://medicare-clinic.com/reschedule/{appointment_data.get('id')}" class="button" style="background: #dc3545;">
                            📅 Need to Reschedule?
                        </a>
                    </div>
                    
                    <p>📞 Questions or need to make changes? Call us at {self.clinic_phone}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_form_check_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        """Create 24-hour form check reminder with actions (Tier 2)"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #ffc107; color: #212529; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .urgent {{ background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .action-buttons {{ text-align: center; margin: 20px 0; }}
                .button {{ color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; font-weight: bold; }}
                .btn-yes {{ background: #28a745; }}
                .btn-no {{ background: #dc3545; }}
                .btn-confirm {{ background: #2E8B57; }}
                .btn-cancel {{ background: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ APPOINTMENT TOMORROW!</h1>
                    <h2>{self.clinic_name}</h2>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <div class="urgent">
                        <h3>🚨 Your appointment is TOMORROW!</h3>
                        <p><strong>{appointment_data.get('date', 'TBD')} at {appointment_data.get('time', 'TBD')}</strong></p>
                        <p><strong>Doctor:</strong> {appointment_data.get('doctor', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_data.get('location', 'TBD')}</p>
                    </div>
                    
                    <h3>📋 ACTION REQUIRED - Please Confirm:</h3>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>1️⃣ Have you completed your intake forms?</h4>
                        <div class="action-buttons">
                            <a href="https://medicare-clinic.com/forms/completed/{appointment_data.get('id')}" class="button btn-yes">
                                ✅ YES - Forms Completed
                            </a>
                            <a href="https://medicare-clinic.com/forms/incomplete/{appointment_data.get('id')}" class="button btn-no">
                                ❌ NO - Need Help with Forms
                            </a>
                        </div>
                    </div>
                    
                    <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>2️⃣ Will you be attending your appointment?</h4>
                        <div class="action-buttons">
                            <a href="https://medicare-clinic.com/visit/confirmed/{appointment_data.get('id')}" class="button btn-confirm">
                                ✅ YES - I'll Be There
                            </a>
                            <a href="https://medicare-clinic.com/visit/cancel/{appointment_data.get('id')}" class="button btn-cancel">
                                ❌ NO - Need to Cancel
                            </a>
                        </div>
                    </div>
                    
                    <h3>📍 Appointment Details</h3>
                    <ul>
                        <li><strong>Arrive:</strong> 15 minutes early for check-in</li>
                        <li><strong>Bring:</strong> Insurance card, photo ID, completed forms</li>
                        <li><strong>Address:</strong> {self.clinic_address}</li>
                        <li><strong>Parking:</strong> Free on-site parking available</li>
                    </ul>
                    
                    <div style="background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <p><strong>📞 Need to speak with us?</strong> Call {self.clinic_phone}</p>
                        <p><strong>⏰ Last-minute cancellations:</strong> Please call as soon as possible to avoid charges</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_final_confirmation_email(self, patient_data: Dict, appointment_data: Dict) -> str:
        """Create 2-hour final confirmation email (Tier 3)"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #dc3545; color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 20px; border-radius: 0 0 10px 10px; }}
                .urgent {{ background: #f8d7da; border: 2px solid #dc3545; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .final-actions {{ text-align: center; margin: 20px 0; }}
                .button {{ color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px 5px; font-weight: bold; }}
                .btn-confirm {{ background: #28a745; }}
                .btn-emergency {{ background: #dc3545; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 FINAL REMINDER</h1>
                    <h2>Your appointment is in 2 HOURS!</h2>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <div class="urgent">
                        <h3>🕐 APPOINTMENT IN 2 HOURS!</h3>
                        <p><strong>TODAY at {appointment_data.get('time', 'TBD')}</strong></p>
                        <p><strong>Doctor:</strong> {appointment_data.get('doctor', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_data.get('location', 'TBD')}</p>
                    </div>
                    
                    <h3>🏃‍♀️ Final Checklist</h3>
                    <ul style="font-size: 18px; line-height: 1.8;">
                        <li>✅ <strong>Leave now:</strong> Arrive 15 minutes early</li>
                        <li>✅ <strong>Bring:</strong> Insurance card, photo ID, completed forms</li>
                        <li>✅ <strong>Address:</strong> {self.clinic_address}</li>
                        <li>✅ <strong>Parking:</strong> Free on-site (entrance on Healthcare Blvd)</li>
                    </ul>
                    
                    <div class="final-actions">
                        <h3>🚨 LAST CHANCE ACTIONS</h3>
                        <a href="https://medicare-clinic.com/final/confirm/{appointment_data.get('id')}" class="button btn-confirm">
                            ✅ CONFIRMED - On My Way!
                        </a>
                        <a href="https://medicare-clinic.com/emergency/cancel/{appointment_data.get('id')}" class="button btn-emergency">
                            🚨 EMERGENCY CANCEL
                        </a>
                    </div>
                    
                    <div style="background: #fff3cd; border: 2px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0;">
                        <h4>📞 Running Late or Need Help?</h4>
                        <p style="font-size: 18px; margin: 0;"><strong>CALL IMMEDIATELY: {self.clinic_phone}</strong></p>
                        <p style="margin: 5px 0 0 0;">We can hold your slot for up to 15 minutes if you call ahead.</p>
                    </div>
                    
                    <p style="text-align: center; font-size: 16px;"><strong>We look forward to seeing you soon! 🏥</strong></p>
                </div>
            </div>
        </body>
        </html>
        """