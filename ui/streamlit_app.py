"""
Production Streamlit Application - Updated for Real System
RagaAI Assignment - All Features Working with Real Services
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
    page_title="MediCare AI Scheduling - Production",
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import production components
SYSTEM_READY = False
AGENT_AVAILABLE = False

try:
    from agents.medical_agent import ProductionMedicalAgent
    from integrations.email_service import EmailService
    from integrations.sms_service import SMSService
    from integrations.calendly_integration import CalendlyIntegration
    from integrations.reminder_system import get_reminder_system
    from utils.excel_export import ExcelExporter
    AGENT_AVAILABLE = True
    SYSTEM_READY = True
    logger.info("✅ All production components loaded successfully")
except ImportError as e:
    logger.error(f"❌ Production component import error: {e}")

# Enhanced CSS for production
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
    .production-badge {
        background: #28a745;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        display: inline-block;
        margin-left: 10px;
    }
    .service-status {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        margin: 0.2rem 0;
        border-radius: 5px;
        border-left: 4px solid;
    }
    .service-online {
        border-left-color: #28a745;
        background: #d4edda;
        color: #155724;
    }
    .service-offline {
        border-left-color: #dc3545;
        background: #f8d7da;
        color: #721c24;
    }
    .metric-card-pro {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #3CB371;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .real-time-indicator {
        background: #dc3545;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 10px;
        font-size: 0.7rem;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_production_agent():
    """Initialize and cache the production AI agent"""
    if not AGENT_AVAILABLE:
        return None
    
    try:
        agent = ProductionMedicalAgent()
        logger.info("✅ Production AI Agent initialized")
        return agent
    except Exception as e:
        logger.error(f"❌ Failed to initialize production agent: {e}")
        return None

@st.cache_resource
def get_production_services():
    """Initialize production services"""
    services = {
        'email': None,
        'sms': None,
        'calendar': None,
        'reminders': None,
        'excel': None
    }
    
    try:
        services['email'] = EmailService()
        services['sms'] = SMSService()
        services['calendar'] = CalendlyIntegration()
        services['reminders'] = get_reminder_system()
        services['excel'] = ExcelExporter()
        
        logger.info("✅ Production services initialized")
    except Exception as e:
        logger.error(f"❌ Service initialization error: {e}")
    
    return services

def get_real_database_stats():
    """Get real database statistics"""
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        # Get patient counts
        cursor.execute("SELECT COUNT(*) FROM patients")
        total_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_type = 'new'")
        new_patients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM patients WHERE patient_type = 'returning'")
        returning_patients = cursor.fetchone()[0]
        
        # Get appointments
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_datetime) >= DATE('now')")
        upcoming_appointments = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE DATE(appointment_datetime) = DATE('now')")
        today_appointments = cursor.fetchone()[0]
        
        # Get reminders
        cursor.execute("SELECT COUNT(*) FROM reminders WHERE sent = TRUE AND DATE(scheduled_time) > DATE('now', '-7 days')")
        reminders_sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM reminder_responses WHERE DATE(received_at) > DATE('now', '-7 days')")
        responses_received = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_patients": total_patients,
            "new_patients": new_patients,
            "returning_patients": returning_patients,
            "upcoming_appointments": upcoming_appointments,
            "today_appointments": today_appointments,
            "reminders_sent": reminders_sent,
            "responses_received": responses_received,
            "response_rate": f"{(responses_received/reminders_sent*100):.1f}%" if reminders_sent > 0 else "0%"
        }
    except Exception as e:
        logger.error(f"❌ Database stats error: {e}")
        return {"error": str(e)}

def initialize_session_state():
    """Initialize Streamlit session state for production"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = f"prod_{int(datetime.now().timestamp())}"
    if "current_step" not in st.session_state:
        st.session_state.current_step = "greeting"
    if "appointment_data" not in st.session_state:
        st.session_state.appointment_data = None

def render_production_header():
    """Render production system header"""
    st.markdown(f"""
    <div class="main-header">
        <h1>🏥 MediCare Allergy & Wellness Center</h1>
        <h3>Production AI Scheduling System <span class="production-badge">LIVE</span></h3>
        <p>Real Services • Real Data • Real Automation</p>
        <div class="real-time-indicator">🔴 LIVE SYSTEM</div>
    </div>
    """, unsafe_allow_html=True)

