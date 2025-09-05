# RagaAI Assignment - Final Submission Checklist
# Run these commands to ensure everything works for demo

echo "🏥 RagaAI Medical Scheduling Agent - Final Setup"
echo "=============================================="

# 1. Fix File Permissions (Critical)
echo "🔧 Fixing file permissions..."
chmod 777 data/
chmod 666 data/doctor_schedules.xlsx 2>/dev/null || echo "Excel file will be created"
chmod 666 data/sample_patients.csv 2>/dev/null || echo "CSV will be created"
chmod 666 medical_scheduling.db 2>/dev/null || echo "Database will be created"

# 2. Generate Required Data
echo "📊 Generating required assignment data..."
python data/generate_data.py

# 3. Create Intake Forms
echo "📋 Setting up intake forms..."
mkdir -p forms
python -c "
from intake_form_integration import complete_intake_form_setup
complete_intake_form_setup()
"

# 4. Initialize Database
echo "🗃️ Initializing database..."
python -c "
from database.database import DatabaseManager
db = DatabaseManager()
print('✅ Database initialized')
"

# 5. Test Core Agent
echo "🤖 Testing medical agent..."
python -c "
try:
    from agents.medical_agent import EnhancedMedicalSchedulingAgent
    agent = EnhancedMedicalSchedulingAgent()
    print('✅ Medical agent loaded successfully')
except Exception as e:
    print(f'❌ Agent error: {e}')
"

# 6. Test Reminder System
echo "📬 Testing reminder system..."
python -c "
try:
    from integrations.reminder_system import get_reminder_system
    rs = get_reminder_system()
    print('✅ Reminder system ready')
except Exception as e:
    print(f'❌ Reminder error: {e}')
"

# 7. Test Excel Export
echo "📊 Testing Excel export..."
python -c "
try:
    from utils.excel_export import EnhancedExcelExporter
    exporter = EnhancedExcelExporter()
    print('✅ Excel export ready')
except Exception as e:
    print(f'❌ Export error: {e}')
"

# 8. Validate Assignment Requirements
echo "🧪 Running assignment validation..."
python critical_fixes_needed.py

# 9. Start Application
echo "🚀 Starting application..."
echo "Run: streamlit run ui/streamlit_app.py"
echo ""
echo "📋 DEMO SCRIPT FOR RAGAAI:"
echo "=========================="
echo "1. Say: 'Hi, I'm John Smith, born March 15, 1985, phone 555-1234'"
echo "2. Continue: 'I need an allergist for seasonal allergies'"  
echo "3. Select: 'Dr. Sarah Johnson at Main Clinic'"
echo "4. Choose: 'Tuesday at 10 AM'"
echo "5. Provide: 'BlueCross BlueShield, member 123456789, group G1234'"
echo "6. Check database for reminders created"
echo "7. Export Excel to show complete data"
echo ""
echo "✅ READY FOR RAGAAI SUBMISSION!"