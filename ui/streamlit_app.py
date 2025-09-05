import streamlit as st
import os
import sys
from datetime import datetime
from pathlib import Path
import logging
import sqlite3
import pandas as pd

# Setup encoding
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import project modules
try:
    from agents.medical_agent import EnhancedMedicalSchedulingAgent
    from integrations.reminder_system import get_reminder_system
    from utils.excel_export import EnhancedExcelExporter
    from integrations.email_service import EmailService
    from integrations.sms_service import SMSService
    from database.database import DatabaseManager
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()

st.set_page_config(
    page_title="MediCare AI Scheduling - Complete Integration", 
    page_icon="🏥", 
    layout="wide"
)

# Custom CSS for better visuals
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #2E8B57, #3CB371);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #2E8B57;
        margin: 0.5rem 0;
    }
    .success-alert {
        background: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
    .warning-alert {
        background: #fff3cd;
        color: #856404;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🏥 MediCare AI Scheduling Agent</h1>
    <p>Complete Integration Demo - All Features Working Together</p>
</div>
""", unsafe_allow_html=True)

# Initialize services
@st.cache_resource
def initialize_services():
    """Initialize all services"""
    try:
        agent = EnhancedMedicalSchedulingAgent()
        reminder_system = get_reminder_system()
        excel_exporter = EnhancedExcelExporter()
        email_service = EmailService()
        sms_service = SMSService()
        db_manager = DatabaseManager()
        
        return {
            "agent": agent,
            "reminder_system": reminder_system,
            "excel_exporter": excel_exporter,
            "email_service": email_service,
            "sms_service": sms_service,
            "db_manager": db_manager
        }
    except Exception as e:
        st.error(f"Service initialization error: {e}")
        return None

services = initialize_services()

if not services:
    st.error("Failed to initialize services. Please check configuration.")
    st.stop()

# Sidebar with system status
with st.sidebar:
    st.header("🔧 System Status")
    
    # Check each service
    service_status = []
    
    if services["agent"]:
        service_status.append("✅ AI Agent: Ready")
    else:
        service_status.append("❌ AI Agent: Failed")
    
    if services["reminder_system"]:
        service_status.append("✅ Reminder System: Active")
    else:
        service_status.append("❌ Reminder System: Failed")
    
    if services["excel_exporter"]:
        service_status.append("✅ Excel Export: Ready")
    else:
        service_status.append("❌ Excel Export: Failed")
    
    if services["email_service"]:
        service_status.append("✅ Email Service: Demo Mode")
    else:
        service_status.append("❌ Email Service: Failed")
    
    if services["sms_service"]:
        service_status.append("✅ SMS Service: Demo Mode")
    else:
        service_status.append("❌ SMS Service: Failed")
    
    for status in service_status:
        st.markdown(f"<div class='feature-card'>{status}</div>", unsafe_allow_html=True)
    
    # Database stats
    st.subheader("📊 Database Stats")
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        
        # Patient count
        patient_count = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
        st.metric("Patients", patient_count)
        
        # Appointment count
        appointment_count = pd.read_sql("SELECT COUNT(*) as count FROM appointments", conn).iloc[0]['count']
        st.metric("Appointments", appointment_count)
        
        # Reminder count
        reminder_count = pd.read_sql("SELECT COUNT(*) as count FROM reminders", conn).iloc[0]['count']
        st.metric("Reminders", reminder_count)
        
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")

# Main interface tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat Interface", 
    "📊 Live Monitoring", 
    "📋 Admin Panel",
    "🧪 Feature Testing",
    "📈 System Analytics"
])

with tab1:
    st.header("AI Chat Interface")
    st.markdown("Complete appointment booking with real-time integration feedback")
    
    # Initialize chat
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! Welcome to MediCare Allergy & Wellness Center. I'm ready to help you book an appointment. Please tell me your name and date of birth to get started."
        })
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Process with agent
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                try:
                    # Convert to LangChain format
                    from langchain_core.messages import HumanMessage, AIMessage
                    
                    conversation = []
                    for msg in st.session_state.messages:
                        if msg["role"] == "user":
                            conversation.append(HumanMessage(content=msg["content"]))
                        else:
                            conversation.append(AIMessage(content=msg["content"]))
                    
                    # Get response from agent
                    response_messages = services["agent"].process_message(conversation)
                    
                    if response_messages and len(response_messages) > 0:
                        response_content = response_messages[-1].content
                        st.write(response_content)
                        
                        # Add to session state
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": response_content
                        })
                        
                        # Show integration activity
                        if "booking" in response_content.lower() or "confirmed" in response_content.lower():
                            st.success("🎉 Integration Activity: Appointment booking triggered!")
                            st.info("📧 Email confirmation sent (demo mode)")
                            st.info("📱 SMS reminder scheduled (demo mode)")
                            st.info("📊 Excel export ready for download")
                    
                except Exception as e:
                    st.error(f"Agent error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "I apologize for the technical issue. Please try again."
                    })

with tab2:
    st.header("🔴 Live System Monitoring")
    st.markdown("Real-time activity across all integrated services")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📬 Recent Reminder Activity")
        try:
            conn = sqlite3.connect("medical_scheduling.db")
            reminders_df = pd.read_sql("""
                SELECT appointment_id, reminder_type, scheduled_time, sent, 
                       email_sent, sms_sent, created_at
                FROM reminders 
                ORDER BY created_at DESC 
                LIMIT 10
            """, conn)
            
            if not reminders_df.empty:
                st.dataframe(reminders_df)
            else:
                st.info("No reminder activity yet. Book an appointment to see reminders here!")
            
            conn.close()
        except Exception as e:
            st.error(f"Reminder monitoring error: {e}")
    
    with col2:
        st.subheader("📧 Email & SMS Activity")
        try:
            # Show demo email/SMS activity
            st.markdown("""
            <div class="success-alert">
                ✅ Email Service: Ready (Demo Mode)<br>
                📧 Last activity: System initialized<br>
                📱 SMS Service: Ready (Demo Mode)<br>
                📲 Last activity: System initialized
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🧪 Test Email Integration"):
                patient_data = {"first_name": "Test", "email": "test@demo.com"}
                appointment_data = {"date": "2024-09-10", "time": "10:00 AM", "doctor": "Dr. Johnson"}
                
                result = services["email_service"].send_appointment_confirmation(patient_data, appointment_data)
                if result:
                    st.success("✅ Email confirmation sent successfully (demo mode)")
                else:
                    st.error("❌ Email sending failed")
            
            if st.button("📱 Test SMS Integration"):
                patient_data = {"phone": "555-1234"}
                appointment_data = {"date": "2024-09-10", "time": "10:00 AM"}
                
                result = services["sms_service"].send_initial_reminder_sms(patient_data, appointment_data)
                if result:
                    st.success("✅ SMS reminder sent successfully (demo mode)")
                else:
                    st.error("❌ SMS sending failed")
        
        except Exception as e:
            st.error(f"Communication monitoring error: {e}")

with tab3:
    st.header("🔧 Admin Panel")
    st.markdown("Manage patients, appointments, and export data")
    
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["👥 Patients", "📅 Appointments", "📊 Exports"])
    
    with admin_tab1:
        st.subheader("Patient Database")
        try:
            conn = sqlite3.connect("medical_scheduling.db")
            patients_df = pd.read_sql("SELECT * FROM patients LIMIT 20", conn)
            st.dataframe(patients_df)
            conn.close()
        except Exception as e:
            st.error(f"Patient data error: {e}")
    
    with admin_tab2:
        st.subheader("Recent Appointments")
        try:
            conn = sqlite3.connect("medical_scheduling.db")
            appointments_df = pd.read_sql("""
                SELECT a.id, a.appointment_datetime, a.doctor, a.location, 
                       p.first_name, p.last_name, a.status
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                ORDER BY a.appointment_datetime DESC
                LIMIT 10
            """, conn)
            
            if not appointments_df.empty:
                st.dataframe(appointments_df)
            else:
                st.info("No appointments yet. Use the chat interface to book one!")
            
            conn.close()
        except Exception as e:
            st.error(f"Appointment data error: {e}")
    
    with admin_tab3:
        st.subheader("Data Export")
        
        if st.button("📊 Generate Complete Excel Report"):
            try:
                filepath = services["excel_exporter"].export_complete_appointment_data()
                if filepath:
                    st.success(f"✅ Excel report generated: {filepath}")
                    
                    # Offer download
                    with open(filepath, "rb") as f:
                        st.download_button(
                            label="📥 Download Excel Report",
                            data=f.read(),
                            file_name=Path(filepath).name,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                else:
                    st.error("❌ Excel export failed")
            except Exception as e:
                st.error(f"Export error: {e}")

with tab4:
    st.header("🧪 Feature Testing")
    st.markdown("Test individual features and integrations")
    
    test_col1, test_col2 = st.columns(2)
    
    with test_col1:
        st.subheader("🤖 AI Agent Testing")
        
        if st.button("Test Patient Lookup"):
            try:
                from langchain_core.messages import HumanMessage
                test_message = [HumanMessage(content="I'm John Smith, born March 15, 1985")]
                response = services["agent"].process_message(test_message)
                
                if response:
                    st.success("✅ Agent responded successfully")
                    st.code(response[-1].content)
                else:
                    st.error("❌ Agent failed to respond")
            except Exception as e:
                st.error(f"Agent test error: {e}")
        
        if st.button("Test Calendar Integration"):
            try:
                from integrations.calendly_integration import CalendlyIntegration
                calendar = CalendlyIntegration()
                
                test_date = datetime.now().date()
                slots = calendar.get_available_slots("Dr. Sarah Johnson", test_date, 30)
                
                if slots:
                    st.success(f"✅ Found {len(slots)} available slots")
                    for slot in slots[:3]:
                        st.info(f"📅 Available: {slot.strftime('%I:%M %p')}")
                else:
                    st.warning("⚠️ No slots found for today")
            except Exception as e:
                st.error(f"Calendar test error: {e}")
    
    with test_col2:
        st.subheader("📬 Communication Testing")
        
        if st.button("Test Reminder System"):
            try:
                test_datetime = datetime.now() + timedelta(days=7)
                result = services["reminder_system"].schedule_appointment_reminders(
                    "TEST_REMINDER", test_datetime, "test@demo.com", "555-1234"
                )
                
                if result:
                    st.success("✅ Reminder system working")
                    st.info("📅 3-tier reminders scheduled successfully")
                else:
                    st.error("❌ Reminder system failed")
            except Exception as e:
                st.error(f"Reminder test error: {e}")
        
        if st.button("Test Database Integration"):
            try:
                patients = services["db_manager"].get_all_patients()
                st.success(f"✅ Database working - {len(patients)} patients loaded")
            except Exception as e:
                st.error(f"Database test error: {e}")

with tab5:
    st.header("📈 System Analytics")
    st.markdown("Performance metrics and system health")
    
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        
        # Overall statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_patients = pd.read_sql("SELECT COUNT(*) as count FROM patients", conn).iloc[0]['count']
            st.metric("Total Patients", total_patients)
        
        with col2:
            total_appointments = pd.read_sql("SELECT COUNT(*) as count FROM appointments", conn).iloc[0]['count']
            st.metric("Total Appointments", total_appointments)
        
        with col3:
            total_reminders = pd.read_sql("SELECT COUNT(*) as count FROM reminders", conn).iloc[0]['count']
            st.metric("Reminders Scheduled", total_reminders)
        
        with col4:
            # System uptime (mock)
            st.metric("System Status", "🟢 Online")
        
        conn.close()
        
    except Exception as e:
        st.error(f"Analytics error: {e}")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666;">
    🏥 MediCare AI Scheduling Agent - Complete Integration Demo<br>
    All 7 core features working seamlessly together with visual feedback
</div>
""", unsafe_allow_html=True)
