#!/usr/bin/env python3
"""
Quick Setup Script for AI Medical Scheduling Agent
RagaAI Assignment - Automated System Setup
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        logger.error("Python 3.8+ is required")
        return False
    logger.info(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def install_dependencies():
    """Install required dependencies"""
    logger.info("Installing dependencies...")
    
    try:
        # Install basic requirements
        basic_packages = [
            "streamlit",
            "pandas", 
            "plotly",
            "python-dotenv",
            "openpyxl"
        ]
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade", "pip"
        ])
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + basic_packages)
        
        logger.info("✅ Basic dependencies installed")
        
        # Try to install AI dependencies
        try:
            ai_packages = [
                "langchain",
                "langchain-google-genai", 
                "langgraph"
            ]
            
            subprocess.check_call([
                sys.executable, "-m", "pip", "install"
            ] + ai_packages)
            
            logger.info("✅ AI dependencies installed")
            
        except subprocess.CalledProcessError:
            logger.warning("⚠️ AI dependencies failed to install - will run in limited mode")
        
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def setup_environment():
    """Setup environment configuration"""
    logger.info("Setting up environment...")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.example").exists():
            shutil.copy(".env.example", ".env")
            logger.info("✅ Created .env from template")
        else:
            # Create basic .env file
            with open(".env", "w") as f:
                f.write("# AI Medical Scheduling Agent Configuration\n")
                f.write("# Add your Google Gemini API key below:\n")
                f.write("GOOGLE_API_KEY=your_api_key_here\n")
                f.write("\n# Optional services:\n")
                f.write("# SENDGRID_API_KEY=your_sendgrid_key\n")
                f.write("# TWILIO_SID=your_twilio_sid\n")
                f.write("# TWILIO_TOKEN=your_twilio_token\n")
            
            logger.info("✅ Created basic .env file")
        
        logger.warning("⚠️ Please edit .env file and add your Google API key")
    else:
        logger.info("✅ .env file already exists")
    
    return True

def create_directories():
    """Create necessary directories"""
    logger.info("Creating directories...")
    
    directories = ["data", "exports", "logs", "forms"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        
        # Create .gitkeep files for empty directories
        gitkeep_file = Path(directory) / ".gitkeep"
        if not gitkeep_file.exists():
            with open(gitkeep_file, "w") as f:
                f.write("# Keep directory in git\n")
    
    logger.info("✅ Directories created")
    return True

def create_sample_data():
    """Create minimal sample data"""
    logger.info("Creating sample data...")
    
    try:
        # Try to import and use the full generator
        from data.generate_data import generate_all_data
        generate_all_data()
        logger.info("✅ Full sample data generated")
        return True
        
    except ImportError:
        logger.info("Using fallback data generation...")
        
        # Create minimal CSV data
        import csv
        
        sample_patients = [
            ["patient_id", "first_name", "last_name", "dob", "phone", "email", "patient_type", "insurance_carrier", "member_id", "group_number", "emergency_contact_name", "emergency_contact_phone", "emergency_contact_relationship"],
            ["P001", "John", "Smith", "1985-03-15", "555-1001", "john.smith@email.com", "new", "BlueCross BlueShield", "M123456", "G1001", "Jane Smith", "555-2001", "Spouse"],
            ["P002", "Jane", "Doe", "1990-07-22", "555-1002", "jane.doe@email.com", "returning", "Aetna", "M123457", "G1002", "John Doe", "555-2002", "Spouse"],
            ["P003", "Mike", "Johnson", "1975-11-08", "555-1003", "mike.johnson@email.com", "returning", "Cigna", "M123458", "G1003", "Sarah Johnson", "555-2003", "Spouse"],
            ["P004", "Sarah", "Williams", "1988-01-30", "555-1004", "sarah.williams@email.com", "new", "UnitedHealthcare", "M123459", "G1004", "Mike Williams", "555-2004", "Spouse"],
            ["P005", "David", "Brown", "1992-05-12", "555-1005", "david.brown@email.com", "returning", "Kaiser Permanente", "M123460", "G1005", "Lisa Brown", "555-2005", "Spouse"]
        ]
        
        csv_file = Path("data/sample_patients.csv")
        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(sample_patients)
        
        logger.info("✅ Fallback sample data created")
        return True

def setup_database():
    """Setup database if possible"""
    logger.info("Setting up database...")
    
    try:
        from database.database import DatabaseManager
        db = DatabaseManager()
        logger.info("✅ Database initialized")
        return True
        
    except ImportError:
        logger.warning("⚠️ Database components not available - will create when AI components are installed")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Database setup failed: {e}")
        return True

def test_streamlit():
    """Test if Streamlit can run"""
    logger.info("Testing Streamlit...")
    
    try:
        import streamlit
        logger.info("✅ Streamlit is available")
        return True
    except ImportError:
        logger.error("❌ Streamlit not available")
        return False

def main():
    """Main setup function"""
    print("""
    🏥 AI Medical Scheduling Agent - Quick Setup
    ===========================================
    RagaAI Assignment - Automated System Setup
    
    This script will set up your system for the medical scheduling agent.
    """)
    
    # Run setup steps
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Setting up environment", setup_environment),
        ("Creating directories", create_directories),
        ("Creating sample data", create_sample_data),
        ("Setting up database", setup_database),
        ("Testing Streamlit", test_streamlit)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n🔄 {step_name}...")
        try:
            if step_func():
                success_count += 1
            else:
                logger.warning(f"⚠️ {step_name} completed with warnings")
        except Exception as e:
            logger.error(f"❌ {step_name} failed: {e}")
    
    print(f"\n📊 Setup Results: {success_count}/{len(steps)} steps completed successfully")
    
    if success_count >= len(steps) - 1:  # Allow for one failure
        print("""
        ✅ Setup completed successfully!
        
        🚀 Next Steps:
        1. Edit .env file and add your Google API key
        2. Run the application:
           
           streamlit run ui/streamlit_app.py
           
           OR
           
           python main.py
        
        🎯 The system is ready for the RagaAI assignment demo!
        """)
        
        # Ask if user wants to start the app now
        try:
            response = input("\nWould you like to start the Streamlit app now? (y/N): ")
            if response.lower() in ['y', 'yes']:
                print("🚀 Starting Streamlit app...")
                subprocess.run([
                    sys.executable, "-m", "streamlit", "run", 
                    "ui/streamlit_app.py",
                    "--server.port", "8501"
                ])
        except KeyboardInterrupt:
            print("\n👋 Setup complete! Run 'streamlit run ui/streamlit_app.py' when ready.")
    
    else:
        print("""
        ⚠️ Setup completed with some issues.
        
        The system may still work in limited mode. Try running:
        streamlit run ui/streamlit_app.py
        
        Check the error messages above and install missing dependencies.
        """)

if __name__ == "__main__":
    main()