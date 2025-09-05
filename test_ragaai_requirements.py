#!/usr/bin/env python3
"""
ENHANCED TEST SUITE BASED ON COMPLETE REPOSITORY ANALYSIS
Missing test coverage identified after examining every file
Save as: test_enhanced_coverage.py
"""

import sys
import os
import sqlite3
import pandas as pd
import logging
from pathlib import Path
from datetime import datetime, timedelta
import traceback

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class EnhancedTestCoverage:
    """Enhanced test suite covering gaps found in code analysis"""
    
    def __init__(self):
        self.test_results = {"total": 0, "passed": 0, "failed": 0, "details": []}
        
    def run_complete_test_suite(self):
        """Run enhanced tests based on actual code analysis"""
        
        print("🔍 ENHANCED TEST SUITE - Based on Complete Code Analysis")
        print("=" * 70)
        
        # Tests based on actual file examination
        self.test_streamlit_ui_integration()
        self.test_medical_agent_langgraph_implementation()
        self.test_reminder_system_integration()
        self.test_excel_export_with_reminder_data()
        self.test_intake_form_pdf_generation()
        self.test_calendly_integration_excel_backend()
        self.test_sms_service_response_handling()
        self.test_email_service_3_tier_templates()
        self.test_database_migrations_reminder_tables()
        self.test_docker_production_deployment()
        self.test_assignment_specific_requirements()
        
        self.generate_enhanced_report()
        
    def test_streamlit_ui_integration(self):
        """Test Streamlit UI based on actual ui/streamlit_app.py code"""
        
        print("\n🖥️ Testing Streamlit UI Integration")
        print("-" * 50)
        
        try:
            # Test if streamlit_app.py has the correct imports
            ui_file = Path("ui/streamlit_app.py")
            if not ui_file.exists():
                self.record_failure("streamlit_app.py missing")
                return
                
            content = ui_file.read_text()
            
            # Check for required components found in the code
            required_components = [
                "EnhancedMedicalSchedulingAgent",
                "SYSTEM_PROMPT",
                "st.chat_message",
                "conversation_with_prompt"
            ]
            
            missing = []
            for component in required_components:
                if component not in content:
                    missing.append(component)
            
            if missing:
                self.record_failure(f"Streamlit UI missing components: {missing}")
            else:
                self.record_success("Streamlit UI has all required components")
                
            # Test system prompt integration
            if "You are a friendly and highly efficient AI assistant" in content:
                self.record_success("System prompt properly configured")
            else:
                self.record_failure("System prompt missing or incorrect")
                
        except Exception as e:
            self.record_failure(f"Streamlit UI test failed: {e}")
    
    def test_medical_agent_langgraph_implementation(self):
        """Test LangGraph implementation in medical_agent.py"""
        
        print("\n🤖 Testing Medical Agent LangGraph Implementation")
        print("-" * 50)
        
        try:
            # Test the actual medical agent implementation
            from agents.medical_agent import EnhancedMedicalSchedulingAgent
            
            agent = EnhancedMedicalSchedulingAgent()
            
            # Test if it has LangGraph components based on code analysis
            if hasattr(agent, 'graph'):
                self.record_success("Agent has LangGraph workflow")
            else:
                self.record_failure("Agent missing LangGraph structure")
            
            # Test tools integration (found in the code)
            required_tools = [
                'search_for_patient',
                'find_available_appointments', 
                'get_date_for_relative_request',
                'book_appointment'
            ]
            
            # Test if agent can process messages
            test_message = [{"role": "user", "content": "Hello"}]
            response = agent.process_message(test_message)
            
            if response and len(response) > 0:
                self.record_success("Agent processes messages correctly")
            else:
                self.record_failure("Agent message processing failed")
                
        except Exception as e:
            self.record_failure(f"Medical agent test failed: {e}")
    
    def test_reminder_system_integration(self):
        """Test 3-tier reminder system found in integrations/reminder_system.py"""
        
        print("\n📬 Testing 3-Tier Reminder System Integration")
        print("-" * 50)
        
        try:
            from integrations.reminder_system import ReminderSystem
            
            reminder_system = ReminderSystem()
            
            # Test database tables (from the actual code)
            conn = sqlite3.connect("medical_scheduling.db")
            cursor = conn.cursor()
            
            # Check if reminder tables exist (as implemented)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reminders'")
            if cursor.fetchone():
                self.record_success("Reminders table exists")
            else:
                self.record_failure("Reminders table missing")
            
            # Test reminder scheduling (key method found in code)
            test_datetime = datetime.now() + timedelta(days=7)
            result = reminder_system.schedule_appointment_reminders(
                "TEST_APT", test_datetime, "test@email.com", "555-1234"
            )
            
            if result:
                self.record_success("Reminder scheduling works")
            else:
                self.record_failure("Reminder scheduling failed")
                
            conn.close()
            
        except Exception as e:
            self.record_failure(f"Reminder system test failed: {e}")
    
    def test_excel_export_with_reminder_data(self):
        """Test Excel export including reminder data (utils/excel_export.py)"""
        
        print("\n📊 Testing Excel Export with Reminder Data")
        print("-" * 50)
        
        try:
            from utils.excel_export import EnhancedExcelExporter
            
            exporter = EnhancedExcelExporter()
            
            # Test export method found in the code
            filepath = exporter.export_complete_appointment_data()
            
            if filepath and Path(filepath).exists():
                self.record_success("Excel export creates file successfully")
                
                # Test file content (checking the sheets mentioned in code)
                df = pd.read_excel(filepath, sheet_name='Executive_Summary')
                if not df.empty:
                    self.record_success("Excel export contains executive summary")
                else:
                    self.record_failure("Excel export missing executive summary")
                    
            else:
                self.record_failure("Excel export failed to create file")
                
        except Exception as e:
            self.record_failure(f"Excel export test failed: {e}")
    
    def test_intake_form_pdf_generation(self):
        """Test intake form PDF (forms/patient_intake_form.pdf)"""
        
        print("\n📋 Testing Intake Form PDF Generation")
        print("-" * 50)
        
        try:
            form_path = Path("forms/patient_intake_form.pdf")
            
            if not form_path.exists():
                # Try to generate it using the setup script found
                try:
                    from forms.intake_form_setup import setup_complete_intake_system
                    success = setup_complete_intake_system()
                    
                    if success and form_path.exists():
                        self.record_success("Intake form PDF generated successfully")
                    else:
                        self.record_failure("Intake form PDF generation failed")
                except:
                    self.record_failure("Intake form setup script failed")
            else:
                # Check form content (based on the template in the code)
                content = form_path.read_text(encoding='utf-8')
                
                required_sections = [
                    "PATIENT INFORMATION",
                    "INSURANCE INFORMATION", 
                    "CRITICAL PRE-VISIT INSTRUCTIONS",
                    "STOP these medications 7 days before"
                ]
                
                missing_sections = []
                for section in required_sections:
                    if section not in content:
                        missing_sections.append(section)
                
                if not missing_sections:
                    self.record_success("Intake form contains all required sections")
                else:
                    self.record_failure(f"Intake form missing: {missing_sections}")
                    
        except Exception as e:
            self.record_failure(f"Intake form test failed: {e}")
    
    def test_calendly_integration_excel_backend(self):
        """Test Calendly integration with Excel backend (integrations/calendly_integration.py)"""
        
        print("\n📅 Testing Calendly Integration with Excel Backend")
        print("-" * 50)
        
        try:
            from integrations.calendly_integration import CalendlyIntegration
            
            calendly = CalendlyIntegration()
            
            # Test Excel file loading (as implemented in the code)
            if Path("data/doctor_schedules.xlsx").exists():
                self.record_success("Doctor schedules Excel file exists")
                
                # Test availability checking
                test_date = datetime.now().date()
                slots = calendly.get_available_slots("Dr. Sarah Johnson", test_date, 30)
                
                if isinstance(slots, list):
                    self.record_success("Calendar returns available slots")
                else:
                    self.record_failure("Calendar slots not returning properly")
                    
                # Test booking functionality
                test_time = datetime.now() + timedelta(days=1, hours=10)
                patient_data = {"full_name": "Test Patient"}
                
                result = calendly.book_appointment("Dr. Sarah Johnson", test_time, patient_data, 60)
                
                if result and result.get("status") == "confirmed":
                    self.record_success("Calendar booking works")
                else:
                    self.record_failure("Calendar booking failed")
                    
            else:
                self.record_failure("Doctor schedules Excel file missing")
                
        except Exception as e:
            self.record_failure(f"Calendly integration test failed: {e}")
    
    def test_sms_service_response_handling(self):
        """Test SMS service response handling (integrations/sms_service.py)"""
        
        print("\n📱 Testing SMS Service Response Handling")
        print("-" * 50)
        
        try:
            from integrations.sms_service import SMSService
            
            sms_service = SMSService()
            
            # Test response handling (key feature found in code)
            test_responses = [
                ("YES", "form_completed"),
                ("CANCEL", "visit_cancelled"), 
                ("CONFIRM", "visit_confirmed"),
                ("HELP", "help_request")
            ]
            
            for message, expected_type in test_responses:
                response_data = sms_service.handle_incoming_sms("555-1234", message)
                
                if response_data.get("response_type") == expected_type:
                    self.record_success(f"SMS handles '{message}' correctly")
                else:
                    self.record_failure(f"SMS failed to handle '{message}'")
                    
        except Exception as e:
            self.record_failure(f"SMS service test failed: {e}")
    
    def test_email_service_3_tier_templates(self):
        """Test email service 3-tier templates (integrations/email_service.py)"""
        
        print("\n📧 Testing Email Service 3-Tier Templates")
        print("-" * 50)
        
        try:
            from integrations.email_service import EmailService
            
            email_service = EmailService()
            
            # Test all 3 reminder types (found in the code)
            reminder_methods = [
                'send_initial_reminder',
                'send_form_check_reminder', 
                'send_final_confirmation'
            ]
            
            patient_data = {"first_name": "Test", "email": "test@email.com"}
            appointment_data = {"date": "2024-09-10", "time": "10:00 AM", "doctor": "Dr. Johnson"}
            
            for method_name in reminder_methods:
                if hasattr(email_service, method_name):
                    method = getattr(email_service, method_name)
                    result = method(patient_data, appointment_data)
                    
                    self.record_success(f"Email service has {method_name}")
                else:
                    self.record_failure(f"Email service missing {method_name}")
                    
        except Exception as e:
            self.record_failure(f"Email service test failed: {e}")
    
    def test_database_migrations_reminder_tables(self):
        """Test database migrations for reminder tables (database/migrations.py)"""
        
        print("\n🗃️ Testing Database Migrations for Reminder Tables")
        print("-" * 50)
        
        try:
            from database.migrations import run_reminder_system_migrations
            
            # Run migrations
            run_reminder_system_migrations()
            
            # Check if all tables exist
            conn = sqlite3.connect("medical_scheduling.db")
            cursor = conn.cursor()
            
            required_tables = [
                'reminders',
                'reminder_responses',
                'reminder_actions'
            ]
            
            for table in required_tables:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                if cursor.fetchone():
                    self.record_success(f"Table {table} exists")
                else:
                    self.record_failure(f"Table {table} missing")
            
            conn.close()
            
        except Exception as e:
            self.record_failure(f"Database migrations test failed: {e}")
    
    def test_docker_production_deployment(self):
        """Test Docker production deployment (Dockerfile, docker-compose.yml)"""
        
        print("\n🐳 Testing Docker Production Deployment")
        print("-" * 50)
        
        try:
            # Check Docker files exist
            docker_files = [
                "Dockerfile",
                "docker-compose.yml",
                ".dockerignore"
            ]
            
            for file in docker_files:
                if Path(file).exists():
                    self.record_success(f"{file} exists")
                else:
                    self.record_failure(f"{file} missing")
            
            # Check Dockerfile content
            dockerfile = Path("Dockerfile")
            if dockerfile.exists():
                content = dockerfile.read_text()
                
                required_elements = [
                    "FROM python:",
                    "COPY requirements.txt",
                    "EXPOSE 8501",
                    "streamlit run"
                ]
                
                for element in required_elements:
                    if element in content:
                        self.record_success(f"Dockerfile has {element}")
                    else:
                        self.record_failure(f"Dockerfile missing {element}")
                        
        except Exception as e:
            self.record_failure(f"Docker deployment test failed: {e}")
    
    def test_assignment_specific_requirements(self):
        """Test specific RagaAI assignment requirements"""
        
        print("\n🎯 Testing RagaAI Assignment Specific Requirements")
        print("-" * 50)
        
        try:
            # Test 50 patient requirement
            csv_path = Path("data/sample_patients.csv")
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                if len(df) == 50:
                    self.record_success("Exactly 50 patients in database")
                else:
                    self.record_failure(f"Wrong patient count: {len(df)}, need 50")
            else:
                self.record_failure("Patient CSV file missing")
            
            # Test LangChain/LangGraph usage
            try:
                import langchain
                import langgraph
                self.record_success("LangChain/LangGraph properly installed")
            except ImportError:
                self.record_failure("LangChain/LangGraph not properly installed")
            
            # Test main entry points
            entry_points = ["main.py", "run_local.py", "setup.py"]
            for entry_point in entry_points:
                if Path(entry_point).exists():
                    self.record_success(f"{entry_point} exists")
                else:
                    self.record_failure(f"{entry_point} missing")
            
            # Test assignment documentation
            if Path("README.md").exists():
                readme_content = Path("README.md").read_text()
                if "RagaAI" in readme_content and "assignment" in readme_content.lower():
                    self.record_success("README properly documents RagaAI assignment")
                else:
                    self.record_failure("README missing assignment documentation")
            
        except Exception as e:
            self.record_failure(f"Assignment requirements test failed: {e}")
    
    def record_success(self, message):
        """Record a test success"""
        self.test_results["total"] += 1
        self.test_results["passed"] += 1
        self.test_results["details"].append({"status": "PASS", "message": message})
        print(f"  ✅ PASS: {message}")
    
    def record_failure(self, message):
        """Record a test failure"""
        self.test_results["total"] += 1
        self.test_results["failed"] += 1
        self.test_results["details"].append({"status": "FAIL", "message": message})
        print(f"  ❌ FAIL: {message}")
    
    def generate_enhanced_report(self):
        """Generate enhanced test report"""
        
        print("\n" + "=" * 70)
        print("📊 ENHANCED TEST REPORT - Based on Complete Code Analysis")
        print("=" * 70)
        
        total = self.test_results["total"]
        passed = self.test_results["passed"]
        failed = self.test_results["failed"]
        
        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        
        if total > 0:
            pass_rate = (passed / total) * 100
            print(f"   📊 Pass Rate: {pass_rate:.1f}%")
            
            if pass_rate >= 90:
                print("🏆 EXCELLENT - Ready for RagaAI submission!")
            elif pass_rate >= 75:
                print("🥇 GOOD - Minor fixes needed")
            elif pass_rate >= 60:
                print("🥈 NEEDS WORK - Several issues to address")
            else:
                print("🔴 CRITICAL - Major problems need fixing")
        
        # Show failed tests
        failed_tests = [d for d in self.test_results["details"] if d["status"] == "FAIL"]
        if failed_tests:
            print(f"\n🚨 Critical Issues to Fix:")
            for i, test in enumerate(failed_tests[:10], 1):
                print(f"   {i}. {test['message']}")
            
            if len(failed_tests) > 10:
                print(f"   ... and {len(failed_tests) - 10} more issues")
        
        print(f"\n💡 Next Steps:")
        if failed > 0:
            print("   1. Fix the failed tests listed above")
            print("   2. Re-run this enhanced test suite")
            print("   3. Test end-to-end workflow manually")
        else:
            print("   1. Run manual end-to-end tests")
            print("   2. Prepare demo scenarios")
            print("   3. Package for RagaAI submission")
        
        print("=" * 70)

if __name__ == "__main__":
    print("🔍 Enhanced Test Suite - Based on Complete Repository Analysis")
    print("Testing gaps found after examining every file line-by-line\n")
    
    tester = EnhancedTestCoverage()
    tester.run_complete_test_suite()
    
    # Exit with appropriate code
    if tester.test_results["failed"] == 0:
        print("\n🎉 ALL ENHANCED TESTS PASSED!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {tester.test_results['failed']} ISSUES NEED FIXING")
        sys.exit(1)