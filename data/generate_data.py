"""
Sample Data Generator for AI Medical Scheduling Agent
RagaAI Assignment - Generate 50 patients + doctor schedules as required
"""

import csv
import json
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_patients_csv(num_patients: int = 50) -> str:
    """Generate CSV file with sample patients as required by assignment"""
    
    try:
        from faker import Faker
    except ImportError:
        logger.warning("Faker not installed, using simple name generation")
        # Simple fallback without Faker
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Mark", "Anna", "Chris", "Maria"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        fake = None
    else:
        fake = Faker()
        first_names = None
        last_names = None
    
    patients = []
    
    # Insurance carriers
    insurance_carriers = [
        "BlueCross BlueShield",
        "Aetna",
        "Cigna", 
        "UnitedHealthcare",
        "Kaiser Permanente",
        "Humana"
    ]
    
    relationships = ["Spouse", "Parent", "Child", "Sibling", "Friend", "Partner"]
    
    for i in range(num_patients):
        if fake:
            first_name = fake.first_name()
            last_name = fake.last_name()
            dob = fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%Y-%m-%d")
            phone = fake.phone_number()[:12]  # Limit length
        else:
            first_name = first_names[i % len(first_names)]
            last_name = last_names[i % len(last_names)]
            year = random.randint(1950, 2000)
            month = random.randint(1, 12)
            day = random.randint(1, 28)
            dob = f"{year}-{month:02d}-{day:02d}"
            phone = f"555-{1000+i:04d}"
        
        patient = {
            "patient_id": f"P{i+1:03d}",
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "phone": phone,
            "email": f"{first_name.lower()}.{last_name.lower()}{i}@email.com",
            "patient_type": random.choice(["new"] + ["returning"] * 2),  # 2/3 returning
            "insurance_carrier": random.choice(insurance_carriers),
            "member_id": f"M{random.randint(100000, 999999)}",
            "group_number": f"G{random.randint(1000, 9999)}",
            "emergency_contact_name": fake.name() if fake else f"Emergency Contact {i}",
            "emergency_contact_phone": fake.phone_number()[:12] if fake else f"555-{2000+i:04d}",
            "emergency_contact_relationship": random.choice(relationships)
        }
        patients.append(patient)
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Write to CSV
    csv_file = "data/sample_patients.csv"
    with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = patients[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(patients)
    
    logger.info(f"Generated {csv_file} with {num_patients} patients")
    return csv_file

def generate_doctor_schedules_excel() -> str:
    """Generate Excel file with doctor schedules as required"""
    
    try:
        import pandas as pd
    except ImportError:
        logger.error("pandas required for Excel generation")
        return ""
    
    # Available doctors (as specified in assignment)
    doctors = [
        {"id": "dr_johnson", "name": "Dr. Sarah Johnson", "specialty": "Allergist"},
        {"id": "dr_chen", "name": "Dr. Michael Chen", "specialty": "Pulmonologist"},
        {"id": "dr_rodriguez", "name": "Dr. Emily Rodriguez", "specialty": "Immunologist"}
    ]
    
    # Available locations
    locations = [
        "Main Clinic - Healthcare Boulevard",
        "Downtown Branch - Medical Center",
        "Suburban Office - Wellness Plaza"
    ]
    
    # Generate schedules for next 30 days
    schedules_data = []
    base_date = datetime.now().date()
    
    for doctor in doctors:
        for day_offset in range(30):
            current_date = base_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Generate time slots (9 AM to 5 PM, 30-minute intervals)
            current_time = datetime.combine(current_date, datetime.min.time().replace(hour=9))
            end_time = datetime.combine(current_date, datetime.min.time().replace(hour=17))
            
            while current_time < end_time:
                # 75% chance slot is available
                if random.random() > 0.25:
                    schedule_entry = {
                        "doctor_id": doctor["id"],
                        "doctor_name": doctor["name"],
                        "specialty": doctor["specialty"],
                        "date": current_date.strftime("%Y-%m-%d"),
                        "time": current_time.strftime("%H:%M"),
                        "datetime": current_time.strftime("%Y-%m-%d %H:%M"),
                        "location": random.choice(locations),
                        "available": True,
                        "duration_available": random.choice([30, 60, 90]),
                        "appointment_type": random.choice([
                            "Consultation", "Follow-up", "Allergy Testing", "Treatment"
                        ])
                    }
                    schedules_data.append(schedule_entry)
                
                # Move to next 30-minute slot
                current_time += timedelta(minutes=30)
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(schedules_data)
    
    excel_file = "data/doctor_schedules.xlsx"
    
    try:
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Main schedule sheet
            df.to_excel(writer, sheet_name='All_Schedules', index=False)
            
            # Individual doctor sheets
            for doctor in doctors:
                doctor_df = df[df['doctor_id'] == doctor['id']]
                sheet_name = doctor['name'].replace('Dr. ', '').replace(' ', '_')
                if len(sheet_name) <= 31:  # Excel sheet name limit
                    doctor_df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Summary sheet
            summary_data = []
            for doctor in doctors:
                doctor_slots = df[df['doctor_id'] == doctor['id']]
                summary_data.append({
                    'Doctor': doctor['name'],
                    'Specialty': doctor['specialty'],
                    'Total_Available_Slots': len(doctor_slots),
                    'Locations': len(doctor_slots['location'].unique()),
                    'Date_Range': f"{df['date'].min()} to {df['date'].max()}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Generated {excel_file} with {len(schedules_data)} available slots")
        return excel_file
        
    except Exception as e:
        logger.error(f"Error creating Excel file: {e}")
        return ""

def generate_sample_export() -> str:
    """Generate a sample Excel export file"""
    
    try:
        import pandas as pd
    except ImportError:
        return ""
    
    # Sample appointment data
    sample_appointments = []
    
    for i in range(20):
        appointment = {
            "Appointment_ID": f"APT{1000 + i}",
            "Patient_Name": f"Patient {i+1}",
            "Patient_Email": f"patient{i+1}@email.com",
            "Patient_Phone": f"555-{3000+i:04d}",
            "Doctor": random.choice(["Dr. Sarah Johnson", "Dr. Michael Chen", "Dr. Emily Rodriguez"]),
            "Location": random.choice(["Main Clinic", "Downtown Branch", "Suburban Office"]),
            "Date": (datetime.now() + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d"),
            "Time": random.choice(["09:00", "09:30", "10:00", "10:30", "11:00", "14:00", "14:30", "15:00"]),
            "Duration": random.choice([30, 60]),
            "Status": random.choice(["Scheduled", "Confirmed", "Completed"]),
            "Patient_Type": random.choice(["New", "Returning"]),
            "Insurance_Carrier": random.choice(["BlueCross", "Aetna", "Cigna", "UnitedHealth"])
        }
        sample_appointments.append(appointment)
    
    df = pd.DataFrame(sample_appointments)
    
    # Ensure exports directory exists
    Path("exports").mkdir(exist_ok=True)
    
    export_file = "exports/sample_export.xlsx"
    try:
        with pd.ExcelWriter(export_file, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Appointments', index=False)
            
            # Summary sheet
            summary = {
                "Metric": ["Total Appointments", "New Patients", "Returning Patients", "Average Duration"],
                "Value": [
                    len(df),
                    len(df[df['Patient_Type'] == 'New']),
                    len(df[df['Patient_Type'] == 'Returning']),
                    f"{df['Duration'].mean():.1f} minutes"
                ]
            }
            summary_df = pd.DataFrame(summary)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        logger.info(f"Generated {export_file}")
        return export_file
        
    except Exception as e:
        logger.error(f"Error creating sample export: {e}")
        return ""

def create_gitkeep_files():
    """Create .gitkeep files for empty directories"""
    
    directories = ["exports", "logs"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        gitkeep_file = Path(directory) / ".gitkeep"
        with open(gitkeep_file, "w") as f:
            f.write("# Keep directory in git\n")

def generate_all_data():
    """Generate all required sample data"""
    
    logger.info("Generating all sample data for medical scheduling agent...")
    
    try:
        # Generate patients CSV (required)
        patients_file = generate_patients_csv(50)
        
        # Generate doctor schedules Excel (required)
        schedules_file = generate_doctor_schedules_excel()
        
        # Generate sample export
        export_file = generate_sample_export()
        
        # Create .gitkeep files
        create_gitkeep_files()
        
        logger.info("Sample data generation completed!")
        logger.info(f"Files created:")
        if patients_file:
            logger.info(f"  - {patients_file} (50 patients)")
        if schedules_file:
            logger.info(f"  - {schedules_file} (doctor schedules)")
        if export_file:
            logger.info(f"  - {export_file} (sample export)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate sample data: {e}")
        return False

if __name__ == "__main__":
    generate_all_data()