import streamlit as st
import os
import sys
from datetime import datetime
from pathlib import Path
import logging
import sqlite3
import pandas as pd
import plotly.express as px

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
    page_title="MediCare AI Scheduling - Live Dashboard", 
    page_icon="🏥", 
    layout="wide"
)

# Custom CSS for better visuals
# ... (CSS remains the same)

# Main header
st.markdown("""
<div class="main-header">
    <h1>🏥 MediCare AI Scheduling Agent</h1>
    <p>Live & Interactive System Dashboard</p>
</div>
""", unsafe_allow_html=True)

# Initialize services in session state to persist
if 'services' not in st.session_state:
    try:
        st.session_state.services = {
            "agent": EnhancedMedicalSchedulingAgent(),
            "reminder_system": get_reminder_system(),
            "excel_exporter": EnhancedExcelExporter(),
            "email_service": EmailService(),
            "sms_service": SMSService(),
            "db_manager": DatabaseManager()
        }
    except Exception as e:
        st.error(f"Service initialization error: {e}")
        st.stop()

services = st.session_state.services

# Sidebar with system status
# ... (Sidebar remains largely the same but will now reflect true API key status)

# Main interface tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💬 Chat Interface", 
    "📊 Live Monitoring", 
    "📋 Admin Panel",
    "🧪 Feature Testing",
    "📈 System Analytics"
])

with tab1:
    # ... (Chat interface remains the same)
    st.header("AI Chat Interface")
    st.markdown("Complete appointment booking with real-time integration feedback")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.messages.append({
            "role": "assistant", 
            "content": "Hello! Welcome to MediCare. To begin, please provide your full name, date of birth, phone number, and email address."
        })
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    if prompt := st.chat_input("Type your message here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                from langchain_core.messages import HumanMessage, AIMessage
                conversation = [HumanMessage(content=msg["content"]) if msg["role"] == "user" else AIMessage(content=msg["content"]) for msg in st.session_state.messages]
                response_messages = services["agent"].process_message(conversation)
                
                if response_messages:
                    response_content = response_messages[-1].content
                    st.write(response_content)
                    st.session_state.messages.append({"role": "assistant", "content": response_content})


with tab2:
    st.header("🔴 Live System Monitoring")
    st.markdown("Real-time activity across all integrated services. Updates automatically.")

    if st.button("🔄 Refresh Monitoring Data"):
        st.rerun()

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📬 Recent Reminder Activity")
        try:
            reminders_df = pd.read_sql("SELECT appointment_id, reminder_type, scheduled_time, sent FROM reminders ORDER BY created_at DESC LIMIT 10", sqlite3.connect("medical_scheduling.db"))
            if not reminders_df.empty:
                st.dataframe(reminders_df, use_container_width=True)
            else:
                st.info("No reminders scheduled yet. Book an appointment to see live updates.")
        except Exception as e:
            st.error(f"Reminder monitoring error: {e}")
    
    with col2:
        st.subheader("📅 Recent Appointments")
        try:
            appointments_df = pd.read_sql("SELECT id, doctor, appointment_datetime, status FROM appointments ORDER BY created_at DESC LIMIT 10", sqlite3.connect("medical_scheduling.db"))
            if not appointments_df.empty:
                st.dataframe(appointments_df, use_container_width=True)
            else:
                st.info("No appointments booked yet.")
        except Exception as e:
            st.error(f"Appointment monitoring error: {e}")

with tab3:
    st.header("🔧 Admin Panel")
    
    conn = sqlite3.connect("medical_scheduling.db")
    
    st.subheader("👥 Patient Database")
    patients_df = pd.read_sql("SELECT id, first_name, last_name, dob, phone, email, patient_type FROM patients", conn)
    st.dataframe(patients_df, use_container_width=True)

    st.subheader("📊 Export Full Report with Visual Highlighting")
    if st.button("Generate & Download Excel Report"):
        with st.spinner("Generating report..."):
            filepath = services["excel_exporter"].export_complete_appointment_data()
            if filepath:
                st.success(f"Report generated! Click below to download.")
                with open(filepath, "rb") as f:
                    st.download_button(
                        label="📥 Download Excel Report",
                        data=f,
                        file_name=Path(filepath).name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.warning("No appointments found to export. Please book an appointment first.")
    conn.close()


with tab4:
    # ... (Feature testing tab remains the same for manual checks)
    st.header("🧪 Feature Testing")
    st.markdown("Manually test individual system components.")

    st.subheader("📞 Communication Services")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Email Service (SendGrid)**")
        email_address = st.text_input("Enter your email address to test:", key="test_email")
        if st.button("Send Test Email"):
            if email_address:
                with st.spinner("Sending test email..."):
                    success = services["email_service"]._send_email(email_address, "Test Email from MediCare AI", "<h1>Success!</h1><p>Your SendGrid integration is working.</p>")
                    if success:
                        st.success("Test email sent successfully!")
                    else:
                        st.error("Failed to send test email. Check your SendGrid API key and logs.")
            else:
                st.warning("Please enter an email address.")
    
    with col2:
        st.markdown("**SMS Service (Twilio)**")
        phone_number = st.text_input("Enter your phone number (with country code, e.g., +1...):", key="test_sms")
        if st.button("Send Test SMS"):
            if phone_number:
                with st.spinner("Sending test SMS..."):
                    success = services["sms_service"].send_sms(phone_number, "Test SMS from MediCare AI: Your Twilio integration is working!")
                    if success:
                        st.success("Test SMS sent successfully!")
                    else:
                        st.error("Failed to send test SMS. Check your Twilio credentials and logs.")
            else:
                st.warning("Please enter a phone number.")
        
with tab5:
    st.header("📈 System Analytics")
    if st.button("🔄 Refresh Analytics"):
        st.rerun()

    try:
        conn = sqlite3.connect("medical_scheduling.db")
        appointments_df = pd.read_sql("SELECT * FROM appointments", conn)
        patients_df = pd.read_sql("SELECT * FROM patients", conn)
        conn.close()

        if not appointments_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Appointments by Doctor")
                fig = px.bar(appointments_df['doctor'].value_counts().reset_index(), x='doctor', y='count', labels={'doctor':'Doctor', 'count':'Number of Appointments'})
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                st.subheader("New vs. Returning Patients")
                fig = px.pie(patients_df, names='patient_type', title='Patient Distribution')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointment data available to generate analytics.")

    except Exception as e:
        st.error(f"Analytics error: {e}")