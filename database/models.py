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
    patient_type: PatientType
    phone: Optional[str] = None
    email: Optional[str] = None
    insurance_carrier: Optional[str] = None
    member_id: Optional[str] = None
    group_number: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    created_at: Optional[str] = None # FIX: Added to match database

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
    created_at: Optional[str] = None # FIX: Added to match database
    
    @property
    def date_str(self) -> str:
        dt = self.appointment_datetime
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime("%Y-%m-%d")
    
    @property
    def time_str(self) -> str:
        dt = self.appointment_datetime
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        return dt.strftime("%H:%M")

@dataclass
class Reminder:
    """Reminder data model"""
    id: int
    appointment_id: str
    reminder_type: str
    scheduled_time: datetime
    sent: bool = False