#!/usr/bin/env python3
"""
AI Medical Scheduling Agent - Main Entry Point (Fixed)
RagaAI Assignment - Robust Healthcare Booking System with Error Handling
"""

import os
import sys
import logging
import subprocess
import signal
import atexit
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check if environment is properly configured"""
    
    # Load environment variables
    load_dotenv()
    
    # Check if .env exists
    if not Path('.env').exists():
        logger.warning(".env file not found")
        if Path('.env.example').exists():
            logger.info("Copying .env.example to .env")
            import shutil
            shutil.copy('.env.example', '.env')
            logger.warning("Please update .env with your API keys")
        return False
    
    # Check required API key
    if not os.getenv("GOOGLE_API_KEY"):
        logger.error("GOOGLE_API_KEY not found in .env")
        logger.info("Please add your Gemini Pro API key to .env file")
        return False
    
    logger.info("✅ Environment configuration verified")
    return True

def setup_data_fallback():
    """Generate minimal sample data as fallback"""
    
    logger.info("Setting up minimal sample data...")
    
    try:
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Try to import the full generator first
        try:
            from data.generate_data import generate_all_data
            generate_all_data()
            logger.info("✅ Full sample data generated successfully")
            return True
        except ImportError:
            logger.info("Data generator not available, creating minimal data...")
            
            # Create minimal CSV as fallback
            import csv
            csv_data = [
                ["patient_id", "first_name", "last_name", "dob", "phone", "email", "patient_type", "insurance_carrier", "member_id", "group_number", "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship"],
                ["P001", "John", "Smith", "1985-03-15", "555-1001", "john.smith@email.com", "new", "BlueCross BlueShield", "M123456", "G1001", "Jane Smith", "555-2001", "Spouse"],
                ["P002", "Jane", "Doe", "1990-07-22", "555-1002", "jane.doe@email.com", "returning", "Aetna", "M123457", "G1002", "John Doe", "555-2002", "Spouse"],
                ["P003", "Mike", "Johnson", "1975-11-08", "555-1003", "mike.johnson@email.com", "returning", "Cigna", "M123458", "G1003", "Sarah Johnson", "555-2003", "Spouse"],
                ["P004", "Sarah", "Williams", "1988-01-30", "555-1004", "sarah.williams@email.com", "new", "UnitedHealthcare", "M123459", "G1004", "Mike Williams", "555-2004", "Spouse"],
                ["P005", "David", "Brown", "1992-05-12", "555-1005", "david.brown@email.com", "returning", "Kaiser Permanente", "M123460", "G1005", "Lisa Brown", "555-2005", "Spouse"]
            ]
            
            with open("data/sample_patients.csv", "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerows(csv_data)
            
            logger.info("✅ Minimal sample data created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Failed to setup sample data: {e}")
        return False

def setup_database():
    """Setup database if components are available"""
    
    logger.info("Setting up database...")
    
    try:
        # Try to initialize database
        from database.database import DatabaseManager
        db = DatabaseManager()  # This initializes basic tables
        
        # Try to run reminder system migrations
        try:
            from database.migrations import run_reminder_system_migrations
            run_reminder_system_migrations()
            logger.info("✅ Database setup completed with reminder system")
        except ImportError:
            logger.info("✅ Basic database setup completed (reminder system not available)")
        
        return True
    except ImportError:
        logger.warning("⚠️ Database components not available - will work in limited mode")
        return True
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False

def start_reminder_service():
    """Start the automated reminder service if available"""
    
    try:
        from integrations.reminder_system import start_reminder_service
        reminder_system = start_reminder_service()
        
        logger.info("✅ Automated reminder service started successfully")
        
        # Register cleanup function
        def cleanup_reminder_service():
            logger.info("Stopping reminder service...")
            try:
                from integrations.reminder_system import stop_reminder_service
                stop_reminder_service()
                logger.info("✅ Reminder service stopped")
            except Exception as e:
                logger.error(f"Error stopping reminder service: {e}")
        
        atexit.register(cleanup_reminder_service)
        
        # Handle signals for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            cleanup_reminder_service()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        return reminder_system
        
    except ImportError:
        logger.warning("⚠️ Reminder system not available")
        return None
    except Exception as e:
        logger.error(f"❌ Failed to start reminder service: {e}")
        return None

def run_streamlit_app():
    """Launch the Streamlit demo interface"""
    
    logger.info("🚀 Launching AI Medical Scheduling Agent...")
    
    try:
        # Run Streamlit app
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost"
        ])
    except KeyboardInterrupt:
        logger.info("👋 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to run application: {e}")

def run_tests():
    """Run the test suite if available"""
    
    logger.info("🧪 Running tests...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", "tests/", "-v"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
        return result.returncode == 0
    except FileNotFoundError:
        logger.warning("⚠️ pytest not available - skipping tests")
        return True
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

def show_system_status():
    """Show current system status"""
    
    logger.info("📊 Checking system status...")
    
    print("\n🎯 AI Medical Scheduling Agent - System Status")
    print("=" * 50)
    
    # Check environment
    env_status = "✅ Ready" if check_environment() else "❌ Needs Configuration"
    print(f"Environment: {env_status}")
    
    # Check data
    data_exists = Path("data/sample_patients.csv").exists()
    data_status = "✅ Ready" if data_exists else "❌ Not Generated"
    print(f"Sample Data: {data_status}")
    
    # Check database
    db_exists = Path("medical_scheduling.db").exists()
    db_status = "✅ Ready" if db_exists else "❌ Not Initialized"
    print(f"Database: {db_status}")
    
    # Check components
    components = {
        "AI Agent": False,
        "Data Generator": False,
        "Reminder System": False,
        "Excel Export": False,
        "Streamlit": False
    }
    
    try:
        # Try multiple possible agent class names
        try:
            from agents.medical_agent import EnhancedMedicalSchedulingAgent
            components["AI Agent"] = True
        except ImportError:
            try:
                from agents.medical_agent import MedicalSchedulingAgent
                components["AI Agent"] = True
            except ImportError:
                # Check if any agent class exists
                import agents.medical_agent as agent_module
                for attr_name in dir(agent_module):
                    attr = getattr(agent_module, attr_name)
                    if (isinstance(attr, type) and 
                        'agent' in attr_name.lower() and 
                        attr_name != 'Agent'):
                        components["AI Agent"] = True
                        break
    except ImportError:
        pass
    
    try:
        from data.generate_data import generate_all_data
        components["Data Generator"] = True
    except ImportError:
        pass
    
    try:
        from integrations.reminder_system import get_reminder_system
        components["Reminder System"] = True
    except ImportError:
        pass
    
    try:
        from utils.excel_export import ExcelExporter
        components["Excel Export"] = True
    except ImportError:
        pass
    
    try:
        import streamlit
        components["Streamlit"] = True
    except ImportError:
        pass
    
    print("\n🔧 Component Status:")
    for component, available in components.items():
        status = "✅ Available" if available else "❌ Missing"
        print(f"  {component}: {status}")
    
    available_count = sum(components.values())
    total_count = len(components)
    
    print(f"\n🎯 System Readiness: {available_count}/{total_count} components available")
    
    if available_count >= 3:
        print("🟢 System ready for demo!")
    elif available_count >= 1:
        print("🟡 Limited functionality available")
    else:
        print("🔴 System needs setup")
    
    return available_count >= 1

def main():
    """Main application entry point with robust error handling"""
    
    print("""
    🏥 AI Medical Scheduling Agent - RagaAI Assignment
    =================================================
    
    Starting system with error handling and graceful degradation...
    """)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            success = run_tests()
            sys.exit(0 if success else 1)
            
        elif command == "setup":
            logger.info("Running complete system setup...")
            steps = [
                ("Environment check", check_environment),
                ("Database setup", setup_database),
                ("Sample data generation", setup_data_fallback)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"Running: {step_name}")
                if not step_func():
                    logger.warning(f"⚠️ {step_name} completed with warnings")
                    
            logger.info("✅ Setup completed!")
            logger.info("Run 'python main.py' to start the application")
            return
            
        elif command == "status":
            show_system_status()
            return
            
        else:
            logger.error(f"Unknown command: {command}")
            logger.info("Available commands: setup, test, status")
            return
    
    # Main application startup sequence
    logger.info("Starting medical scheduling system...")
    
    # 1. Check environment
    if not check_environment():
        logger.warning("⚠️ Environment issues detected, but continuing...")
    
    # 2. Setup data if needed
    if not Path('data/sample_patients.csv').exists():
        logger.info("Sample data not found, generating...")
        if not setup_data_fallback():
            logger.error("❌ Failed to setup sample data")
            logger.info("Try running 'python main.py setup' first")
            return
    
    # 3. Setup database if needed
    if not Path("medical_scheduling.db").exists():
        logger.info("Database not found, initializing...")
        setup_database()
    
    # 4. Try to start reminder service
    start_reminder_service()
    
    # 5. Show system status
    if not show_system_status():
        logger.warning("⚠️ System has limited functionality")
        logger.info("Run 'python setup.py' for complete setup")
    
    # 6. Launch Streamlit application
    logger.info("🎯 Starting Streamlit application...")
    run_streamlit_app()

if __name__ == "__main__":
    main()