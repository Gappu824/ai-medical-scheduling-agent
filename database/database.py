"""
Database Manager for Medical Scheduling Agent - FINAL STABLE VERSION
RagaAI Assignment - With Flexible Search and Stable Connection Management
"""

import sqlite3
import logging
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import pandas as pd

try:
    from database.models import Patient, Appointment, PatientType, AppointmentStatus
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from database.models import Patient, Appointment, PatientType, AppointmentStatus

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Complete database manager for medical scheduling"""
    
    def __init__(self, db_path: str = "medical_scheduling.db"):
        self.db_path = db_path
        self.init_database()
        self.load_sample_data()
        self.load_schedules_from_excel_to_db()
    
    def get_connection(self) -> sqlite3.Connection:
        """Creates a new, fresh database connection for each request."""
        # FIX: Corrected typo from 'sqlite' to 'sqlite3'
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize all required database tables."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS patients (
                    id TEXT PRIMARY KEY, first_name TEXT NOT NULL, last_name TEXT NOT NULL,
                    dob TEXT NOT NULL, phone TEXT, email TEXT, patient_type TEXT NOT NULL,
                    insurance_carrier TEXT, member_id TEXT, group_number TEXT,
                    emergency_contact_name TEXT, emergency_contact_phone TEXT,
                    emergency_contact_relationship TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )""")
                conn.execute("""
                CREATE TABLE IF NOT EXISTS appointments (
                    id TEXT PRIMARY KEY, patient_id TEXT NOT NULL, doctor TEXT NOT NULL,
                    location TEXT NOT NULL, appointment_datetime TEXT NOT NULL,
                    duration INTEGER NOT NULL, status TEXT NOT NULL, notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (patient_id) REFERENCES patients (id)
                )""")
                conn.execute("""
                CREATE TABLE IF NOT EXISTS doctor_schedules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doctor_name TEXT NOT NULL,
                    datetime TEXT NOT NULL,
                    available BOOLEAN NOT NULL DEFAULT 1,
                    UNIQUE(doctor_name, datetime)
                )""")
            logger.info("Database initialized successfully.")
        finally:
            conn.close()

    def load_sample_data(self):
        """Load sample patients from CSV if not already loaded."""
        conn = self.get_connection()
        try:
            with conn:
                count = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
                if count > 0:
                    return
                
                csv_path = Path("data/sample_patients.csv")
                if not csv_path.exists():
                    logger.warning(f"Sample patients CSV not found at {csv_path}")
                    return
                
                with open(csv_path, 'r', newline='', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    patients_to_insert = [
                        (row['patient_id'], row['first_name'], row['last_name'], row['dob'], row['phone'], row['email'], row['patient_type'],
                         row.get('insurance_carrier'), row.get('member_id'), row.get('group_number'), row.get('emergency_contact_name'),
                         row.get('emergency_contact_phone'), row.get('emergency_contact_relationship'))
                        for row in reader
                    ]
                    if patients_to_insert:
                        conn.executemany("""
                        INSERT OR IGNORE INTO patients (
                            id, first_name, last_name, dob, phone, email, patient_type,
                            insurance_carrier, member_id, group_number, emergency_contact_name,
                            emergency_contact_phone, emergency_contact_relationship
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, patients_to_insert)
                        logger.info(f"Loaded {len(patients_to_insert)} sample patients.")
        finally:
            conn.close()

    def load_schedules_from_excel_to_db(self):
        """Loads schedule data from Excel into the database, if the table is empty."""
        conn = self.get_connection()
        try:
            with conn:
                count = conn.execute("SELECT COUNT(*) FROM doctor_schedules").fetchone()[0]
                if count > 0:
                    return

                excel_path = Path("data/doctor_schedules.xlsx")
                if not excel_path.exists():
                    logger.error(f"doctor_schedules.xlsx not found at {excel_path}! Cannot load schedules.")
                    return

                df = pd.read_excel(excel_path, sheet_name='All_Schedules')
                df['datetime'] = pd.to_datetime(df['datetime'])

                schedules_to_insert = [
                    (row['doctor_name'], row['datetime'].isoformat())
                    for index, row in df.iterrows() if row['available']
                ]
                if schedules_to_insert:
                    conn.executemany(
                        "INSERT OR IGNORE INTO doctor_schedules (doctor_name, datetime) VALUES (?, ?)",
                        schedules_to_insert
                    )
                    logger.info(f"Loaded available slots into the database.")
        finally:
            conn.close()

    def find_patient(self, first_name: str, last_name: str, dob: str = None) -> List[Patient]:
        """Flexibly finds patients. Each call uses its own connection."""
        conn = self.get_connection()
        try:
            query = "SELECT * FROM patients WHERE LOWER(first_name) = LOWER(?) AND LOWER(last_name) = LOWER(?)"
            params = [first_name.strip(), last_name.strip()]
            if dob:
                query += " AND dob = ?"
                params.append(dob)
            rows = conn.execute(query, tuple(params)).fetchall()
            patient_keys = Patient.__annotations__.keys()
            return [Patient(**{k: v for k, v in dict(row).items() if k in patient_keys}) for row in rows]
        finally:
            conn.close()

    def get_patient_by_id(self, patient_id: str) -> Optional[Patient]:
        """Retrieves a single patient by their unique ID."""
        conn = self.get_connection()
        try:
            row = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
            if not row: return None
            patient_keys = Patient.__annotations__.keys()
            return Patient(**{k: v for k, v in dict(row).items() if k in patient_keys})
        finally:
            conn.close()

    def get_patient_appointment_history(self, patient_id: str) -> List[Dict]:
        """Gets the most recent appointment history for a given patient."""
        conn = self.get_connection()
        try:
            history_rows = conn.execute(
                "SELECT doctor, location FROM appointments WHERE patient_id = ? ORDER BY appointment_datetime DESC LIMIT 1",
                (patient_id,)
            ).fetchall()
            return [{"doctor": row["doctor"], "location": row["location"]} for row in history_rows]
        finally:
            conn.close()
    # Around line 139 in database.py, fix patient creation:
    def create_patient(self, patient_data: Dict) -> Optional[Patient]:
        """Creates a new patient and returns the patient object."""
        conn = self.get_connection()
        patient_id = f"P{int(datetime.now().timestamp())}"
        try:
            with conn:
                conn.execute("""
                INSERT INTO patients (id, first_name, last_name, dob, phone, email, patient_type) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_id, patient_data["first_name"], patient_data["last_name"],
                    patient_data["dob"], patient_data.get("phone", ""),
                    patient_data.get("email", ""), "new"  # Explicitly set as "new"
                ))
            return self.get_patient_by_id(patient_id)
        except sqlite3.Error as e:
            logger.error(f"Failed to create patient: {e}")
            return None
        finally:
            conn.close()

    def create_appointment(self, appointment: Appointment) -> bool:
        """Creates a new appointment record."""
        conn = self.get_connection()
        try:
            with conn:
                conn.execute("""
                INSERT INTO appointments (id, patient_id, doctor, location, appointment_datetime, duration, status, notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    appointment.id, appointment.patient_id, appointment.doctor,
                    appointment.location, appointment.appointment_datetime.isoformat(),
                    appointment.duration, appointment.status.value, appointment.notes
                ))
            return True
        except sqlite3.Error as e:
            logger.error(f"Error creating appointment: {e}")
            return False
        finally:
            conn.close()