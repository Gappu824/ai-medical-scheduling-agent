#!/usr/bin/env python3
"""
AI Medical Scheduling Agent - Main Entry Point
RagaAI Assignment - Complete Production System Launcher
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv
import sqlite3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def ensure_directories():
    """Ensure all required directories exist"""
    directories = ["data", "exports", "logs", "forms", "forms/form_templates"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep for empty directories
        gitkeep_file = Path(directory) / ".gitkeep"
        if not gitkeep_file.exists():
            with open(gitkeep_file, "w") as f:
                f.write("# Keep directory in git\n")

def check_environment():
    """Check production environment configuration"""
    load_dotenv()
    
    issues = []
    
    # Check critical environment variables
    required_vars = {
        'GOOGLE_API_KEY': 'Google Gemini API key is required for AI functionality'
    }
    
    optional_vars = {
        'GMAIL_USER': 'Gmail user for email service',
        'GMAIL_APP_PASSWORD': 'Gmail app password for email service',
        'TWILIO_ACCOUNT_SID': 'Twilio SID for SMS service',
        'TWILIO_AUTH_TOKEN': 'Twilio token for SMS service',
        'TWILIO_PHONE_NUMBER': 'Twilio phone number for SMS service'
    }
    
    # Check required variables
    for var, description in required_vars.items():
        if not os.getenv(var):
            issues.append(f"❌ Missing {var}: {description}")
        else:
            logger.info(f"✅ {var} configured")
    
    # Check optional variables
    for var, description in optional_vars.items():
        if not os.getenv(var):
            logger.warning(f"⚠️ Optional {var} not configured: {description}")
        else:
            logger.info(f"✅ {var} configured")
    
    if issues:
        logger.error("Environment configuration issues:")
        for issue in issues:
            logger.error(issue)
        return False
    
    return True

def initialize_database():
    """Initialize production database with all required tables"""
    logger.info("Initializing production database...")
    
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            patient_type TEXT NOT NULL DEFAULT 'new',
            insurance_carrier TEXT,
            member_id TEXT,
            group_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relationship TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Appointments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor TEXT NOT NULL,
            location TEXT NOT NULL,
            appointment_datetime TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT DEFAULT 'scheduled',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
        """)
        
        # Reminders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL CHECK(reminder_type IN ('initial', 'form_check', 'final_confirmation')),
            scheduled_time TEXT NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            email_sent BOOLEAN DEFAULT FALSE,
            sms_sent BOOLEAN DEFAULT FALSE,
            response_received BOOLEAN DEFAULT FALSE,
            response_data TEXT,
            attempts INTEGER DEFAULT 0,
            last_attempt TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id)
        )
        """)
        
        # Reminder responses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminder_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            reminder_id INTEGER,
            response_type TEXT NOT NULL,
            response_channel TEXT NOT NULL,
            response_content TEXT,
            action_taken TEXT,
            processed BOOLEAN DEFAULT FALSE,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id),
            FOREIGN KEY (reminder_id) REFERENCES reminders (id)
        )
        """)
        
        # SMS responses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sms_responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            phone TEXT NOT NULL,
            response_type TEXT NOT NULL,
            original_message TEXT,
            parsed_data TEXT,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE
        )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_name ON patients (last_name, first_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_patients_dob ON patients (dob)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_appointments_datetime ON appointments (appointment_datetime)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_scheduled ON reminders (scheduled_time, sent)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Production database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

def load_sample_data():
    """Load sample data if not already present"""
    logger.info("Loading sample data...")
    
    try:
        from data.generate_data import generate_all_data
        generate_all_data()
        logger.info("✅ Sample data generated successfully")
        return True
    except ImportError:
        logger.warning("⚠️ Data generator not available, creating minimal data")
        return False
        
    except Exception as e:
        logger.error(f"❌ Error loading sample data: {e}")
        return False


def run_streamlit():
    """Launch production Streamlit application"""
    logger.info("🚀 Launching Streamlit application...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "true",
            "--theme.primaryColor", "#2E8B57",
            "--theme.backgroundColor", "#FFFFFF",
            "--theme.secondaryBackgroundColor", "#F8F9FA"
        ])
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to run application: {e}")

def main():
    """Main production entry point"""
    
    print("""
    🏥 AI Medical Scheduling Agent - PRODUCTION SYSTEM
    =================================================
    RagaAI Assignment - Industrial Grade Implementation
    
    Real Services • Real Data • Real Automation
    """)
    
    ensure_directories()
    
    if not check_environment():
        logger.error("❌ Environment configuration issues detected")
        return
    
    if not initialize_database():
        logger.error("❌ Database initialization failed")
        return
        
    load_sample_data()

    run_streamlit()


if __name__ == "__main__":
    main()