"""
Database Manager for Medical Scheduling Agent
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
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database with all required tables"""
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
        
        # Reminders table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL,
            scheduled_time TEXT NOT NULL,
            sent BOOLEAN DEFAULT FALSE,
            response TEXT,
            sent_at TIMESTAMP,
            delivery_status TEXT DEFAULT 'pending',
            channel TEXT DEFAULT 'email',
            priority TEXT DEFAULT 'normal',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id)
        )
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def load_sample_data(self):
        """Load sample patients from CSV if not already loaded"""
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
                    INSERT INTO patients (
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
            logger.info(f"Loaded {cursor.rowcount} sample patients from CSV")
            
        except Exception as e:
            logger.error(f"Error loading sample data: {e}")
        
        conn.close()
    
    def find_patient(self, first_name: str, last_name: str, dob: str) -> Optional[Patient]:
        """Find patient by name and DOB"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM patients 
        WHERE LOWER(first_name) = LOWER(?) 
        AND LOWER(last_name) = LOWER(?) 
        AND dob = ?
        """, (first_name.strip(), last_name.strip(), dob))
        
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
                patient_type=PatientType(row['patient_type']),
                insurance_carrier=row['insurance_carrier'],
                member_id=row['member_id'],
                group_number=row['group_number'],
                emergency_contact_name=row['emergency_contact_name'],
                emergency_contact_phone=row['emergency_contact_phone'],
                emergency_contact_relationship=row['emergency_contact_relationship']
            )
        return None
    
    def create_patient(self, patient_data: Dict) -> Patient:
        """Create new patient record"""
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
            "new"
        ))
        
        conn.commit()
        conn.close()
        
        return Patient(
            id=patient_id,
            first_name=patient_data["first_name"],
            last_name=patient_data["last_name"],
            dob=patient_data["dob"],
            phone=patient_data.get("phone", ""),
            email=patient_data.get("email", ""),
            patient_type=PatientType.NEW
        )
    
    def create_appointment(self, appointment: Appointment) -> bool:
        """Create new appointment"""
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
    
    def get_all_patients(self) -> List[Dict]:
        """Get all patients for admin view"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM patients ORDER BY last_name, first_name")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_appointments_by_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """Get appointments within date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT a.*, p.first_name, p.last_name, p.email, p.phone
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        WHERE DATE(a.appointment_datetime) BETWEEN ? AND ?
        ORDER BY a.appointment_datetime
        """, (start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_patient_insurance(self, patient_id: str, insurance_data: Dict) -> bool:
        """Update patient insurance information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
            UPDATE patients 
            SET insurance_carrier = ?, member_id = ?, group_number = ?
            WHERE id = ?
            """, (
                insurance_data.get('carrier'),
                insurance_data.get('member_id'), 
                insurance_data.get('group_number'),
                patient_id
            ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error updating insurance: {e}")
            return False