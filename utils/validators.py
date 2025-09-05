"""
Input Validation Utilities for Medical Scheduling Agent - Fixed Syntax
RagaAI Assignment - Data Validation and Format Checking
"""

import re
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

def validate_patient_info(patient_data: Dict) -> Tuple[bool, List[str]]:
    """Validate patient information"""
    
    errors = []
    
    # Validate required fields
    required_fields = ["first_name", "last_name", "dob"]
    for field in required_fields:
        if not patient_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate name fields
    if patient_data.get("first_name"):
        if not validate_name(patient_data["first_name"]):
            errors.append("Invalid first name format")
    
    if patient_data.get("last_name"):
        if not validate_name(patient_data["last_name"]):
            errors.append("Invalid last name format")
    
    # Validate date of birth
    if patient_data.get("dob"):
        if not validate_date_of_birth(patient_data["dob"]):
            errors.append("Invalid date of birth format (use YYYY-MM-DD)")
    
    # Validate phone number
    if patient_data.get("phone"):
        if not validate_phone_number(patient_data["phone"]):
            errors.append("Invalid phone number format")
    
    # Validate email
    if patient_data.get("email"):
        if not validate_email(patient_data["email"]):
            errors.append("Invalid email address format")
    
    return len(errors) == 0, errors

def validate_appointment_data(appointment_data: Dict) -> Tuple[bool, List[str]]:
    """Validate appointment information"""
    
    errors = []
    
    # Validate required fields
    required_fields = ["doctor", "location", "datetime", "duration"]
    for field in required_fields:
        if not appointment_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate doctor
    if appointment_data.get("doctor"):
        valid_doctors = ["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez"]
        if appointment_data["doctor"] not in valid_doctors:
            errors.append(f"Invalid doctor selection: {appointment_data['doctor']}")
    
    # Validate location
    if appointment_data.get("location"):
        valid_locations = ["Main Clinic", "Downtown Branch", "Suburban Office"]
        if appointment_data["location"] not in valid_locations:
            errors.append(f"Invalid location selection: {appointment_data['location']}")
    
    # Validate duration
    if appointment_data.get("duration"):
        if not isinstance(appointment_data["duration"], int) or appointment_data["duration"] not in [30, 60, 90]:
            errors.append("Invalid duration (must be 30, 60, or 90 minutes)")
    
    # Validate appointment datetime
    if appointment_data.get("datetime"):
        if not validate_appointment_datetime(appointment_data["datetime"]):
            errors.append("Invalid appointment date/time")
    
    return len(errors) == 0, errors

def validate_name(name: str) -> bool:
    """Validate name field"""
    
    if not name or not isinstance(name, str):
        return False
    
    # Name should only contain letters, spaces, hyphens, and apostrophes
    pattern = r"^[a-zA-Z\s\-']+$"
    
    if not re.match(pattern, name):
        return False
    
    # Name should be between 1 and 50 characters
    if len(name.strip()) < 1 or len(name.strip()) > 50:
        return False
    
    return True

def validate_date_of_birth(dob: str) -> bool:
    """Validate date of birth"""
    
    if not dob or not isinstance(dob, str):
        return False
    
    # Try different date formats
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(dob, date_format).date()
            
            # Check if date is reasonable (not in future, not too old)
            today = date.today()
            min_date = date(today.year - 120, today.month, today.day)  # 120 years ago
            
            if min_date <= parsed_date <= today:
                return True
        except ValueError:
            continue
    
    return False

def validate_phone_number(phone: str) -> bool:
    """Validate phone number"""
    
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # US phone number should have 10 or 11 digits
    if len(digits_only) == 10:
        return True
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return True
    
    return False

def validate_email(email: str) -> bool:
    """Validate email address"""
    
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        return False
    
    # Check length
    if len(email) > 254:
        return False
    
    return True

def validate_appointment_datetime(appointment_datetime) -> bool:
    """Validate appointment date and time"""
    
    if isinstance(appointment_datetime, str):
        try:
            # Try to parse ISO format
            parsed_datetime = datetime.fromisoformat(appointment_datetime)
        except ValueError:
            return False
    elif isinstance(appointment_datetime, datetime):
        parsed_datetime = appointment_datetime
    else:
        return False
    
    # Check if appointment is in the future
    if parsed_datetime <= datetime.now():
        return False
    
    # Check if appointment is within business hours (9 AM - 5 PM)
    if not (9 <= parsed_datetime.hour < 17):
        return False
    
    # Check if appointment is on a weekday
    if parsed_datetime.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check if appointment is not too far in the future (e.g., within 1 year)
    max_future_date = datetime.now().replace(year=datetime.now().year + 1)
    if parsed_datetime > max_future_date:
        return False
    
    return True

