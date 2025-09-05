"""
Enhanced Logging Configuration with Visual Feedback
"""

import logging
import sys
from datetime import datetime

class VisualFormatter(logging.Formatter):
    """Custom formatter with visual indicators"""
    
    def format(self, record):
        # Add visual indicators
        if record.levelno >= logging.ERROR:
            icon = "❌"
        elif record.levelno >= logging.WARNING:
            icon = "⚠️"
        elif record.levelno >= logging.INFO:
            icon = "✅"
        else:
            icon = "🔍"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Create visual log entry
        return f"{icon} {timestamp} [{record.name}] {record.getMessage()}"

def setup_visual_logging():
    """Setup enhanced visual logging for all components"""
    
    # Create console handler with visual formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(VisualFormatter())
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler],
        format='%(message)s'
    )
    
    # Configure specific loggers
    loggers_to_configure = [
        'agents.medical_agent',
        'integrations.reminder_system',
        'integrations.email_service',
        'integrations.sms_service',
        'utils.excel_export',
        'database.database'
    ]
    
    for logger_name in loggers_to_configure:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)
