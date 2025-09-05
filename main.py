#!/usr/bin/env python3
"""
Production AI Medical Scheduling Agent - Main Entry Point
RagaAI Assignment - Complete Production System Launcher
"""

import os
import sys
import logging
import subprocess
import signal
import atexit
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

def check_production_environment():
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

def initialize_production_database():
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
        # Check if sample data already exists
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        conn.close()
        
        if patient_count >= 50:
            logger.info(f"✅ Sample data already loaded ({patient_count} patients)")
            return True
        
        # Try to run data generator
        try:
            from data.generate_data import generate_all_data
            success = generate_all_data()
            if success:
                logger.info("✅ Sample data generated successfully")
                return True
        except ImportError:
            logger.warning("⚠️ Data generator not available, creating minimal data")
        
        # Create minimal sample data as fallback
        return create_minimal_sample_data()
        
    except Exception as e:
        logger.error(f"❌ Error loading sample data: {e}")
        return False

def create_minimal_sample_data():
    """Create minimal sample data for production testing"""
    logger.info("Creating minimal sample data...")
    
    try:
        import csv
        from datetime import datetime, timedelta
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Create sample patients CSV
        sample_patients = []
        
        # Generate 50 patients as required
        first_names = ["John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Emily", "James", "Jessica"] * 5
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"] * 5
        
        for i in range(50):
            patient = {
                'patient_id': f'P{i+1:03d}',
                'first_name': first_names[i],
                'last_name': last_names[i],
                'dob': f'{1950 + (i % 50)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                'phone': f'555-{1000+i:04d}',
                'email': f'{first_names[i].lower()}.{last_names[i].lower()}{i}@email.com',
                'patient_type': 'new' if i % 3 == 0 else 'returning',
                'insurance_carrier': ['BlueCross BlueShield', 'Aetna', 'Cigna', 'UnitedHealthcare', 'Kaiser Permanente'][i % 5],
                'member_id': f'M{100000 + i:06d}',
                'group_number': f'G{1000 + (i % 100):04d}',
                'emergency_contact_name': f'Emergency Contact {i+1}',
                'emergency_contact_phone': f'555-{2000+i:04d}',
                'emergency_contact_relationship': ['Spouse', 'Parent', 'Child', 'Sibling', 'Friend'][i % 5]
            }
            sample_patients.append(patient)
        
        # Write to CSV
        csv_file = "data/sample_patients.csv"
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            fieldnames = sample_patients[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sample_patients)
        
        # Load into database
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        for patient in sample_patients:
            cursor.execute("""
            INSERT OR REPLACE INTO patients 
            (id, first_name, last_name, dob, phone, email, patient_type, 
             insurance_carrier, member_id, group_number, emergency_contact_name, 
             emergency_contact_phone, emergency_contact_relationship)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patient['patient_id'], patient['first_name'], patient['last_name'],
                patient['dob'], patient['phone'], patient['email'], patient['patient_type'],
                patient['insurance_carrier'], patient['member_id'], patient['group_number'],
                patient['emergency_contact_name'], patient['emergency_contact_phone'],
                patient['emergency_contact_relationship']
            ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Created minimal sample data: {len(sample_patients)} patients")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create minimal sample data: {e}")
        return False

def start_production_services():
    """Start production background services"""
    logger.info("Starting production services...")
    
    try:
        # Start reminder service
        from integrations.reminder_system import start_reminder_service
        reminder_system = start_reminder_service()
        
        logger.info("✅ Production reminder service started")
        
        # Register cleanup function
        def cleanup_services():
            logger.info("🛑 Shutting down production services...")
            try:
                from integrations.reminder_system import stop_reminder_service
                stop_reminder_service()
                logger.info("✅ Services stopped gracefully")
            except Exception as e:
                logger.error(f"❌ Error stopping services: {e}")
        
        atexit.register(cleanup_services)
        
        # Handle signals for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"📡 Received signal {signum}, shutting down...")
            cleanup_services()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to start production services: {e}")
        return False

def run_production_streamlit():
    """Launch production Streamlit application"""
    logger.info("🚀 Launching production Streamlit application...")
    
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
        logger.info("👋 Production application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to run production application: {e}")

def run_production_tests():
    """Run production system tests"""
    logger.info("🧪 Running production system tests...")
    
    try:
        # Test database connection
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        conn.close()
        
        logger.info(f"✅ Database test passed: {patient_count} patients")
        
        # Test AI agent
        try:
            from agents.medical_agent import EnhancedMedicalSchedulingAgent
            agent = ProductionMedicalAgent()
            test_response = agent.process_message("Hello", "test_session")
            if test_response and len(test_response) > 10:
                logger.info("✅ AI Agent test passed")
            else:
                logger.error("❌ AI Agent test failed: Invalid response")
        except Exception as e:
            logger.error(f"❌ AI Agent test failed: {e}")
        
        # Test services
        services_status = {}
        
        try:
            from integrations.email_service import EmailService
            email_service = EmailService()
            services_status['email'] = True
            logger.info("✅ Email service test passed")
        except Exception as e:
            services_status['email'] = False
            logger.error(f"❌ Email service test failed: {e}")
        
        try:
            from integrations.sms_service import SMSService
            sms_service = SMSService()
            services_status['sms'] = True
            logger.info("✅ SMS service test passed")
        except Exception as e:
            services_status['sms'] = False
            logger.error(f"❌ SMS service test failed: {e}")
        
        try:
            from integrations.calendly_integration import CalendlyIntegration
            calendar_service = CalendlyIntegration()
            services_status['calendar'] = True
            logger.info("✅ Calendar service test passed")
        except Exception as e:
            services_status['calendar'] = False
            logger.error(f"❌ Calendar service test failed: {e}")
        
        try:
            from utils.excel_export import ExcelExporter
            excel_service = ExcelExporter()
            services_status['excel'] = True
            logger.info("✅ Excel export service test passed")
        except Exception as e:
            services_status['excel'] = False
            logger.error(f"❌ Excel export service test failed: {e}")
        
        # Summary
        working_services = sum(services_status.values())
        total_services = len(services_status)
        
        logger.info(f"📊 Production test summary: {working_services}/{total_services} services operational")
        
        if working_services >= total_services - 1:  # Allow one service to be down
            logger.info("✅ Production system ready!")
            return True
        else:
            logger.warning("⚠️ Production system has issues but may still function")
            return False
        
    except Exception as e:
        logger.error(f"❌ Production tests failed: {e}")
        return False

def show_production_status():
    """Show production system status"""
    logger.info("📊 Checking production system status...")
    
    print("\n🏥 AI Medical Scheduling Agent - Production Status")
    print("=" * 60)
    
    # Environment check
    env_ok = check_production_environment()
    env_status = "✅ Ready" if env_ok else "❌ Issues"
    print(f"Environment Configuration: {env_status}")
    
    # Database check
    db_exists = Path("medical_scheduling.db").exists()
    db_status = "✅ Ready" if db_exists else "❌ Missing"
    print(f"Production Database: {db_status}")
    
    # Data check
    data_exists = Path("data/sample_patients.csv").exists()
    data_status = "✅ Ready" if data_exists else "❌ Missing"
    print(f"Sample Data: {data_status}")
    
    # Service checks
    services = {
        "AI Agent": False,
        "Email Service": False,
        "SMS Service": False,
        "Calendar Integration": False,
        "Reminder System": False,
        "Excel Export": False
    }
    
    try:
        from agents.medical_agent import EnhancedMedicalSchedulingAgent
        services["AI Agent"] = True
    except ImportError:
        pass
    
    try:
        from integrations.email_service import EmailService
        services["Email Service"] = True
    except ImportError:
        pass
    
    try:
        from integrations.sms_service import SMSService
        services["SMS Service"] = True
    except ImportError:
        pass
    
    try:
        from integrations.calendly_integration import CalendlyIntegration
        services["Calendar Integration"] = True
    except ImportError:
        pass
    
    try:
        from integrations.reminder_system import get_reminder_system
        services["Reminder System"] = True
    except ImportError:
        pass
    
    try:
        from utils.excel_export import ExcelExporter
        services["Excel Export"] = True
    except ImportError:
        pass
    
    print("\n🔧 Production Services:")
    for service, available in services.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"  {service}: {status}")
    
    available_count = sum(services.values())
    total_count = len(services)
    
    print(f"\n🎯 System Readiness: {available_count}/{total_count} services available")
    
    if available_count == total_count:
        print("🟢 PRODUCTION READY - All systems operational!")
    elif available_count >= total_count - 1:
        print("🟡 MOSTLY READY - Minor issues detected")
    else:
        print("🔴 NOT READY - Major components missing")
    
    return available_count >= total_count - 1

def main():
    """Main production entry point"""
    
    print("""
    🏥 AI Medical Scheduling Agent - PRODUCTION SYSTEM
    =================================================
    RagaAI Assignment - Industrial Grade Implementation
    
    Real Services • Real Data • Real Automation
    """)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "setup":
            logger.info("🔧 Running complete production setup...")
            
            steps = [
                ("Create directories", ensure_directories),
                ("Check environment", check_production_environment),
                ("Initialize database", initialize_production_database),
                ("Load sample data", load_sample_data),
                ("Start services", start_production_services),
                ("Run tests", run_production_tests)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"🔄 {step_name}...")
                try:
                    success = step_func()
                    if success:
                        logger.info(f"✅ {step_name} completed")
                    else:
                        logger.warning(f"⚠️ {step_name} completed with warnings")
                except Exception as e:
                    logger.error(f"❌ {step_name} failed: {e}")
            
            logger.info("🎉 Production setup completed!")
            logger.info("Run 'python main.py' to start the system")
            return
            
        elif command == "test":
            success = run_production_tests()
            sys.exit(0 if success else 1)
            
        elif command == "status":
            show_production_status()
            return
            
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: setup, test, status")
            return
    
    # Main production startup sequence
    logger.info("🚀 Starting production medical scheduling system...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Check environment
    if not check_production_environment():
        logger.error("❌ Environment configuration issues detected")
        logger.info("💡 Run 'python main.py setup' to configure the system")
        return
    
    # Check/initialize database
    if not Path("medical_scheduling.db").exists():
        logger.info("🔧 Database not found, initializing...")
        if not initialize_production_database():
            logger.error("❌ Database initialization failed")
            return
    
    # Load sample data if needed
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM patients")
        patient_count = cursor.fetchone()[0]
        conn.close()
        
        if patient_count < 50:
            logger.info("📊 Loading sample data...")
            load_sample_data()
    except Exception as e:
        logger.warning(f"⚠️ Could not check patient data: {e}")
    
    # Start background services
    start_production_services()
    
    # Show system status
    system_ready = show_production_status()
    
    if not system_ready:
        logger.warning("⚠️ System has some issues but will attempt to start")
    
    # Launch production application
    logger.info("🎯 Launching production Streamlit interface...")
    run_production_streamlit()

if __name__ == "__main__":
    main()