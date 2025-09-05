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
    from .medical_agent import MedicalSchedulingAgent
    _available_agents.append('MedicalSchedulingAgent')
    
    # Create compatibility aliases
    EnhancedMedicalSchedulingAgent = MedicalSchedulingAgent
    MedicalAgent = MedicalSchedulingAgent
    
except ImportError as e:
    logger.error(f"Failed to import MedicalSchedulingAgent: {e}")
    # Create a placeholder class if the import fails
    class MedicalSchedulingAgent:
        def __init__(self):
            logger.error("Using placeholder MedicalSchedulingAgent due to import failure.")
        def process_message(self, message, session_id=None):
            return "Agent not available - placeholder response. Please check logs for import errors."
    
    EnhancedMedicalSchedulingAgent = MedicalSchedulingAgent
    MedicalAgent = MedicalSchedulingAgent


# Export available components
__all__ = [
    'MedicalSchedulingAgent',
    'EnhancedMedicalSchedulingAgent', 
    'MedicalAgent',
]

__version__ = "1.0.1"
__author__ = "RagaAI Assignment"
__description__ = "LangGraph-based medical scheduling agents with error handling"

# Log what's available
logger.info(f"Agents package loaded. Available: {_available_agents}")
if 'MedicalSchedulingAgent' not in _available_agents:
    logger.critical("CRITICAL: The main MedicalSchedulingAgent could not be loaded.")