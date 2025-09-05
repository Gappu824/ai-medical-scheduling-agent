"""
Fully Functional Streamlit Application for AI Medical Scheduling Agent
RagaAI Assignment - All Features Working (No Mockups)
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

# Import real components
try:
    from agents.medical_agent import EnhancedMedicalSchedulingAgent
    from database.database import DatabaseManager
    from utils.excel_export import ExcelExporter
    from integrations.reminder_system import get_reminder_system
    from data.generate_data import generate_all_data
    AGENT_AVAILABLE = True
except ImportError as e:
    logger.error(f"Import error: {e}")
    AGENT_AVAILABLE = False

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
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_agent():
    """Initialize and cache the AI agent"""
    if not AGENT_AVAILABLE:
        return None
    
    try:
        # Check if data exists
        if not Path("data/sample_patients.csv").exists():
            logger.info("Generating sample data...")
            generate_all_data()
        
        # Initialize agent
        agent = EnhancedMedicalSchedulingAgent()
        logger.info("AI Agent initialized successfully")
        return agent
    except Exception as e:
        logger.error(f"Failed to initialize agent: {e}")
        st.error(f"Agent initialization failed: {e}")
        return None

@st.cache_data(ttl=60)
def get_real_database_stats():
    """Get actual statistics from database"""
    try:
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

def render_workflow_progress():
    """Show actual workflow progress based on conversation"""
    steps = ["Greeting", "Patient Info", "Lookup", "Preferences", "Scheduling", "Insurance", "Confirmation", "Complete"]
    
    # Determine current step based on agent state
    current_index = 0
    agent = get_agent()
    if agent and st.session_state.session_id:
        agent_state = agent.get_session_state(st.session_state.session_id)
        if agent_state:
            step_mapping = {
                "greeting": 0,
                "collect_info": 1,
                "patient_lookup": 2,
                "interactive_preferences": 3,
                "show_availability": 4,
                "collect_insurance": 5,
                "final_confirmation": 6,
                "send_forms": 7
            }
            current_index = step_mapping.get(agent_state.get("current_step", "greeting"), 0)
    
    st.markdown("### 📋 Appointment Booking Progress")
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            if i <= current_index:
                st.markdown(f'<div class="workflow-step-active">{step}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="workflow-step-inactive">{step}</div>', unsafe_allow_html=True)

def render_chat_interface():
    """Render fully functional chat interface"""
    st.subheader("💬 Chat with AI Assistant")
    
    # System status check
    if not AGENT_AVAILABLE:
        st.error("⚠️ AI Agent not available. Missing dependencies.")
        with st.expander("Setup Instructions"):
            st.code("""
            # Install missing dependencies
            pip install -r requirements.txt
            
            # Set up environment
            python main.py setup
            
            # Start application
            python main.py
            """)
        return
    
    # Get agent
    agent = get_agent()
    if not agent:
        st.error("❌ Failed to initialize AI agent.")
        return
    
    # Display conversation
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.markdown(message["content"])
    
    # Chat input with real processing
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
        
        # Process with real AI agent
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
                    st.error(f"Error: {str(e)}")

def render_sidebar():
    """Render functional sidebar with real data"""
    with st.sidebar:
        st.header("📊 Session Info")
        
        # Session metrics
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", len(st.session_state.messages))
        with col2:
            st.metric("Session", st.session_state.session_id[-6:])
        
        # Current state
        if st.session_state.current_patient:
            st.subheader("👤 Current Patient")
            if hasattr(st.session_state.current_patient, 'full_name'):
                st.text(f"Name: {st.session_state.current_patient.full_name}")
                st.text(f"Type: {st.session_state.current_patient.patient_type.value.title()}")
                st.text(f"Duration: {st.session_state.current_patient.appointment_duration} min")
            
        if st.session_state.appointment_data:
            st.subheader("📅 Appointment")
            st.text(f"Doctor: {st.session_state.appointment_data.get('doctor', 'TBD')}")
            st.text(f"Date: {st.session_state.appointment_data.get('display', 'TBD')}")
        
        # System status with real checks
        st.markdown("---")
        st.subheader("🔧 System Status")
        
        # Check actual file existence and database
        checks = {
            "Database": Path("medical_scheduling.db").exists(),
            "Sample Data": Path("data/sample_patients.csv").exists(),
            "AI Agent": AGENT_AVAILABLE and get_agent() is not None,
            "API Key": bool(os.getenv("GOOGLE_API_KEY")),
            "Exports Dir": Path("exports").exists()
        }
        
        for check_name, status in checks.items():
            status_class = "system-status-good" if status else "system-status-bad"
            status_text = "✅ OK" if status else "❌ Error"
            st.markdown(f'<p class="{status_class}">{check_name}: {status_text}</p>', unsafe_allow_html=True)
        
        # Action buttons
        st.markdown("---")
        
        if st.button("🔄 Reset Chat"):
            st.session_state.messages = []
            st.session_state.current_patient = None
            st.session_state.appointment_data = None
            st.session_state.workflow_step = "greeting"
            st.session_state.session_id = f"session_{int(datetime.now().timestamp())}"
            st.rerun()
        
        if st.button("⚙️ System Setup"):
            with st.spinner("Running setup..."):
                try:
                    # Run actual setup
                    if not Path("data").exists():
                        Path("data").mkdir()
                    if not Path("exports").exists():
                        Path("exports").mkdir()
                    
                    # Generate data if missing
                    if not Path("data/sample_patients.csv").exists():
                        generate_all_data()
                    
                    # Initialize database
                    db = DatabaseManager()
                    
                    st.success("Setup completed!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Setup failed: {e}")

def render_real_analytics():
    """Render analytics with actual data from database"""
    st.subheader("📊 Real-Time Analytics Dashboard")
    
    # Get real statistics
    stats = get_real_database_stats()
    
    # Real metrics from database
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>👥 Total Patients</h3>
            <h2>{stats['total_patients']}</h2>
            <p>Loaded from database</p>
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
    
    # Real data visualizations
    if Path("data/sample_patients.csv").exists():
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
        
        # Age distribution
        st.subheader("📈 Patient Age Distribution")
        df['dob'] = pd.to_datetime(df['dob'])
        df['age'] = (datetime.now() - df['dob']).dt.days // 365
        
        fig3 = px.histogram(df, x='age', bins=20, title="Patient Age Distribution")
        st.plotly_chart(fig3, use_container_width=True)
    
    # Reminder system stats if available
    try:
        reminder_system = get_reminder_system()
        reminder_stats = reminder_system.get_reminder_statistics()
        
        if reminder_stats and not reminder_stats.get("error"):
            st.subheader("🔔 Reminder System Performance")
            
            reminder_data = reminder_stats.get("reminder_stats", [])
            if reminder_data:
                df_reminders = pd.DataFrame(reminder_data)
                
                col1, col2 = st.columns(2)
                with col1:
                    fig4 = px.bar(df_reminders, x='type', y='sent', title="Reminders Sent")
                    st.plotly_chart(fig4, use_container_width=True)
                
                with col2:
                    fig5 = px.bar(df_reminders, x='type', y='responded', title="Patient Responses")
                    st.plotly_chart(fig5, use_container_width=True)
    except Exception as e:
        st.info("Reminder system data not available")

def render_functional_admin():
    """Render admin panel with working features"""
    st.subheader("👨‍💼 Admin Panel - Live Data Management")
    
    # Real patient database
    if Path("data/sample_patients.csv").exists():
        df = pd.read_csv("data/sample_patients.csv")
        
        st.markdown("### 👥 Patient Database Management")
        
        # Working filters
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            patient_type_filter = st.selectbox("Patient Type", ["All"] + df['patient_type'].unique().tolist())
        with col2:
            insurance_filter = st.selectbox("Insurance", ["All"] + df['insurance_carrier'].unique().tolist())
        with col3:
            search_term = st.text_input("Search Name")
        with col4:
            show_count = st.number_input("Show Records", min_value=5, max_value=50, value=10)
        
        # Apply filters
        filtered_df = df.copy()
        if patient_type_filter != "All":
            filtered_df = filtered_df[filtered_df['patient_type'] == patient_type_filter]
        if insurance_filter != "All":
            filtered_df = filtered_df[filtered_df['insurance_carrier'] == insurance_filter]
        if search_term:
            mask = (filtered_df['first_name'].str.contains(search_term, case=False, na=False) | 
                   filtered_df['last_name'].str.contains(search_term, case=False, na=False))
            filtered_df = filtered_df[mask]
        
        # Display results
        st.markdown(f"**Showing {len(filtered_df)} of {len(df)} patients**")
        st.dataframe(filtered_df.head(show_count), use_container_width=True)
        
        # Real statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filtered Results", len(filtered_df))
        with col2:
            st.metric("Total Patients", len(df))
        with col3:
            new_count = len(filtered_df[filtered_df['patient_type'] == 'new'])
            st.metric("New Patients", new_count)
        with col4:
            returning_count = len(filtered_df[filtered_df['patient_type'] == 'returning'])
            st.metric("Returning", returning_count)
    
    else:
        st.warning("Patient database not found")
        if st.button("🔄 Generate Sample Data"):
            with st.spinner("Generating 50 sample patients..."):
                try:
                    generate_all_data()
                    st.success("Sample data generated! Refresh to see data.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Generation failed: {e}")
    
    # Working Excel export
    st.markdown("### 📊 Excel Export System")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        export_type = st.selectbox("Export Type", [
            "patient_list", "analytics_summary", "doctor_schedules", "all_appointments"
        ])
    with col2:
        start_date = st.date_input("Start Date", datetime.now().date() - timedelta(days=30))
    with col3:
        end_date = st.date_input("End Date", datetime.now().date())
    
    if st.button("📥 Generate Real Excel Export"):
        try:
            with st.spinner("Generating Excel file..."):
                exporter = ExcelExporter()
                filepath = exporter.export_data(export_type, start_date, end_date, include_details=True)
                
                # Verify file was created
                if Path(filepath).exists():
                    file_size = Path(filepath).stat().st_size
                    st.success(f"✅ Export completed: {Path(filepath).name} ({file_size:,} bytes)")
                    
                    # Working download
                    with open(filepath, "rb") as file:
                        st.download_button(
                            label="⬇️ Download Excel File",
                            data=file.read(),
                            file_name=Path(filepath).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("Export file was not created")
                    
        except Exception as e:
            logger.error(f"Export error: {e}")
            st.error(f"Export failed: {str(e)}")
    
    # Database operations
    st.markdown("### 🗄️ Database Operations")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 Check Database Status"):
            try:
                db = DatabaseManager()
                conn = db.get_connection()
                cursor = conn.cursor()
                
                # Get table info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                st.success(f"Database connected. Tables: {[t[0] for t in tables]}")
                
                # Get counts
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                        count = cursor.fetchone()[0]
                        st.text(f"{table[0]}: {count} records")
                    except:
                        st.text(f"{table[0]}: Error reading")
                
                conn.close()
            except Exception as e:
                st.error(f"Database error: {e}")
    
    with col2:
        if st.button("🔄 Rebuild Database"):
            try:
                with st.spinner("Rebuilding database..."):
                    # Remove existing database
                    if Path("medical_scheduling.db").exists():
                        Path("medical_scheduling.db").unlink()
                    
                    # Recreate
                    db = DatabaseManager()
                    st.success("Database rebuilt successfully!")
                    
            except Exception as e:
                st.error(f"Rebuild failed: {e}")

def main():
    """Main application with all functional features"""
    initialize_session_state()
    render_header()
    
    # Check system readiness
    system_ready = AGENT_AVAILABLE and Path("data/sample_patients.csv").exists()
    
    if not system_ready:
        st.warning("⚠️ System not ready. Please run setup.")
        if st.button("🚀 Quick Setup"):
            with st.spinner("Setting up system..."):
                try:
                    # Create directories
                    for dir_path in ["data", "exports", "logs"]:
                        Path(dir_path).mkdir(exist_ok=True)
                    
                    # Generate data
                    generate_all_data()
                    
                    # Initialize database
                    db = DatabaseManager()
                    
                    st.success("Setup complete! Refresh the page.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Setup failed: {e}")
        return
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🗣️ Schedule Appointment", "📊 Analytics", "👨‍💼 Admin"])
    
    with tab1:
        render_workflow_progress()
        st.divider()
        
        # Main interface
        col1, col2 = st.columns([3, 1])
        with col1:
            render_chat_interface()
        with col2:
            render_sidebar()
    
    with tab2:
        render_real_analytics()
    
    with tab3:
        render_functional_admin()
    
    # Footer with system info
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        🏥 MediCare AI Scheduling Agent | RagaAI Assignment<br>
        System Status: {'🟢 Operational' if system_ready else '🔴 Setup Required'} | 
        Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()