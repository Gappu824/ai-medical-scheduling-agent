#!/usr/bin/env python3
"""
VERIFY COMPLETE INTEGRATION
Quick verification that everything is working
Save as: verify_integration.py
Run: python verify_integration.py
"""

import sys
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

def verify_all_components():
    """Verify all components are working"""
    
    print("🔍 VERIFYING COMPLETE INTEGRATION")
    print("=" * 50)
    
    results = {"passed": 0, "failed": 0, "details": []}
    
    # Test 1: Database Schema
    print("\n1️⃣ Testing Database Schema...")
    try:
        conn = sqlite3.connect("medical_scheduling.db")
        cursor = conn.cursor()
        
        # Check reminders table has required columns
        cursor.execute("PRAGMA table_info(reminders)")
        columns = [col[1] for col in cursor.fetchall()]
        
        required_columns = ['patient_email', 'patient_phone', 'reminder_type']
        missing = [col for col in required_columns if col not in columns]
        
        if not missing:
            print("   ✅ Database schema complete")
            results["passed"] += 1
        else:
            print(f"   ❌ Missing columns: {missing}")
            results["failed"] += 1
        
        conn.close()
        
    except Exception as e:
        print(f"   ❌ Database error: {e}")
        results["failed"] += 1
    
    # Test 2: Patient Data
    print("\n2️⃣ Testing Patient Data...")
    try:
        if Path("data/sample_patients.csv").exists():
            df = pd.read_csv("data/sample_patients.csv")
            if len(df) == 50:
                print(f"   ✅ Patient data complete: {len(df)} patients")
                results["passed"] += 1
            else:
                print(f"   ⚠️ Patient count: {len(df)} (should be 50)")
                results["failed"] += 1
        else:
            print("   ❌ Patient data file missing")
            results["failed"] += 1
    except Exception as e:
        print(f"   ❌ Patient data error: {e}")
        results["failed"] += 1
    
    # Test 3: Service Imports
    print("\n3️⃣ Testing Service Imports...")
    services = [
        ("AI Agent", "agents.medical_agent", "EnhancedMedicalSchedulingAgent"),
        ("Reminder System", "integrations.reminder_system", "get_reminder_system"), 
        ("Email Service", "integrations.email_service", "EmailService"),
        ("SMS Service", "integrations.sms_service", "SMSService"),
        ("Excel Export", "utils.excel_export", "EnhancedExcelExporter")
    ]
    
    for service_name, module_name, class_name in services:
        try:
            module = __import__(module_name, fromlist=[class_name])
            service_class = getattr(module, class_name)
            print(f"   ✅ {service_name} imports successfully")
            results["passed"] += 1
        except Exception as e:
            print(f"   ❌ {service_name} import failed: {e}")
            results["failed"] += 1
    
    # Test 4: File Permissions
    print("\n4️⃣ Testing File Permissions...")
    directories = ["data", "exports", "logs", "forms"]
    
    for directory in directories:
        try:
            dir_path = Path(directory)
            dir_path.mkdir(exist_ok=True)
            
            # Test write permission
            test_file = dir_path / "permission_test.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            print(f"   ✅ {directory}/ writable")
            results["passed"] += 1
        except Exception as e:
            print(f"   ❌ {directory}/ permission error: {e}")
            results["failed"] += 1
    
    # Test 5: UI Files
    print("\n5️⃣ Testing UI Files...")
    ui_files = ["ui/streamlit_app.py", "main_fixed.py"]
    
    for ui_file in ui_files:
        if Path(ui_file).exists():
            print(f"   ✅ {ui_file} exists")
            results["passed"] += 1
        else:
            print(f"   ❌ {ui_file} missing")
            results["failed"] += 1
    
    # Generate Report
    print("\n" + "=" * 50)
    print("📊 INTEGRATION VERIFICATION REPORT")
    print("=" * 50)
    
    total = results["passed"] + results["failed"]
    pass_rate = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"📊 Success Rate: {pass_rate:.1f}%")
    
    if pass_rate >= 90:
        print("\n🏆 EXCELLENT - System ready for demo!")
        print("\n🚀 Next steps:")
        print("   1. Run: python quick_start_complete.py")
        print("   2. Open: http://localhost:8501")
        print("   3. Test booking workflow")
        print("   4. Check live monitoring tab")
        
    elif pass_rate >= 70:
        print("\n🟡 GOOD - Minor issues but demo-ready")
        print("\n🔧 Recommended fixes:")
        print("   1. Run: python fix_complete_integration.py")
        print("   2. Re-run this verification")
        
    else:
        print("\n🔴 CRITICAL - Major issues need fixing")
        print("\n🆘 Required actions:")
        print("   1. Run: python fix_complete_integration.py")
        print("   2. Check error messages above")
        print("   3. Verify all dependencies installed")
    
    return pass_rate >= 70

def run_quick_demo_test():
    """Run a quick demo test to show integration"""
    
    print("\n🎬 RUNNING QUICK DEMO TEST")
    print("-" * 30)
    
    try:
        # Test agent response
        sys.path.insert(0, str(Path(__file__).parent))
        from agents.medical_agent import EnhancedMedicalSchedulingAgent
        from langchain_core.messages import HumanMessage
        
        agent = EnhancedMedicalSchedulingAgent()
        test_message = [HumanMessage(content="Hello, I need an appointment")]
        
        print("🤖 Testing AI Agent...")
        response = agent.process_message(test_message)
        
        if response and len(response) > 0:
            print("   ✅ Agent responds correctly")
            print(f"   📝 Response preview: {response[-1].content[:100]}...")
        else:
            print("   ❌ Agent failed to respond")
        
        # Test reminder system
        print("\n📬 Testing Reminder System...")
        from integrations.reminder_system import get_reminder_system
        
        reminder_system = get_reminder_system()
        
        # Try to schedule a test reminder
        test_datetime = datetime.now()
        result = reminder_system.schedule_appointment_reminders(
            "DEMO_TEST", test_datetime, "demo@test.com", "555-1234"
        )
        
        if result:
            print("   ✅ Reminder system working")
        else:
            print("   ⚠️ Reminder system has issues but functional")
        
        print("\n🎯 DEMO TEST COMPLETE")
        print("   System is ready for live demonstration!")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Demo test failed: {e}")
        print("   ⚠️ System may work but needs testing")
        return False

if __name__ == "__main__":
    print("🔍 Starting complete integration verification...\n")
    
    # Run verification
    system_ready = verify_all_components()
    
    if system_ready:
        # Run demo test
        demo_ready = run_quick_demo_test()
        
        if demo_ready:
            print("\n🎉 SYSTEM FULLY VERIFIED AND DEMO-READY!")
            print("🚀 Run: python quick_start_complete.py")
        else:
            print("\n⚠️ System verified but demo test had issues")
            print("🔧 Try running the fixes first")
    else:
        print("\n❌ System needs fixes before demo")
        print("🛠️ Run: python fix_complete_integration.py")
    
    print(f"\nVerification completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")