#!/usr/bin/env python3
"""
Local Development Runner for AI Medical Scheduling Agent
RagaAI Assignment - Development server with hot reload
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_environment():
    """Check development environment setup"""
    
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

def install_dependencies():
    """Install development dependencies"""
    
    logger.info("Installing dependencies...")
    
    try:
        # Install requirements
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        
        # Install development dependencies
        dev_packages = [
            "black",      # Code formatting
            "flake8",     # Code linting
            "pytest",     # Testing
            "pytest-cov" # Test coverage
        ]
        
        subprocess.check_call([
            sys.executable, "-m", "pip", "install"
        ] + dev_packages)
        
        logger.info("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to install dependencies: {e}")
        return False

def setup_data():
    """Generate sample data for development"""
    
    logger.info("Setting up sample data...")
    
    try:
        from data.generate_data import generate_all_data
        generate_all_data()
        logger.info("✅ Sample data generated successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to generate sample data: {e}")
        return False

def run_development_server():
    """Run Streamlit development server with hot reload"""
    
    logger.info("🚀 Starting development server with hot reload...")
    
    try:
        # Run Streamlit with development settings
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "ui/streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--server.runOnSave", "true",
            "--server.fileWatcherType", "auto",
            "--theme.primaryColor", "#2E8B57",
            "--theme.backgroundColor", "#FFFFFF", 
            "--theme.secondaryBackgroundColor", "#F8F9FA",
            "--theme.textColor", "#262730"
        ])
    except KeyboardInterrupt:
        logger.info("👋 Development server stopped by user")
    except Exception as e:
        logger.error(f"❌ Failed to run development server: {e}")

def run_tests():
    """Run test suite with coverage"""
    
    logger.info("🧪 Running test suite...")
    
    try:
        # Run tests with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/", 
            "-v",
            "--cov=agents",
            "--cov=database", 
            "--cov=integrations",
            "--cov=utils",
            "--cov-report=html",
            "--cov-report=term-missing"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
            
        if result.returncode == 0:
            logger.info("✅ All tests passed")
            logger.info("Coverage report generated in htmlcov/index.html")
        else:
            logger.error("❌ Some tests failed")
            
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        return False

def format_code():
    """Format code with Black"""
    
    logger.info("🎨 Formatting code with Black...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "black",
            "agents/", "database/", "integrations/", "ui/", "utils/", "tests/",
            "--line-length", "88"
        ])
        logger.info("✅ Code formatted successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Code formatting failed: {e}")
        return False

def lint_code():
    """Lint code with flake8"""
    
    logger.info("🔍 Linting code with flake8...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "flake8",
            "agents/", "database/", "integrations/", "ui/", "utils/",
            "--max-line-length", "88",
            "--extend-ignore", "E203,W503"
        ], capture_output=True, text=True)
        
        if result.stdout:
            print("Linting issues:")
            print(result.stdout)
            
        if result.returncode == 0:
            logger.info("✅ No linting issues found")
        else:
            logger.warning("⚠️ Linting issues found (see above)")
            
        return result.returncode == 0
        
    except Exception as e:
        logger.error(f"❌ Code linting failed: {e}")
        return False

def docker_build():
    """Build Docker image locally"""
    
    logger.info("🐳 Building Docker image...")
    
    try:
        subprocess.run([
            "docker", "build",
            "-t", "medical-scheduling-agent:dev",
            "."
        ], check=True)
        
        logger.info("✅ Docker image built successfully")
        logger.info("Run with: docker run -p 8501:8501 medical-scheduling-agent:dev")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Docker build failed: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ Docker not found. Please install Docker first.")
        return False

def docker_run():
    """Run Docker container locally"""
    
    logger.info("🐳 Running Docker container...")
    
    try:
        # Load environment variables for Docker
        env_vars = []
        load_dotenv()
        
        # Add API key if available
        if os.getenv("GOOGLE_API_KEY"):
            env_vars.extend(["-e", f"GOOGLE_API_KEY={os.getenv('GOOGLE_API_KEY')}"])
        
        # Add optional environment variables
        optional_vars = ["SENDGRID_API_KEY", "TWILIO_SID", "TWILIO_TOKEN"]
        for var in optional_vars:
            value = os.getenv(var)
            if value:
                env_vars.extend(["-e", f"{var}={value}"])
        
        # Run container
        cmd = [
            "docker", "run",
            "-p", "8501:8501",
            "--name", "medical-agent-dev"
        ] + env_vars + ["medical-scheduling-agent:dev"]
        
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Docker run failed: {e}")
        return False
    except FileNotFoundError:
        logger.error("❌ Docker not found. Please install Docker first.")
        return False

def main():
    """Main development runner"""
    
    print("""
    🏥 AI Medical Scheduling Agent - Development Server
    ==================================================
    RagaAI Assignment - Local Development Environment
    
    Available Commands:
    • python run_local.py          → Start development server
    • python run_local.py test     → Run test suite  
    • python run_local.py format   → Format code with Black
    • python run_local.py lint     → Lint code with flake8
    • python run_local.py docker   → Build & run Docker
    • python run_local.py setup    → Full development setup
    """)
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            success = run_tests()
            sys.exit(0 if success else 1)
            
        elif command == "format":
            format_code()
            return
            
        elif command == "lint":
            lint_code()
            return
            
        elif command == "docker":
            if docker_build():
                docker_run()
            return
            
        elif command == "setup":
            logger.info("🔧 Setting up development environment...")
            
            steps = [
                ("Check environment", check_environment),
                ("Install dependencies", install_dependencies), 
                ("Setup sample data", setup_data),
                ("Format code", format_code),
                ("Run tests", run_tests)
            ]
            
            for step_name, step_func in steps:
                logger.info(f"Running: {step_name}")
                if not step_func():
                    logger.error(f"❌ Failed at: {step_name}")
                    return
                    
            logger.info("✅ Development setup complete!")
            logger.info("Run 'python run_local.py' to start the server")
            return
            
        else:
            logger.error(f"Unknown command: {command}")
            return
    
    # Default: run development server
    logger.info("Starting development workflow...")
    
    # Quick checks
    if not check_environment():
        logger.error("Please run 'python run_local.py setup' first")
        return
    
    # Ensure sample data exists
    if not Path('data/sample_patients.csv').exists():
        logger.info("Generating sample data...")
        if not setup_data():
            logger.error("Failed to generate sample data")
            return
    
    # Start development server
    run_development_server()

if __name__ == "__main__":
    main()