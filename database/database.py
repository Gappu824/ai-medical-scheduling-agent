"""
Database Manager for Medical Scheduling Agent - Fixed Syntax
RagaAI Assignment - Complete SQLite Database Operations
"""

import sqlite3
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from database.models import Patient, Appointment, PatientType, AppointmentStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Complete database manager for medical scheduling"""
    
    def __init__(self, db_path: str = "medical_scheduling.db"):
        self.db_path = db_path
        self.init_database()
        self.load_sample_data()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
        # ... (code remains the same as your correct version)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Patients table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            dob TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            patient_type TEXT NOT NULL,
            insurance_carrier TEXT,
            member_id TEXT,
            group_number TEXT,
            emergency_contact_name TEXT,
            emergency_contact_phone TEXT,
            emergency_contact_relationship TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Appointments table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id TEXT PRIMARY KEY,
            patient_id TEXT NOT NULL,
            doctor TEXT NOT NULL,
            location TEXT NOT NULL,
            appointment_datetime TEXT NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        )
        """)
        
        cursor.execute("""
CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL CHECK(reminder_type IN ('initial', 'form_check', 'final_confirmation')),
    scheduled_time TEXT NOT NULL,
    sent BOOLEAN DEFAULT FALSE,
    email_sent BOOLEAN DEFAULT FALSE,
    sms_sent BOOLEAN DEFAULT FALSE,
    response_received BOOLEAN DEFAULT FALSE,
    response_data TEXT,
    attempts INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (appointment_id) REFERENCES appointments (id)
)
""")
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    
    def load_sample_data(self):
        """Load sample patients from CSV if not already loaded"""
        # ... (code remains the same as your correct version)
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if data exists
        cursor.execute("SELECT COUNT(*) FROM patients")
        count = cursor.fetchone()[0]
        
        if count > 0:
            conn.close()
            return
        
        # Load from CSV file
        csv_path = Path("data/sample_patients.csv")
        if not csv_path.exists():
            logger.warning("Sample patients CSV not found")
            conn.close()
            return
        
        try:
            with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    cursor.execute("""
                    INSERT OR IGNORE INTO patients (
                        id, first_name, last_name, dob, phone, email, patient_type,
                        insurance_carrier, member_id, group_number,
                        emergency_contact_name, emergency_contact_phone, emergency_contact_relationship
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['patient_id'],
                        row['first_name'],
                        row['last_name'], 
                        row['dob'],
                        row['phone'],
                        row['email'],
                        row['patient_type'],
                        row.get('insurance_carrier'),
                        row.get('member_id'),
                        row.get('group_number'),
                        row.get('emergency_contact_name'),
                        row.get('emergency_contact_phone'),
                        row.get('emergency_contact_relationship')
                    ))
            
            conn.commit()
            logger.info(f"Loaded sample patients from CSV")
            
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
        
        conn.close()
    
    def find_patient(self, first_name: str, last_name: str, dob: str) -> Optional[Patient]:
        """Find patient by name and DOB"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Build query dynamically to handle cases where dob is not provided for lookup
        query = "SELECT * FROM patients WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)"
        params = [first_name.strip(), last_name.strip()]
        
        if dob:
            query += " AND dob = ?"
            params.append(dob)

        cursor.execute(query, tuple(params))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Patient(
                id=row['id'],
                first_name=row['first_name'],
                last_name=row['last_name'],
                dob=row['dob'],
                phone=row['phone'],
                email=row['email'],
                patient_type=PatientType(row['patient_type'])
            )
        return None
    
    def create_patient(self, patient_data: Dict) -> Patient:
        """Create new patient record in the database."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        patient_id = f"P{int(datetime.now().timestamp())}"
        
        cursor.execute("""
        INSERT INTO patients (
            id, first_name, last_name, dob, phone, email, patient_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            patient_data["first_name"],
            patient_data["last_name"],
            patient_data["dob"],
            patient_data.get("phone", ""),
            patient_data.get("email", ""),
            PatientType.NEW.value
        ))
        
        conn.commit()
        conn.close()
        logger.info(f"Successfully created patient {patient_id} in the database.")
        
        return self.find_patient(patient_data["first_name"], patient_data["last_name"], patient_data["dob"])

    def create_appointment(self, appointment: Appointment) -> bool:
        """Create new appointment"""
        # ... (code remains the same as your correct version)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            INSERT INTO appointments (
                id, patient_id, doctor, location, appointment_datetime, 
                duration, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                appointment.id,
                appointment.patient_id,
                appointment.doctor,
                appointment.location,
                appointment.appointment_datetime.isoformat(),
                appointment.duration,
                appointment.status.value,
                appointment.notes
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return False

    # ... (other methods remain the same)