def validate_insurance_info(insurance_data: Dict) -> Tuple[bool, List[str]]:
    """Validate insurance information"""
    
    errors = []
    
    # Validate insurance carrier
    if insurance_data.get("carrier"):
        valid_carriers = [
            "BlueCross BlueShield", "Aetna", "Cigna", "UnitedHealthcare", 
            "Kaiser Permanente", "Humana", "Anthem"
        ]
        if insurance_data["carrier"] not in valid_carriers:
            # Allow other carriers but log a warning
            logger.warning(f"Unusual insurance carrier: {insurance_data['carrier']}")
    
    # Validate member ID
    if insurance_data.get("member_id"):
        member_id = insurance_data["member_id"]
        if not isinstance(member_id, str) or len(member_id) < 5 or len(member_id) > 20:
            errors.append("Invalid member ID format")
    
    # Validate group number
    if insurance_data.get("group_number"):
        group_number = insurance_data["group_number"]
        if not isinstance(group_number, str) or len(group_number) < 3 or len(group_number) > 15:
            errors.append("Invalid group number format")
    
    return len(errors) == 0, errors

def sanitize_input(input_text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    
    if not input_text or not isinstance(input_text, str):
        return ""
    
    # Remove potential harmful characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
    
    sanitized = input_text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length
    max_length = 1000
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

def format_phone_number(phone: str) -> str:
    """Format phone number to standard format"""
    
    if not validate_phone_number(phone):
        return phone
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Format as (XXX) XXX-XXXX
    if len(digits_only) == 10:
        return f"({digits_only[:3]}) {digits_only[3:6]}-{digits_only[6:]}"
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return f"1-({digits_only[1:4]}) {digits_only[4:7]}-{digits_only[7:]}"
    
    return phone

def format_date_of_birth(dob: str) -> str:
    """Format date of birth to standard YYYY-MM-DD format"""
    
    if not dob or not isinstance(dob, str):
        return dob
    
    # Try different date formats
    date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%Y/%m/%d"]
    
    for date_format in date_formats:
        try:
            parsed_date = datetime.strptime(dob, date_format)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return dob

def validate_business_hours(check_datetime: datetime) -> bool:
    """Check if datetime falls within business hours"""
    
    # Business hours: Monday-Friday, 9 AM - 5 PM
    
    # Check if it's a weekday
    if check_datetime.weekday() >= 5:
        return False
    
    # Check if it's within business hours
    if not (9 <= check_datetime.hour < 17):
        return False
    
    return True

def validate_appointment_duration(duration: int, patient_type: str) -> bool:
    """Validate appointment duration based on patient type"""
    
    if patient_type == "new":
        # New patients: 60 or 90 minutes
        return duration in [60, 90]
    elif patient_type == "returning":
        # Returning patients: 30 or 60 minutes
        return duration in [30, 60]
    else:
        # Unknown patient type, allow standard durations
        return duration in [30, 60, 90]

def extract_patient_info_from_text(text: str) -> Dict:
    """Extract patient information from natural language text"""
    
    extracted_info = {}
    
    # Extract name patterns
    name_patterns = [
        r"(?:my name is|i'm|i am)\s+([a-zA-Z]+)\s+([a-zA-Z]+)",
        r"([a-zA-Z]+)\s+([a-zA-Z]+)(?:\s+is my name)",
        r"^([a-zA-Z]+)\s+([a-zA-Z]+)"  # Names at start of text
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_info["first_name"] = match.group(1).title()
            extracted_info["last_name"] = match.group(2).title()
            break
    
    # Extract date of birth patterns
    dob_patterns = [
        r"(?:born|birth|dob|date of birth).*?(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"(\d{1,2}[/-]\d{1,2}[/-]\d{4})",
        r"(?:born|birth).*?(\w+\s+\d{1,2},?\s+\d{4})"  # "March 15, 1985"
    ]
    
    for pattern in dob_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            extracted_info["dob"] = match.group(1)
            break
    
    # Extract phone number
    phone_pattern = r"(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})"
    phone_match = re.search(phone_pattern, text)
    if phone_match:
        extracted_info["phone"] = phone_match.group(1)
    
    # Extract email
    email_pattern = r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    email_match = re.search(email_pattern, text)
    if email_match:
        extracted_info["email"] = email_match.group(1)
    
    return extracted_info

def check_appointment_conflicts(doctor: str, appointment_datetime: datetime, duration: int) -> bool:
    """Check for appointment scheduling conflicts"""
    
    # This would integrate with your calendar system
    # For now, return a mock conflict check
    
    # Check if appointment is during lunch break (12-1 PM)
    if 12 <= appointment_datetime.hour < 13:
        return True
    
    # Check if appointment would run past business hours
    end_time = appointment_datetime.hour + (duration / 60)
    if end_time > 17:  # 5 PM
        return True
    
    return False

def validate_insurance_member_id(member_id: str, carrier: str = None) -> bool:
    """Validate insurance member ID format based on carrier"""
    
    if not member_id or not isinstance(member_id, str):
        return False
    
    # Remove spaces and dashes
    clean_id = re.sub(r'[\s-]', '', member_id)
    
    # Basic validation - should be alphanumeric and reasonable length
    if not re.match(r'^[A-Za-z0-9]+$', clean_id):
        return False
    
    if len(clean_id) < 5 or len(clean_id) > 20:
        return False
    
    return True