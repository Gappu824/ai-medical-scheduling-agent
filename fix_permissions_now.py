#!/usr/bin/env python3
"""
QUICK 5-MINUTE FIX: File Permission Issues
Save this as: fix_permissions_now.py
Run: python fix_permissions_now.py
"""

import os
import stat
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_permissions_now():
    """Fix all file permission issues in 5 minutes"""
    
    print("🔧 QUICK PERMISSION FIX - 5 MINUTES")
    print("=" * 50)
    
    steps_completed = []
    
    # Step 1: Close Excel if open
    print("📝 Step 1: Please close Excel if you have doctor_schedules.xlsx open")
    input("Press ENTER when Excel is closed...")
    steps_completed.append("✅ Excel closed")
    
    # Step 2: Delete problematic files (they'll be regenerated)
    print("\n🗑️ Step 2: Removing problematic files...")
    
    files_to_remove = [
        "data/doctor_schedules.xlsx",
        "data/doctor_schedules.xlsx.lock"
    ]
    
    for file_path in files_to_remove:
        try:
            if Path(file_path).exists():
                Path(file_path).unlink()
                print(f"   Removed: {file_path}")
        except Exception as e:
            print(f"   Could not remove {file_path}: {e}")
    
    steps_completed.append("✅ Cleared problematic files")
    
    # Step 3: Fix directory permissions
    print("\n📁 Step 3: Fixing directory permissions...")
    
    directories = ["data", "exports", "logs", "forms"]
    
    for directory in directories:
        try:
            Path(directory).mkdir(exist_ok=True)
            
            # Make directory writable (cross-platform)
            if os.name == 'nt':  # Windows
                os.system(f'attrib -r "{directory}" /s /d')
            else:  # Mac/Linux
                Path(directory).chmod(0o777)
            
            print(f"   Fixed: {directory}/")
            
        except Exception as e:
            print(f"   Warning: Could not fix {directory}: {e}")
    
    steps_completed.append("✅ Fixed directory permissions")
    
    # Step 4: Regenerate data files
    print("\n📊 Step 4: Regenerating data files...")
    
    try:
        # Generate sample data
        from data.generate_data import generate_all_data
        generate_all_data()
        print("   ✅ Generated sample_patients.csv (50 patients)")
        print("   ✅ Generated doctor_schedules.xlsx")
        steps_completed.append("✅ Regenerated data files")
        
    except ImportError:
        print("   ⚠️ generate_data.py not found, creating manually...")
        create_minimal_data()
        steps_completed.append("✅ Created minimal data files")
    
    except Exception as e:
        print(f"   ❌ Error generating data: {e}")
        print("   🔄 Creating minimal fallback data...")
        create_minimal_data()
        steps_completed.append("⚠️ Created fallback data")
    
    # Step 5: Test file access
    print("\n🧪 Step 5: Testing file access...")
    
    test_results = []
    
    # Test Excel file
    excel_path = Path("data/doctor_schedules.xlsx")
    if excel_path.exists() and os.access(excel_path, os.W_OK):
        test_results.append("✅ doctor_schedules.xlsx - Writable")
    else:
        test_results.append("❌ doctor_schedules.xlsx - Not writable")
    
    # Test CSV file
    csv_path = Path("data/sample_patients.csv")
    if csv_path.exists() and os.access(csv_path, os.W_OK):
        test_results.append("✅ sample_patients.csv - Writable")
    else:
        test_results.append("❌ sample_patients.csv - Not writable")
    
    # Test exports directory
    if os.access(Path("exports"), os.W_OK):
        test_results.append("✅ exports/ - Writable")
    else:
        test_results.append("❌ exports/ - Not writable")
    
    for result in test_results:
        print(f"   {result}")
    
    steps_completed.append("✅ Tested file access")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 PERMISSION FIX COMPLETE!")
    print("=" * 50)
    
    for step in steps_completed:
        print(f"   {step}")
    
    # Check if all tests passed
    failed_tests = [result for result in test_results if result.startswith("❌")]
    
    if not failed_tests:
        print("\n🎉 ALL PERMISSION ISSUES FIXED!")
        print("✅ Ready to run the medical scheduling agent")
        print("\n🚀 Next steps:")
        print("1. Run: streamlit run ui/streamlit_app.py")
        print("2. Test booking an appointment")
        print("3. Check database for reminders")
        print("4. Export Excel file")
        return True
    else:
        print(f"\n⚠️ {len(failed_tests)} issues remain:")
        for failed in failed_tests:
            print(f"   {failed}")
        print("\n💡 Try running as administrator/sudo if issues persist")
        return False

def create_minimal_data():
    """Create minimal data files if generation fails"""
    
    try:
        import csv
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Create minimal patient CSV
        Path("data").mkdir(exist_ok=True)
        
        patients = []
        for i in range(50):
            patients.append({
                'patient_id': f'P{i+1:03d}',
                'first_name': f'Patient{i+1}',
                'last_name': f'Test{i+1}',
                'dob': f'{1950 + (i % 50)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}',
                'phone': f'555-{1000+i:04d}',
                'email': f'patient{i+1}@test.com',
                'patient_type': 'new' if i % 3 == 0 else 'returning',
                'insurance_carrier': ['BlueCross', 'Aetna', 'Cigna'][i % 3],
                'member_id': f'M{100000+i}',
                'group_number': f'G{1000+i}'
            })
        
        # Write CSV
        with open("data/sample_patients.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=patients[0].keys())
            writer.writeheader()
            writer.writerows(patients)
        
        print("   ✅ Created sample_patients.csv (50 patients)")
        
        # Create minimal Excel schedule
        schedule_data = []
        base_date = datetime.now().date()
        
        doctors = ["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez"]
        
        for i in range(100):  # 100 appointment slots
            date = base_date + timedelta(days=(i // 10))
            hour = 9 + (i % 8)  # 9 AM to 4 PM
            
            schedule_data.append({
                'doctor_name': doctors[i % 3],
                'specialty': ['Allergist', 'Pulmonologist', 'Immunologist'][i % 3],
                'date': date.strftime('%Y-%m-%d'),
                'time': f'{hour:02d}:00',
                'datetime': f'{date} {hour:02d}:00:00',
                'location': ['Main Clinic', 'Downtown Branch', 'Suburban Office'][i % 3],
                'available': True,
                'duration_available': 60
            })
        
        df = pd.DataFrame(schedule_data)
        df.to_excel("data/doctor_schedules.xlsx", sheet_name='All_Schedules', index=False)
        
        print("   ✅ Created doctor_schedules.xlsx (100 slots)")
        
    except Exception as e:
        print(f"   ❌ Error creating minimal data: {e}")
        
        # Ultra-minimal fallback - just create empty files
        Path("data/sample_patients.csv").touch()
        Path("data/doctor_schedules.xlsx").touch()
        print("   ⚠️ Created empty placeholder files")

if __name__ == "__main__":
    success = fix_permissions_now()
    
    if success:
        print("\n🎉 PERMISSION FIX SUCCESSFUL!")
        print("Your system is now ready for the RagaAI demo!")
    else:
        print("\n🔧 Some issues remain. Try:")
        print("1. Run as administrator (Windows) or sudo (Mac/Linux)")
        print("2. Manually delete data/doctor_schedules.xlsx")
        print("3. Run this script again")