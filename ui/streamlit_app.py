"""
Fully Functional Streamlit Application for AI Medical Scheduling Agent - FIXED
RagaAI Assignment - All Features Working (Import Error Fixed)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import logging
import sys
import os
import json
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="MediCare AI Scheduling",
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import components with proper error handling
AGENT_AVAILABLE = False
GENERATOR_AVAILABLE = False

try:
    from agents.medical_agent import EnhancedMedicalSchedulingAgent
    from database.database import DatabaseManager
    from utils.excel_export import ExcelExporter
    AGENT_AVAILABLE = True
    logger.info("✅ Core components loaded successfully")
except ImportError as e:
    logger.error(f"Core component import error: {e}")

try:
    from integrations.reminder_system import get_reminder_system
    REMINDER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Reminder system not available: {e}")
    REMINDER_AVAILABLE = False

try:
    from data.generate_data import generate_all_data
    GENERATOR_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Data generator not available: {e}")
    GENERATOR_AVAILABLE = False

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57 0%, #3CB371 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #3CB371;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .workflow-step-active {
        background: #2E8B57; 
        color: white; 
        padding: 0.8rem; 
        border-radius: 10px; 
        text-align: center; 
        margin: 0.2rem;
        font-weight: bold;
    }
    .workflow-step-inactive {
        background: #f8f9fa; 
        color: #6c757d; 
        padding: 0.8rem;
        border-radius: 10px; 
        text-align: center; 
        border: 1px solid #dee2e6;
        margin: 0.2rem;
    }
    .system-status-good {
        color: #28a745;
        font-weight: bold;
    }
    .system-status-bad {
        color: #dc3545;
        font-weight: bold;
    }
    .setup-instructions {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def create_sample_data_fallback():
    """Create minimal sample data as fallback when generator is not available"""
    try:
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        # Create minimal CSV if it doesn't exist
        csv_path = Path("data/sample_patients.csv")
        if not csv_path.exists():
            # Create basic CSV structure
            sample_data = {
                'patient_id': [f'P{i:03d}' for i in range(1, 11)],
                'first_name': ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Mark', 'Anna', 'Chris', 'Maria'],
                'last_name': ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'],
                'dob': ['1985-03-15', '1990-07-22', '1975-11-08', '1988-01-30', '1992-05-12', 
                        '1980-09-18', '1987-12-03', '1995-04-25', '1983-08-07', '1991-10-14'],
                'phone': [f'555-{1000+i:04d}' for i in range(10)],
                'email': [f'patient{i}@email.com' for i in range(1, 11)],
                'patient_type': ['new', 'returning'] * 5,
                'insurance_carrier': ['BlueCross BlueShield', 'Aetna', 'Cigna', 'UnitedHealthcare', 'Kaiser Permanente'] * 2,
                'member_id': [f'M{i:06d}' for i in range(100000, 100010)],
                'group_number': [f'G{i:04d}' for i in range(1000, 1010)],
                'emergency_contact_name': [f'Emergency Contact {i}' for i in range(1, 11)],
                'emergency_contact_phone': [f'555-{2000+i:04d}' for i in range(10)],
                'emergency_contact_relationship': ['Spouse', 'Parent', 'Child', 'Sibling', 'Friend'] * 2
            }
            
            df = pd.DataFrame(sample_data)
            df.to_csv(csv_path, index=False)
            logger.info("✅ Created fallback sample data")
            return True
            
    except Exception as e:
        logger.error(f"Failed to create fallback data: {e}")
        return False

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent with error handling"""
    if not AGENT_AVAILABLE or EnhancedMedicalSchedulingAgent is None:
        return None
    
    try:
        # Ensure sample data exists
        if not Path("data/sample_patients.csv").exists():
            if GENERATOR_AVAILABLE:
                logger.info("Generating sample data...")
                generate_all_data()
            else:
                logger.info("Creating fallback sample data...")
                create_sample_data_fallback()
        
        # Initialize agent
        agent = EnhancedMedicalSchedulingAgent()
        logger.info("✅ AI Agent initialized successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        return None

def safe_database_stats():
    """Get database statistics with error handling"""
    try:
        if not AGENT_AVAILABLE:
            return {"total_patients": 0, "new_patients": 0, "returning_patients": 0, "upcoming_appointments": 0}
        
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Get patient counts
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_type = 'new'")
        new_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_type = 'returning'")
        returning_patients = cursor.fetchone()[0]
        
        # Get appointments if table exists
        try:
            cursor.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_datetime) >= DATE('now')")
            upcoming_appointments = cursor.fetchone()[0]
        except:
            upcoming_appointments = 0
        
        conn.close()
        
        return {
            "total_patients": total_patients,
            "new_patients": new_patients,
            "returning_patients": returning_patients,
            "upcoming_appointments": upcoming_appointments
        }
    except Exception as e:
        logger.error(f"Database stats error: {e}")
        return {"total_patients": 0, "new_patients": 0, "returning_patients": 0, "upcoming_appointments": 0}

