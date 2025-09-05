"""
AI Medical Scheduling Agents Package
RagaAI Assignment - LangGraph Agent Implementation
"""

from .medical_agent import MedicalSchedulingAgent
from .patient_agent import PatientAgent
from .calendar_agent import CalendarAgent
from .workflow import MedicalWorkflow

__all__ = [
    'MedicalSchedulingAgent',
    'PatientAgent', 
    'CalendarAgent',
    'MedicalWorkflow'
]

__version__ = "1.0.0"
__author__ = "RagaAI Assignment"
__description__ = "LangGraph-based medical scheduling agents"