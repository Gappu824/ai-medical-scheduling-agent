"""
AI Medical Scheduling Agents Package - FIXED
RagaAI Assignment - LangGraph Agent Implementation with Error Handling
"""

import logging

logger = logging.getLogger(__name__)

# Try to import each agent with error handling
_available_agents = []

# Medical Agent (main agent)
try:
    from .medical_agent import EnhancedMedicalSchedulingAgent
    _available_agents.append('EnhancedMedicalSchedulingAgent')
    
    # Create compatibility aliases
    MedicalSchedulingAgent = EnhancedMedicalSchedulingAgent
    MedicalAgent = EnhancedMedicalSchedulingAgent
    
except ImportError as e:
    logger.warning(f"Failed to import EnhancedMedicalSchedulingAgent: {e}")
    try:
        from .medical_agent import MedicalSchedulingAgent
        _available_agents.append('MedicalSchedulingAgent')
        
        # Create aliases
        EnhancedMedicalSchedulingAgent = MedicalSchedulingAgent
        MedicalAgent = MedicalSchedulingAgent
        
    except ImportError as e2:
        logger.error(f"Failed to import any medical agent: {e2}")
        # Create placeholder
        class MedicalSchedulingAgent:
            def __init__(self):
                logger.warning("Using placeholder MedicalSchedulingAgent")
            def process_message(self, message, session_id=None):
                return "Agent not available - placeholder response"
        
        EnhancedMedicalSchedulingAgent = MedicalSchedulingAgent
        MedicalAgent = MedicalSchedulingAgent

# Patient Agent
try:
    from .patient_agent import PatientAgent
    _available_agents.append('PatientAgent')
except ImportError as e:
    logger.warning(f"Failed to import PatientAgent: {e}")
    # Create placeholder
    class PatientAgent:
        def __init__(self):
            logger.warning("Using placeholder PatientAgent")
    
# Calendar Agent  
try:
    from .calendar_agent import CalendarAgent
    _available_agents.append('CalendarAgent')
except ImportError as e:
    logger.warning(f"Failed to import CalendarAgent: {e}")
    # Create placeholder
    class CalendarAgent:
        def __init__(self):
            logger.warning("Using placeholder CalendarAgent")

# Workflow
try:
    from .workflow import MedicalWorkflow
    _available_agents.append('MedicalWorkflow')
except ImportError as e:
    logger.warning(f"Failed to import MedicalWorkflow: {e}")
    # Create placeholder
    class MedicalWorkflow:
        def __init__(self):
            logger.warning("Using placeholder MedicalWorkflow")
        def run_workflow(self, message, session_id=None):
            return {"messages": [{"role": "assistant", "content": "Workflow not available"}]}

# Export available components
__all__ = [
    'MedicalSchedulingAgent',
    'EnhancedMedicalSchedulingAgent', 
    'MedicalAgent',
    'PatientAgent',
    'CalendarAgent', 
    'MedicalWorkflow'
]

__version__ = "1.0.0"
__author__ = "RagaAI Assignment"
__description__ = "LangGraph-based medical scheduling agents with error handling"

# Log what's available
logger.info(f"Agents package loaded. Available: {_available_agents}")
if not _available_agents:
    logger.warning("No agents successfully imported - using placeholders")