def initialize_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_patient" not in st.session_state:
        st.session_state.current_patient = None
    if "workflow_step" not in st.session_state:
        st.session_state.workflow_step = "greeting"
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"session_{int(datetime.now().timestamp())}"
    if "appointment_data" not in st.session_state:
        st.session_state.appointment_data = None

def render_header():
    """Render main header"""
    st.markdown("""
    <div class="main-header">
        <h1>🏥 MediCare Allergy & Wellness Center</h1>
        <h3>AI-Powered Medical Scheduling Assistant</h3>
        <p>456 Healthcare Boulevard, Suite 300 | Phone: (555) 123-4567</p>
    </div>
    """, unsafe_allow_html=True)

def render_system_status():
    """Render comprehensive system status"""
    st.subheader("🔧 System Status & Setup")
    
    # Check system components
    checks = {
        "Environment File (.env)": Path(".env").exists(),
        "Google API Key": bool(os.getenv("GOOGLE_API_KEY")),
        "Database File": Path("medical_scheduling.db").exists(),
        "Sample Data": Path("data/sample_patients.csv").exists(),
        "AI Agent Components": AGENT_AVAILABLE,
        "Data Generator": GENERATOR_AVAILABLE,
        "Reminder System": REMINDER_AVAILABLE,
        "Exports Directory": Path("exports").exists()
    }
    
    # Display status grid
    col1, col2 = st.columns(2)
    items = list(checks.items())
    mid_point = len(items) // 2
    
    with col1:
        for check_name, status in items[:mid_point]:
            status_class = "system-status-good" if status else "system-status-bad"
            status_text = "✅ Ready" if status else "❌ Missing"
            st.markdown(f'<p class="{status_class}">{check_name}: {status_text}</p>', unsafe_allow_html=True)
    
    with col2:
        for check_name, status in items[mid_point:]:
            status_class = "system-status-good" if status else "system-status-bad"
            status_text = "✅ Ready" if status else "❌ Missing"
            st.markdown(f'<p class="{status_class}">{check_name}: {status_text}</p>', unsafe_allow_html=True)
    
    # Overall system readiness
    ready_count = sum(checks.values())
    total_count = len(checks)
    readiness_percentage = (ready_count / total_count) * 100
    
    st.progress(readiness_percentage / 100)
    st.markdown(f"**System Readiness: {readiness_percentage:.0f}% ({ready_count}/{total_count} components ready)**")
    
    return readiness_percentage >= 50  # System is usable if 50%+ ready

