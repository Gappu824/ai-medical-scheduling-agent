"""
Complete Streamlit Application for AI Medical Scheduling Agent
RagaAI Assignment - Fixed Syntax and Complete Implementation
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

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
    }
    .chat-message {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #3CB371;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        border-left: 4px solid #3CB371;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "current_patient" not in st.session_state:
        st.session_state.current_patient = None
    if "workflow_step" not in st.session_state:
        st.session_state.workflow_step = "greeting"

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
    """Show workflow progress"""
    steps = ["Greeting", "Patient Info", "Lookup", "Scheduling", "Insurance", "Confirmation", "Complete"]
    current_index = 0
    
    cols = st.columns(len(steps))
    for i, step in enumerate(steps):
        with cols[i]:
            if i <= current_index:
                st.markdown(f"""
                <div style="background: #2E8B57; color: white; padding: 0.8rem; 
                           border-radius: 10px; text-align: center;">
                    {step}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f8f9fa; color: #6c757d; padding: 0.8rem;
                           border-radius: 10px; text-align: center; border: 1px solid #dee2e6;">
                    {step}
                </div>
                """, unsafe_allow_html=True)

def render_chat_interface():
    """Render chat interface"""
    st.subheader("💬 Chat with AI Assistant")
    
    # Display messages
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
        
        # Mock AI response for demo
        if not st.session_state.messages or len(st.session_state.messages) == 1:
            response = """Hello! Welcome to MediCare Allergy & Wellness Center. I'm your AI scheduling assistant.

I'll help you schedule an appointment with one of our specialists. To get started, I need some basic information:

- Your full name (First and Last)
- Date of birth (MM/DD/YYYY)
- Phone number and email address

You can provide this all at once or step by step. How would you like to proceed?"""
        else:
            response = "Thank you for that information. I'm processing your request and will help you find the perfect appointment slot."
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        st.rerun()

def render_sidebar():
    """Render sidebar content"""
    with st.sidebar:
        st.header("📊 Session Info")
        
        st.metric("Messages", len(st.session_state.messages))
        st.metric("Current Step", st.session_state.workflow_step.replace('_', ' ').title())
        
        if st.session_state.current_patient:
            st.subheader("👤 Current Patient")
            st.text(f"Name: {st.session_state.current_patient.get('name', 'N/A')}")
            st.text(f"Type: {st.session_state.current_patient.get('type', 'N/A')}")
        
        st.markdown("---")
        if st.button("🔄 Reset Conversation"):
            st.session_state.messages = []
            st.session_state.current_patient = None
            st.session_state.workflow_step = "greeting"
            st.rerun()

def render_analytics():
    """Render analytics dashboard"""
    st.subheader("📊 Healthcare Analytics")
    
    # Mock data for demo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>📅 Appointments</h3>
            <h2>324</h2>
            <p style="color: #28a745;">↑ 12%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>👥 New Patients</h3>
            <h2>87</h2>
            <p style="color: #28a745;">↑ 8%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>📋 Form Rate</h3>
            <h2>92%</h2>
            <p style="color: #ffc107;">→ Same</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>⚠️ No-Shows</h3>
            <h2>5.2%</h2>
            <p style="color: #28a745;">↓ 15%</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        # Mock appointment data
        dates = pd.date_range('2024-08-01', periods=30)
        appointments_data = pd.DataFrame({
            'Date': dates,
            'New Patients': [3, 5, 2, 4, 6, 3, 1, 4, 5, 2, 3, 6, 4, 2, 5, 3, 4, 2, 6, 3, 5, 2, 4, 3, 6, 2, 5, 4, 3, 2],
            'Returning': [8, 12, 6, 10, 14, 9, 4, 11, 13, 7, 8, 15, 10, 6, 12, 8, 11, 7, 14, 9, 12, 6, 10, 8, 15, 7, 12, 11, 8, 6]
        })
        
        fig = px.line(appointments_data.melt(id_vars=['Date'], var_name='Type', value_name='Count'),
                     x='Date', y='Count', color='Type', title='Daily Appointments')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Doctor utilization
        doctor_data = pd.DataFrame({
            'Doctor': ['Dr. Johnson', 'Dr. Chen', 'Dr. Rodriguez'],
            'Appointments': [45, 38, 52]
        })
        
        fig2 = px.bar(doctor_data, x='Doctor', y='Appointments', title='Doctor Utilization')
        st.plotly_chart(fig2, use_container_width=True)

def render_admin():
    """Render admin panel"""
    st.subheader("👨‍💼 Admin Panel")
    
    # Patient database
    if Path(project_root / "data" / "sample_patients.csv").exists():
        try:
            df = pd.read_csv(project_root / "data" / "sample_patients.csv")
            st.markdown("### 👥 Patient Database")
            st.dataframe(df.head(10), use_container_width=True)
        except Exception as e:
            st.error(f"Error loading patient data: {e}")
    else:
        st.info("Patient database not found. Run setup to generate sample data.")
    
    # Export functionality
    st.markdown("### 📊 Export Data")
    if st.button("📥 Generate Excel Report"):
        try:
            # Mock export data
            export_data = pd.DataFrame({
                'Date': pd.date_range('2024-09-01', periods=10),
                'Patient': ['John Doe', 'Jane Smith'] * 5,
                'Doctor': ['Dr. Johnson', 'Dr. Chen'] * 5,
                'Status': ['Completed', 'Scheduled'] * 5
            })
            
            # Save to exports folder
            exports_dir = project_root / "exports"
            exports_dir.mkdir(exist_ok=True)
            filename = f"appointments_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = exports_dir / filename
            
            export_data.to_excel(filepath, index=False)
            st.success(f"Export saved: {filename}")
            
            # Download button
            with open(filepath, "rb") as file:
                st.download_button(
                    label="⬇️ Download Excel File",
                    data=file.read(),
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Export failed: {e}")

def main():
    """Main application"""
    initialize_session_state()
    render_header()
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["🗣️ Schedule Appointment", "📊 Analytics", "👨‍💼 Admin"])
    
    with tab1:
        render_workflow_progress()
        st.divider()
        
        col1, col2 = st.columns([2, 1])
        with col1:
            render_chat_interface()
        with col2:
            render_sidebar()
    
    with tab2:
        render_analytics()
    
    with tab3:
        render_admin()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #6c757d; padding: 1rem;">
        🏥 MediCare AI Scheduling Agent | RagaAI Assignment
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()