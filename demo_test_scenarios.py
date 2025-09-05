#!/usr/bin/env python3
"""
Manual Test Scenarios for RagaAI Assignment Demo
Interactive test scenarios to validate all features work correctly
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path

def render_test_scenarios():
    """Render interactive test scenarios in Streamlit"""
    
    st.title("🧪 Demo Test Scenarios - RagaAI Assignment")
    st.markdown("**Use these scenarios to validate all features before your demo**")
    
    # Test scenario selector
    scenario_type = st.selectbox(
        "Choose Test Scenario Type:",
        [
            "🎯 Core Feature Tests",
            "🔥 Failure Mode Tests", 
            "🎬 Demo Scenarios",
            "🚨 Edge Cases",
            "📊 Data Validation"
        ]
    )
    
    if scenario_type == "🎯 Core Feature Tests":
        render_core_feature_tests()
    elif scenario_type == "🔥 Failure Mode Tests":
        render_failure_mode_tests()
    elif scenario_type == "🎬 Demo Scenarios":
        render_demo_scenarios()
    elif scenario_type == "🚨 Edge Cases":
        render_edge_case_tests()
    elif scenario_type == "📊 Data Validation":
        render_data_validation_tests()

def render_core_feature_tests():
    """Core feature validation tests"""
    
    st.subheader("🎯 Core Feature Tests")
    st.markdown("Test each of the 7 required features systematically")
    
    features = [
        {
            "name": "Feature 1: Patient Greeting",
            "test_inputs": [
                "Hi, I'm John Smith, born March 15, 1985, phone 555-1234, email john@test.com",
                "Hello, I need an appointment",
                "My name is María García-López, DOB 02/29/1988, phone (555) 123-4567"
            ],
            "expected": "Should extract patient info, ask for missing fields, handle special characters",
            "validation": "✅ Extracts name, DOB, phone, email\n✅ Asks for missing information\n✅ Handles various formats"
        },
        {
            "name": "Feature 2: Patient Lookup", 
            "test_inputs": [
                "I'm John Smith, born 1985-03-15",  # Should exist in sample data
                "I'm NewPatient TestUser, born 1999-12-31",  # Should not exist
                "Jane Johnson, DOB 07/11/1971"  # Test different date format
            ],
            "expected": "Should find existing patients, classify as new/returning",
            "validation": "✅ Finds existing patients\n✅ Identifies new patients\n✅ Handles date format variations"
        },
        {
            "name": "Feature 3: Smart Scheduling",
            "test_inputs": [
                "Continue with new patient flow → Check 60-minute duration",
                "Continue with returning patient → Check 30-minute duration"
            ],
            "expected": "60min for new, 30min for returning patients",
            "validation": "✅ New patients get 60-minute slots\n✅ Returning patients get 30-minute slots"
        },
        {
            "name": "Feature 4: Calendar Integration",
            "test_inputs": [
                "I'd like to see Dr. Sarah Johnson at Main Clinic",
                "Show me available times next week",
                "I'll take Tuesday at 9 AM"
            ],
            "expected": "Shows available slots, allows booking",
            "validation": "✅ Displays available time slots\n✅ Parses time selection\n✅ Confirms booking"
        },
        {
            "name": "Feature 5: Insurance Collection",
            "test_inputs": [
                "BlueCross BlueShield, member ID 123456789, group G4567",
                "I have Aetna but don't have my card with me",
                "I don't have insurance"
            ],
            "expected": "Captures insurance info, handles missing data",
            "validation": "✅ Parses complete insurance info\n✅ Handles partial information\n✅ Manages uninsured patients"
        },
        {
            "name": "Feature 6: Excel Export",
            "test_inputs": [
                "Complete booking process → Check if Excel file created",
                "Go to Admin panel → Test export functionality"
            ],
            "expected": "Generates Excel file with appointment data",
            "validation": "✅ Creates Excel file\n✅ Contains appointment details\n✅ File is downloadable"
        },
        {
            "name": "Feature 7: Form Distribution",
            "test_inputs": [
                "Complete booking with email → Check email sent",
                "Verify intake forms attached"
            ],
            "expected": "Sends confirmation email with forms",
            "validation": "✅ Sends confirmation email\n✅ Includes intake forms\n✅ Contains appointment details"
        }
    ]
    
    # Feature test interface
    selected_feature = st.selectbox(
        "Select Feature to Test:",
        [f["name"] for f in features]
    )
    
    feature = next(f for f in features if f["name"] == selected_feature)
    
    st.markdown(f"### {feature['name']}")
    st.markdown(f"**Expected Behavior:** {feature['expected']}")
    
    st.markdown("**Test Inputs:**")
    for i, test_input in enumerate(feature['test_inputs'], 1):
        st.code(f"{i}. {test_input}")
    
    st.markdown("**Validation Checklist:**")
    st.markdown(feature['validation'])
    
    # Test results tracking
    st.markdown("**Test Results:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        passed = st.button("✅ PASSED", key=f"pass_{selected_feature}")
    with col2:
        failed = st.button("❌ FAILED", key=f"fail_{selected_feature}")
    with col3:
        partial = st.button("⚠️ PARTIAL", key=f"partial_{selected_feature}")
    
    if failed:
        issue = st.text_area("Describe the issue:", key=f"issue_{selected_feature}")
        if issue:
            st.error(f"Issue logged: {issue}")

def render_failure_mode_tests():
    """Test failure scenarios and error handling"""
    
    st.subheader("🔥 Failure Mode Tests")
    st.markdown("Test how your system handles errors and edge cases")
    
    failure_scenarios = [
        {
            "category": "Data Validation Failures",
            "tests": [
                "I'm Bob, born yesterday, phone abc-def-ghij",
                "Jane Doe, DOB 13/50/1990, email not-an-email",
                "Name with symbols: @#$%^&*()",
                "Extremely long name: " + "A" * 200
            ]
        },
        {
            "category": "Database Connection Issues",
            "tests": [
                "Simulate: Rename medical_scheduling.db → test patient lookup",
                "Simulate: Corrupt sample_patients.csv → test data loading",
                "Test with empty database → verify graceful handling"
            ]
        },
        {
            "category": "API/Service Failures", 
            "tests": [
                "Test without GOOGLE_API_KEY → check LLM fallback",
                "Simulate email service down → test booking completion",
                "Test calendar service unavailable → check alternatives"
            ]
        },
        {
            "category": "Concurrent Access",
            "tests": [
                "Open multiple browser tabs → book same time slot",
                "Test session isolation → ensure no data mixing",
                "Rapid input submission → check race conditions"
            ]
        },
        {
            "category": "Memory/Storage Issues",
            "tests": [
                "Fill exports/ directory → test file creation",
                "Large patient database → test performance",
                "Long conversation → test memory usage"
            ]
        }
    ]
    
    selected_category = st.selectbox(
        "Select Failure Category:",
        [s["category"] for s in failure_scenarios]
    )
    
    scenario = next(s for s in failure_scenarios if s["category"] == selected_category)
    
    st.markdown(f"### {scenario['category']}")
    
    for i, test in enumerate(scenario['tests'], 1):
        st.markdown(f"**Test {i}:** {test}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            result = st.selectbox(
                f"Result {i}:",
                ["Not Tested", "Handled Gracefully", "Poor Error Message", "System Crashed"],
                key=f"failure_{selected_category}_{i}"
            )
        with col2:
            if result != "Not Tested":
                if result == "Handled Gracefully":
                    st.success("✅")
                elif result == "Poor Error Message":
                    st.warning("⚠️")
                else:
                    st.error("❌")

def render_demo_scenarios():
    """Pre-planned demo scenarios"""
    
    st.subheader("🎬 Demo Scenarios")
    st.markdown("**Perfect scenarios for your 3-5 minute demo video**")
    
    demo_scripts = [
        {
            "name": "🆕 New Patient Complete Flow",
            "duration": "2-3 minutes",
            "script": [
                "**Opening:** 'Let me show you how our AI handles a new patient booking'",
                "**Input:** 'Hi, I'm Sarah Williams, born January 30, 1988'",
                "**Narrate:** 'Notice it extracts the information and asks for missing details'",
                "**Input:** 'Phone 555-2020, email sarah@demo.com'", 
                "**Narrate:** 'It searches our database - Sarah is new, so 60-minute appointment'",
                "**Input:** 'I need an allergist, downtown location preferred'",
                "**Narrate:** 'Shows available times with Dr. Johnson downtown'",
                "**Input:** 'Tuesday at 10 AM works perfect'",
                "**Narrate:** 'Collects insurance information'",
                "**Input:** 'UnitedHealthcare, member 987654321, group G2020'",
                "**Narrate:** 'Confirms appointment, generates Excel export, sends forms'",
                "**Show:** Admin panel with Excel download"
            ]
        },
        {
            "name": "🔄 Returning Patient Quick Flow",
            "duration": "1-2 minutes", 
            "script": [
                "**Opening:** 'Now let's see how it handles returning patients'",
                "**Input:** 'I'm John Smith, born March 15, 1985'",
                "**Narrate:** 'Found in database - returning patient, 30-minute slot'",
                "**Input:** 'Same doctor as last time, Main Clinic'",
                "**Narrate:** 'Quick booking based on preferences'",
                "**Input:** 'Wednesday morning at 9:30 AM'",
                "**Narrate:** 'Streamlined process for returning patients'",
                "**Show:** Complete booking confirmation"
            ]
        },
        {
            "name": "🚨 Error Handling Demo", 
            "duration": "1 minute",
            "script": [
                "**Opening:** 'Let me demonstrate robust error handling'",
                "**Input:** 'I'm Bob, born yesterday, phone abc-123'",
                "**Narrate:** 'Notice graceful handling of invalid data'",
                "**Input:** 'Actually, I'm Bob Johnson, born 1975-06-15, phone 555-3030'",
                "**Narrate:** 'System recovers and continues normally'",
                "**Show:** No crashes, helpful error messages"
            ]
        },
        {
            "name": "📊 Data Export & Analytics",
            "duration": "1 minute",
            "script": [
                "**Opening:** 'Administrative features for clinic management'",
                "**Show:** Analytics dashboard with patient metrics",
                "**Demo:** Excel export with real appointment data",
                "**Show:** File download and contents",
                "**Narrate:** 'Complete data management for clinic operations'"
            ]
        }
    ]
    
    selected_demo = st.selectbox(
        "Select Demo Scenario:",
        [d["name"] for d in demo_scripts]
    )
    
    demo = next(d for d in demo_scripts if d["name"] == selected_demo)
    
    st.markdown(f"### {demo['name']}")
    st.markdown(f"**Duration:** {demo['duration']}")
    
    st.markdown("**Demo Script:**")
    for step in demo['script']:
        if step.startswith("**Input:**"):
            st.code(step.replace("**Input:** ", ""))
        elif step.startswith("**Show:**"):
            st.info(step)
        elif step.startswith("**Narrate:**"):
            st.markdown(f"🎤 {step}")
        else:
            st.markdown(step)
    
    # Practice mode
    if st.button(f"🎬 Practice {demo['name']}"):
        st.success("Practice mode: Follow the script above step by step!")
        st.balloons()

def render_edge_case_tests():
    """Test edge cases and unusual scenarios"""
    
    st.subheader("🚨 Edge Case Tests")
    
    edge_cases = [
        {
            "category": "Unusual Names & Data",
            "cases": [
                "María José García-López de la Cruz",
                "Name with numbers: John Smith III",
                "Single name: Cher",
                "Dr. John Smith Jr. MD (patient, not doctor)"
            ]
        },
        {
            "category": "Date Edge Cases",
            "cases": [
                "Leap year: February 29, 2000",
                "Recent birth: December 31, 2005", 
                "Very old: January 1, 1920",
                "Future date (should fail): January 1, 2030"
            ]
        },
        {
            "category": "Communication Preferences",
            "cases": [
                "No email address provided",
                "No phone number provided", 
                "International phone: +44 20 7946 0958",
                "Multiple emails: primary@email.com, backup@email.com"
            ]
        },
        {
            "category": "Scheduling Conflicts",
            "cases": [
                "Request past date: 'Yesterday at 3 PM'",
                "Weekend request: 'Saturday morning'",
                "Holiday request: 'Christmas Day'",
                "After hours: '11 PM appointment'"
            ]
        },
        {
            "category": "Insurance Edge Cases",
            "cases": [
                "Multiple insurance: 'Primary BlueCross, Secondary Aetna'",
                "International insurance: 'European Health Card'",
                "No insurance: 'I'll pay cash'",
                "Expired insurance: 'My plan expired last month'"
            ]
        }
    ]
    
    for edge_case in edge_cases:
        st.markdown(f"### {edge_case['category']}")
        
        for case in edge_case['cases']:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**Test:** {case}")
            
            with col2:
                result = st.selectbox(
                    "Result:",
                    ["Not Tested", "Handled Well", "Needs Work", "Failed"],
                    key=f"edge_{case}_{edge_case['cases'].index(case)}"
                )
                
                if result == "Handled Well":
                    st.success("✅")
                elif result == "Needs Work":
                    st.warning("⚠️")
                elif result == "Failed":
                    st.error("❌")

def render_data_validation_tests():
    """Validate data requirements"""
    
    st.subheader("📊 Data Validation Tests")
    st.markdown("Verify assignment data requirements are met")
    
    # Check 50 patients requirement
    st.markdown("### Patient Database Validation")
    
    if Path("data/sample_patients.csv").exists():
        import pandas as pd
        df = pd.read_csv("data/sample_patients.csv")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Patients", len(df))
            if len(df) == 50:
                st.success("✅ Exactly 50 as required")
            else:
                st.error(f"❌ Need 50, have {len(df)}")
        
        with col2:
            new_patients = len(df[df['patient_type'] == 'new'])
            st.metric("New Patients", new_patients)
        
        with col3:
            returning_patients = len(df[df['patient_type'] == 'returning'])
            st.metric("Returning Patients", returning_patients)
        
        # Data quality checks
        st.markdown("### Data Quality Checks")
        
        required_fields = ['patient_id', 'first_name', 'last_name', 'dob', 'phone', 'email', 'patient_type']
        
        for field in required_fields:
            if field in df.columns:
                missing_count = df[field].isna().sum()
                if missing_count == 0:
                    st.success(f"✅ {field}: No missing values")
                else:
                    st.warning(f"⚠️ {field}: {missing_count} missing values")
            else:
                st.error(f"❌ Missing required field: {field}")
        
        # Show sample data
        st.markdown("### Sample Data Preview")
        st.dataframe(df.head(10))
        
    else:
        st.error("❌ sample_patients.csv not found!")
        st.markdown("**Fix:** Run `python data/generate_data.py`")
    
    # Check other data files
    st.markdown("### Other Required Files")
    
    file_checks = [
        ("Doctor Schedules", "data/doctor_schedules.xlsx"),
        ("Database File", "medical_scheduling.db"), 
        ("Exports Directory", "exports"),
        ("Forms Directory", "forms")
    ]
    
    for name, path in file_checks:
        if Path(path).exists():
            st.success(f"✅ {name}: Found")
        else:
            st.error(f"❌ {name}: Missing ({path})")

def main():
    """Main test interface"""
    
    st.set_page_config(
        page_title="Demo Test Scenarios",
        page_icon="🧪",
        layout="wide"
    )
    
    render_test_scenarios()
    
    # Summary section
    st.markdown("---")
    st.markdown("### 📋 Pre-Demo Checklist")
    
    checklist = [
        "All 7 core features tested and working",
        "Error handling demonstrates graceful recovery", 
        "Demo scenarios practiced and timed",
        "Excel export functionality verified",
        "50 patient database confirmed",
        "Email/SMS integrations tested",
        "Reminder system functionality checked",
        "Edge cases handled appropriately"
    ]
    
    for item in checklist:
        st.checkbox(item)
    
    st.markdown("### 🎯 Demo Success Tips")
    st.info("""
    **For a successful demo:**
    1. Test your demo scenarios multiple times beforehand
    2. Have backup scenarios ready in case something fails
    3. Narrate what you're showing - don't just type silently
    4. Show both success and error handling
    5. Keep within 3-5 minute time limit
    6. Highlight the technical complexity (LangGraph, multi-agent, etc.)
    7. Show the Excel export and reminder system
    """)

if __name__ == "__main__":
    main()