def render_setup_instructions():
    """Render setup instructions"""
    st.markdown("""
    <div class="setup-instructions">
        <h3>🚀 Setup Instructions</h3>
        <p>To get the full system running, follow these steps:</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📋 Complete Setup Guide", expanded=True):
        st.markdown("""
        ### Step 1: Install Dependencies
        ```bash
        pip install -r requirements.txt
        ```
        
        ### Step 2: Environment Configuration
        ```bash
        # Copy environment template
        cp .env.example .env
        
        # Edit .env and add your Google API key
        GOOGLE_API_KEY=your_gemini_api_key_here
        ```
        
        ### Step 3: Run System Setup
        ```bash
        python main.py setup
        ```
        
        ### Step 4: Start Application
        ```bash
        python main.py
        # OR
        streamlit run ui/streamlit_app.py
        ```
        
        ### Alternative: Quick Docker Setup
        ```bash
        docker-compose up --build
        ```
        """)

def render_quick_setup():
    """Render quick setup interface"""
    st.subheader("⚡ Quick Setup")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📁 Create Directories"):
            try:
                for dir_name in ["data", "exports", "logs"]:
                    Path(dir_name).mkdir(exist_ok=True)
                st.success("Directories created!")
            except Exception as e:
                st.error(f"Failed: {e}")
    
    with col2:
        if st.button("📊 Generate Sample Data"):
            try:
                if GENERATOR_AVAILABLE:
                    generate_all_data()
                else:
                    create_sample_data_fallback()
                st.success("Sample data generated!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
    
    with col3:
        if st.button("🗄️ Initialize Database"):
            try:
                if AGENT_AVAILABLE:
                    db = DatabaseManager()
                    st.success("Database initialized!")
                else:
                    st.warning("Database components not available")
            except Exception as e:
                st.error(f"Failed: {e}")
    
    with col4:
        if st.button("🔄 Full Reset"):
            try:
                # Remove database
                if Path("medical_scheduling.db").exists():
                    Path("medical_scheduling.db").unlink()
                
                # Recreate data
                if GENERATOR_AVAILABLE:
                    generate_all_data()
                else:
                    create_sample_data_fallback()
                
                # Reinitialize database
                if AGENT_AVAILABLE:
                    db = DatabaseManager()
                
                st.success("System reset complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Reset failed: {e}")

def render_chat_interface():
    """Render chat interface with graceful degradation"""
    st.subheader("💬 Chat with AI Assistant")
    
    # Check if agent is available
    if not AGENT_AVAILABLE:
        st.warning("⚠️ AI Agent not available. Please install dependencies and run setup.")
        render_setup_instructions()
        return
    
    # Get agent
    agent = get_agent()
    if not agent:
        st.error("❌ Failed to initialize AI agent.")
        st.info("Try running the setup steps above to resolve this issue.")
        return
    
    # Display conversation
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.now().isoformat()
        })
        
        # Show user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Process with AI agent
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processing your request..."):
                try:
                    # Call actual AI agent
                    response = agent.process_message(prompt, st.session_state.session_id)
                    
                    # Display response
                    st.markdown(response)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Update session state from agent
                    agent_state = agent.get_session_state(st.session_state.session_id)
                    if agent_state:
                        st.session_state.workflow_step = agent_state.get("current_step", "greeting")
                        if agent_state.get("current_patient"):
                            st.session_state.current_patient = agent_state["current_patient"]
                        if agent_state.get("appointment_info"):
                            st.session_state.appointment_data = agent_state["appointment_info"]
                    
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"Chat processing error: {e}")
                    st.error(f"Error processing message: {str(e)}")
                    st.info("Please check your system setup and API configuration.")

def render_analytics_with_fallback():
    """Render analytics with fallback for missing data"""
    st.subheader("📊 Analytics Dashboard")
    
    # Get statistics
    stats = safe_database_stats()
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Patients</h3>
            <h2>{stats['total_patients']}</h2>
            <p>In database</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🆕 New Patients</h3>
            <h2>{stats['new_patients']}</h2>
            <p>60-minute appointments</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>🔄 Returning Patients</h3>
            <h2>{stats['returning_patients']}</h2>
            <p>30-minute appointments</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📅 Scheduled</h3>
            <h2>{stats['upcoming_appointments']}</h2>
            <p>Upcoming appointments</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Show charts if data is available
    if Path("data/sample_patients.csv").exists():
        try:
            df = pd.read_csv("data/sample_patients.csv")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Patient Type Distribution")
                patient_counts = df['patient_type'].value_counts()
                fig = px.pie(values=patient_counts.values, names=patient_counts.index, 
                            title="New vs Returning Patients")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("🏥 Insurance Carriers")
                insurance_counts = df['insurance_carrier'].value_counts().head(5)
                fig2 = px.bar(x=insurance_counts.index, y=insurance_counts.values,
                             title="Top Insurance Carriers")
                st.plotly_chart(fig2, use_container_width=True)
                
        except Exception as e:
            st.warning(f"Unable to load analytics data: {e}")
    else:
        st.info("📊 Analytics will be available after sample data is generated.")

def main():
    """Main application with robust error handling"""
    initialize_session_state()
    render_header()
    
    # Check overall system status
    system_ready = render_system_status()
    
    if not system_ready:
        st.warning("⚠️ System requires setup to function fully.")
        render_quick_setup()
        
        # Show what's available anyway
        st.info("Some features may be available even without full setup:")
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🗣️ Schedule Appointment", "📊 Analytics", "⚙️ System"])
    
    with tab1:
        if system_ready:
            render_chat_interface()
        else:
            st.warning("Chat interface requires system setup.")
            render_setup_instructions()
    
    with tab2:
        render_analytics_with_fallback()
    
    with tab3:
        st.subheader("⚙️ System Management")
        render_system_status()
        st.divider()
        render_quick_setup()
        
        if st.button("🔍 Run System Diagnostics"):
            st.text("🔍 Running diagnostics...")
            
            diagnostics = {
                "Python Version": sys.version,
                "Working Directory": str(Path.cwd()),
                "Environment Variables": len([k for k in os.environ.keys() if k.startswith(('GOOGLE_', 'SENDGRID_', 'TWILIO_'))]),
                "Available Modules": f"Agent: {AGENT_AVAILABLE}, Generator: {GENERATOR_AVAILABLE}, Reminders: {REMINDER_AVAILABLE}"
            }
            
            for key, value in diagnostics.items():
                st.text(f"{key}: {value}")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        🏥 MediCare AI Scheduling Agent | RagaAI Assignment<br>
        System Status: {'🟢 Ready' if system_ready else '🟡 Setup Required'} | 
        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()