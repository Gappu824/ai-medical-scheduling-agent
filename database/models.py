"""
Database Models for Medical Scheduling Agent
RagaAI Assignment - Patient and Appointment Data Models
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class PatientType(Enum):
    """Patient type enumeration"""
    NEW = "new"
    RETURNING = "returning"

class AppointmentStatus(Enum):
    """Appointment status enumeration"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

@dataclass
class Patient:
    """Patient data model"""
    id: str
    first_name: str
    last_name: str
    dob: str
    phone: str
    email: str
    patient_type: PatientType
    insurance_carrier: Optional[str] = None
    member_id: Optional[str] = None
    group_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"
    
    @property
    def appointment_duration(self) -> int:
        """Return appointment duration based on patient type"""
        return 60 if self.patient_type == PatientType.NEW else 30

@dataclass
class Appointment:
    """Appointment data model"""
    id: str
    patient_id: str
    doctor: str
    location: str
    appointment_datetime: datetime
    duration: int
    status: AppointmentStatus
    notes: Optional[str] = None
    
    @property
    def date_str(self) -> str:
        return self.appointment_datetime.strftime("%Y-%m-%d")
    
    @property
    def time_str(self) -> str:
        return self.appointment_datetime.strftime("%H:%M")

@dataclass
class Reminder:
    """Reminder data model"""
    id: int
    appointment_id: str
    reminder_type: str
    scheduled_time: datetime
    sent: bool = False
    response: Optional[str] = None
    sent_at: Optional[datetime] = None

# Available doctors and locations
AVAILABLE_DOCTORS = [
    {
        "id": "dr_johnson",
        "name": "Dr. Sarah Johnson",
        "specialty": "Allergist/Immunologist",
        "locations": ["Main Clinic", "Downtown Branch"]
    },
    {
        "id": "dr_chen", 
        "name": "Dr. Michael Chen",
        "specialty": "Pulmonologist",
        "locations": ["Main Clinic", "Suburban Office"]
    },
    {
        "id": "dr_rodriguez",
        "name": "Dr. Emily Rodriguez", 
        "specialty": "Immunologist",
        "locations": ["Main Clinic", "Downtown Branch", "Suburban Office"]
    }
]

CLINIC_LOCATIONS = [
    {
        "name": "Main Clinic",
        "address": "456 Healthcare Boulevard, Suite 300",
        "features": "Full diagnostic lab, allergy testing suite, parking available"
    },
    {
        "name": "Downtown Branch",
        "address": "789 Medical Center Drive, Suite 150", 
        "features": "Convenient downtown location, public transport access"
    },
    {
        "name": "Suburban Office",
        "address": "321 Wellness Plaza, Suite 200",
        "features": "Quiet suburban setting, easy parking, family-friendly"
    }
]