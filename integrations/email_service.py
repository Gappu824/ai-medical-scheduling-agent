"""
Email Service Implementation using SendGrid
RagaAI Assignment - Email Confirmations and Form Distribution
"""

import os
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class EmailService:
    """Professional email service for medical appointment confirmations and forms"""
    
    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = "appointments@medicareallergy.com"
        self.clinic_name = "MediCare Allergy & Wellness Center"
        
    def send_appointment_confirmation(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send appointment confirmation email to patient"""
        try:
            subject = f"Appointment Confirmation - {self.clinic_name}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ background: #2c5aa0; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .appointment-details {{ background: white; padding: 20px; border-left: 4px solid #2c5aa0; margin: 15px 0; }}
                    .important {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{self.clinic_name}</h1>
                    <h2>Appointment Confirmation</h2>
                </div>
                
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <p>Your appointment has been successfully scheduled. Please review the details below:</p>
                    
                    <div class="appointment-details">
                        <h3>Appointment Details</h3>
                        <p><strong>Date:</strong> {appointment_data.get('date', 'TBD')}</p>
                        <p><strong>Time:</strong> {appointment_data.get('time', 'TBD')}</p>
                        <p><strong>Doctor:</strong> {appointment_data.get('doctor', 'TBD')}</p>
                        <p><strong>Location:</strong> {appointment_data.get('location', 'Main Clinic')}</p>
                        <p><strong>Duration:</strong> {appointment_data.get('duration', 60)} minutes</p>
                    </div>
                    
                    <div class="important">
                        <h3>Important Pre-Visit Information</h3>
                        <p>Your intake form will be sent separately and must be completed 24 hours before your visit.</p>
                        <p><strong>Please bring:</strong> Insurance cards, photo ID, and current medication list</p>
                    </div>
                    
                    <p>If you need to reschedule or have questions, please call us at (555) 123-4567.</p>
                </div>
                
                <div class="footer">
                    <p>{self.clinic_name}<br>
                    456 Healthcare Boulevard, Suite 300<br>
                    Phone: (555) 123-4567</p>
                </div>
            </body>
            </html>
            """
            
            # Mock email sending (in real implementation, use SendGrid API)
            logger.info(f"Email confirmation sent to {patient_data.get('email', 'patient@example.com')}")
            logger.info(f"Subject: {subject}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send confirmation email: {e}")
            return False
    
    def send_intake_form(self, patient_data: Dict, appointment_data: Dict) -> bool:
        """Send intake form email to patient (only after appointment confirmation)"""
        try:
            subject = f"Complete Your Intake Form - {appointment_data.get('date', 'Upcoming Appointment')}"
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ background: #2c5aa0; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .form-info {{ background: white; padding: 20px; border-left: 4px solid #28a745; margin: 15px 0; }}
                    .critical {{ background: #f8d7da; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0; }}
                    .footer {{ text-align: center; padding: 20px; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{self.clinic_name}</h1>
                    <h2>Patient Intake Form</h2>
                </div>
                
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    
                    <p>Please complete your patient intake form before your appointment on {appointment_data.get('date', 'your scheduled date')}.</p>
                    
                    <div class="form-info">
                        <h3>Form Completion Instructions</h3>
                        <p><strong>Deadline:</strong> Must be completed 24 hours before your appointment</p>
                        <p><strong>Form:</strong> New Patient Intake Form (attached)</p>
                        <p><strong>Submission:</strong> Email back to appointments@medicareallergy.com</p>
                    </div>
                    
                    <div class="critical">
                        <h3>CRITICAL: Pre-Visit Medication Instructions</h3>
                        <p><strong>If allergy testing is planned, you MUST stop the following medications 7 days before your appointment:</strong></p>
                        <ul>
                            <li>All antihistamines (Claritin, Zyrtec, Allegra, Benadryl)</li>
                            <li>Cold medications containing antihistamines</li>
                            <li>Sleep aids like Tylenol PM</li>
                        </ul>
                        <p><strong>You MAY continue:</strong> Nasal sprays (Flonase, Nasacort), asthma inhalers, and prescription medications</p>
                    </div>
                    
                    <p>If you have questions about medications or the form, please call (555) 123-4567.</p>
                </div>
                
                <div class="footer">
                    <p>{self.clinic_name}<br>
                    456 Healthcare Boulevard, Suite 300<br>
                    Phone: (555) 123-4567</p>
                </div>
            </body>
            </html>
            """
            
            # Mock email sending with form attachment
            logger.info(f"Intake form email sent to {patient_data.get('email', 'patient@example.com')}")
            logger.info(f"Subject: {subject}")
            logger.info("Attachment: patient_intake_form.pdf")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send intake form email: {e}")
            return False
    
    def send_reminder_email(self, patient_data: Dict, appointment_data: Dict, reminder_type: str) -> bool:
        """Send appointment reminder email"""
        try:
            if reminder_type == "initial":
                subject = f"Appointment Reminder - {appointment_data.get('date', 'Upcoming')}"
                message = "This is a friendly reminder about your upcoming appointment."
            elif reminder_type == "form_check":
                subject = f"Action Required: Form Completion - {appointment_data.get('date', 'Tomorrow')}"
                message = "Please confirm you have completed your intake form and are ready for your appointment."
            else:  # final
                subject = f"Final Reminder - Appointment Today"
                message = "Your appointment is in 2 hours. Please arrive 15 minutes early."
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; }}
                    .header {{ background: #2c5aa0; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .reminder {{ background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Appointment Reminder</h1>
                </div>
                <div class="content">
                    <p>Dear {patient_data.get('first_name', 'Patient')},</p>
                    <div class="reminder">
                        <p>{message}</p>
                        <p><strong>Appointment:</strong> {appointment_data.get('date', 'TBD')} at {appointment_data.get('time', 'TBD')}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            logger.info(f"Reminder email ({reminder_type}) sent to {patient_data.get('email', 'patient@example.com')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send reminder email: {e}")
            return False