def render_service_status():
    """Render real-time service status"""
    st.subheader("🔧 System Status")
    
    services = get_production_services()
    
    # Check individual service status
    service_status = {
        "AI Agent": AGENT_AVAILABLE,
        "Email Service": services['email'] is not None,
        "SMS Service": services['sms'] is not None,
        "Calendar System": services['calendar'] is not None,
        "Reminder System": services['reminders'] is not None,
        "Excel Export": services['excel'] is not None,
        "Database": Path("medical_scheduling.db").exists(),
        "Sample Data": Path("data/sample_patients.csv").exists()
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        for service, status in list(service_status.items())[:4]:
            status_class = "service-online" if status else "service-offline"
            status_icon = "🟢" if status else "🔴"
            st.markdown(f"""
            <div class="service-status {status_class}">
                {status_icon} <strong>{service}</strong>: {'Online' if status else 'Offline'}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        for service, status in list(service_status.items())[4:]:
            status_class = "service-online" if status else "service-offline"
            status_icon = "🟢" if status else "🔴"
            st.markdown(f"""
            <div class="service-status {status_class}">
                {status_icon} <strong>{service}</strong>: {'Online' if status else 'Offline'}
            </div>
            """, unsafe_allow_html=True)
    
    # Overall system health
    online_count = sum(service_status.values())
    total_count = len(service_status)
    health_percentage = (online_count / total_count) * 100
    
    st.progress(health_percentage / 100)
    st.markdown(f"**System Health: {health_percentage:.0f}% ({online_count}/{total_count} services online)**")
    
    return health_percentage >= 75

def render_production_chat():
    """Render production chat interface with real agent"""
    st.subheader("💬 AI Assistant - Production Mode")
    
    if not SYSTEM_READY:
        st.error("❌ Production system not ready. Please check service status above.")
        return
    
    agent = get_production_agent()
    if not agent:
        st.error("❌ AI Agent not available. Please check configuration.")
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
        
        # Process with production AI agent
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Processing with production AI..."):
                try:
                    # Call production agent
                    response = agent.process_message(prompt, st.session_state.session_id)
                    
                    # Display response
                    st.markdown(response)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Show real-time indicators
                    agent_state = agent.get_session_state(st.session_state.session_id)
                    if agent_state:
                        st.session_state.current_step = agent_state.get("current_step", "unknown")
                        if agent_state.get("appointment_info"):
                            st.session_state.appointment_data = agent_state["appointment_info"]
                    
                    st.rerun()
                    
                except Exception as e:
                    logger.error(f"❌ Production chat error: {e}")
                    st.error(f"Production system error: {str(e)}")

def render_real_analytics():
    """Render real analytics from production database"""
    st.subheader("📊 Real-Time Analytics")
    
    # Get real statistics
    stats = get_real_database_stats()
    
    if "error" in stats:
        st.error(f"Database connection error: {stats['error']}")
        return
    
    # Display real metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card-pro">
            <h3>👥 Total Patients</h3>
            <h1>{stats['total_patients']}</h1>
            <p>In production database</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card-pro">
            <h3>📅 Today's Appointments</h3>
            <h1>{stats['today_appointments']}</h1>
            <p>Scheduled for today</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card-pro">
            <h3>🔔 Reminders Sent</h3>
            <h1>{stats['reminders_sent']}</h1>
            <p>Last 7 days</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card-pro">
            <h3>📱 Response Rate</h3>
            <h1>{stats['response_rate']}</h1>
            <p>Patient engagement</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-time charts from database
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        
        # Patient type distribution
        patient_df = pd.read_sql_query("""
        SELECT patient_type, COUNT(*) as count 
        FROM patients 
        GROUP BY patient_type
        """, conn)
        
        if not patient_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Patient Type Distribution (Real Data)")
                fig = px.pie(patient_df, values='count', names='patient_type', 
                           title="New vs Returning Patients")
                st.plotly_chart(fig, use_container_width=True)
            
            # Appointment trends
            apt_df = pd.read_sql_query("""
            SELECT DATE(appointment_datetime) as date, COUNT(*) as appointments
            FROM appointments 
            WHERE DATE(appointment_datetime) >= DATE('now', '-30 days')
            GROUP BY DATE(appointment_datetime)
            ORDER BY date
            """, conn)
            
            with col2:
                if not apt_df.empty:
                    st.subheader("📈 Appointment Trends (Real Data)")
                    fig2 = px.line(apt_df, x='date', y='appointments',
                                 title="Daily Appointments (Last 30 Days)")
                    st.plotly_chart(fig2, use_container_width=True)
        
        conn.close()
        
    except Exception as e:
        st.warning(f"Chart generation error: {e}")

def render_production_admin():
    """Render production admin panel with real exports"""
    st.subheader("⚙️ Production Admin Panel")
    
    services = get_production_services()
    
    # Real export functionality
    st.markdown("### 📊 Real Data Exports")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 Export Patient List"):
            if services['excel']:
                try:
                    with st.spinner("Generating real patient export..."):
                        file_path = services['excel'].export_patient_list()
                        if file_path:
                            st.success(f"✅ Export created: {Path(file_path).name}")
                            
                            # Provide download link
                            with open(file_path, "rb") as file:
                                st.download_button(
                                    label="⬇️ Download Patient List",
                                    data=file,
                                    file_name=Path(file_path).name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                        else:
                            st.error("❌ Export failed")
                except Exception as e:
                    st.error(f"Export error: {e}")
    
    with col2:
        if st.button("📈 Export Analytics"):
            if services['excel']:
                try:
                    with st.spinner("Generating analytics report..."):
                        start_date = datetime.now() - timedelta(days=30)
                        end_date = datetime.now()
                        file_path = services['excel'].export_analytics_summary(start_date, end_date)
                        if file_path:
                            st.success(f"✅ Analytics export created: {Path(file_path).name}")
                        else:
                            st.error("❌ Analytics export failed")
                except Exception as e:
                    st.error(f"Analytics error: {e}")
    
    with col3:
        if st.button("🔔 Export Reminder Report"):
            if services['excel']:
                try:
                    with st.spinner("Generating reminder report..."):
                        start_date = datetime.now() - timedelta(days=30)
                        end_date = datetime.now()
                        file_path = services['excel'].export_reminder_report(start_date, end_date)
                        if file_path:
                            st.success(f"✅ Reminder report created: {Path(file_path).name}")
                        else:
                            st.error("❌ Reminder report failed")
                except Exception as e:
                    st.error(f"Reminder report error: {e}")
    
    # Service testing
    st.markdown("### 🧪 Service Testing")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📧 Email Service Test**")
        test_email = st.text_input("Test Email Address:", placeholder="your-email@gmail.com")
        if st.button("Send Test Email") and test_email and services['email']:
            try:
                with st.spinner("Sending test email..."):
                    success = services['email'].test_email_service(test_email)
                    if success:
                        st.success("✅ Test email sent successfully!")
                    else:
                        st.warning("⚠️ Email sent in mock mode (check logs)")
            except Exception as e:
                st.error(f"Email test failed: {e}")
    
    with col2:
        st.markdown("**📱 SMS Service Test**")
        test_phone = st.text_input("Test Phone Number:", placeholder="+1234567890")
        if st.button("Send Test SMS") and test_phone and services['sms']:
            try:
                with st.spinner("Sending test SMS..."):
                    success = services['sms'].test_sms_service(test_phone)
                    if success:
                        st.success("✅ Test SMS sent successfully!")
                    else:
                        st.warning("⚠️ SMS sent in mock mode (check logs)")
            except Exception as e:
                st.error(f"SMS test failed: {e}")
    
    # Real-time system monitoring
    st.markdown("### 📊 Real-Time System Monitoring")
    
    if services['reminders']:
        reminder_stats = services['reminders'].get_reminder_statistics()
        if 'error' not in reminder_stats:
            st.json(reminder_stats)
        else:
            st.error(f"Reminder stats error: {reminder_stats['error']}")

def main():
    """Main production application"""
    initialize_session_state()
    render_production_header()
    
    # Check system readiness
    system_health = render_service_status()
    
    if not system_health:
        st.warning("⚠️ Some services are offline. System functionality may be limited.")
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🗣️ Schedule Appointment", "📊 Real-Time Analytics", "⚙️ Production Admin"])
    
    with tab1:
        if SYSTEM_READY:
            render_production_chat()
        else:
            st.error("❌ Production chat requires system components to be online.")
            st.info("Please check the service status above and ensure all components are properly configured.")
    
    with tab2:
        render_real_analytics()
    
    with tab3:
        render_production_admin()
    
    # Production footer
    st.markdown("---")
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    system_status = '🟢 ONLINE' if system_health else '🟡 DEGRADED'
    
    st.markdown(f"""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        🏥 <strong>MediCare AI Scheduling Agent - PRODUCTION SYSTEM</strong><br>
        Status: {system_status} | Services: {'All Online' if system_health else 'Some Offline'} | 
        Last Updated: {current_time}<br>
        <span class="real-time-indicator">🔴 LIVE</span> Real Database • Real Communications • Real Automation
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()