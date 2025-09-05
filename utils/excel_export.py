"""
Excel Export Functionality for Medical Scheduling Agent
RagaAI Assignment - Admin Excel Reports Generation
"""

import pandas as pd
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Handle Excel export functionality for admin reports"""
    
    def __init__(self):
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)
    
    def export_data(self, export_type: str, start_date, end_date, include_details: bool = True) -> str:
        """Export data based on type and date range"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{export_type}_{timestamp}.xlsx"
        filepath = self.exports_dir / filename
        
        try:
            if export_type == "all_appointments":
                self._export_appointments(filepath, start_date, end_date, include_details)
            elif export_type == "patient_list":
                self._export_patients(filepath, include_details)
            elif export_type == "doctor_schedules":
                self._export_doctor_schedules(filepath)
            elif export_type == "analytics_summary":
                self._export_analytics(filepath, start_date, end_date)
            else:
                raise ValueError(f"Unknown export type: {export_type}")
            
            logger.info(f"Export completed: {filename}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Export failed: {e}")
            raise e
    
    def _export_appointments(self, filepath: Path, start_date, end_date, include_details: bool):
        """Export appointments data"""
        
        # Mock appointment data for demo
        appointments_data = {
            'Appointment_ID': [f'APT{1000+i}' for i in range(20)],
            'Patient_Name': ['John Doe', 'Jane Smith', 'Mike Johnson'] * 7 + ['Sarah Wilson'],
            'Patient_Email': ['john@email.com', 'jane@email.com', 'mike@email.com'] * 7 + ['sarah@email.com'],
            'Patient_Phone': ['555-1234', '555-5678', '555-9012'] * 7 + ['555-3456'],
            'Doctor': ['Dr. Sarah Johnson', 'Dr. Michael Chen', 'Dr. Emily Rodriguez'] * 7 + ['Dr. Sarah Johnson'],
            'Location': ['Main Clinic', 'Downtown Branch', 'Suburban Office'] * 7 + ['Main Clinic'],
            'Date': pd.date_range(start='2024-09-01', periods=20, freq='D').strftime('%Y-%m-%d').tolist(),
            'Time': ['09:00', '10:30', '14:00', '15:30'] * 5,
            'Duration': [60, 30, 60, 30] * 5,
            'Status': ['Scheduled', 'Confirmed', 'Completed'] * 6 + ['Scheduled', 'Confirmed'],
            'Patient_Type': ['New', 'Returning'] * 10,
            'Insurance_Carrier': ['BlueCross', 'Aetna', 'Cigna'] * 6 + ['BlueCross', 'Aetna']
        }
        
        df = pd.DataFrame(appointments_data)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Appointments', index=False)
            
            if include_details:
                # Summary statistics
                summary_data = {
                    'Metric': ['Total Appointments', 'New Patients', 'Returning Patients', 'Completed', 'No Shows'],
                    'Count': [len(df), len(df[df['Patient_Type']=='New']), 
                             len(df[df['Patient_Type']=='Returning']),
                             len(df[df['Status']=='Completed']), 2]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    def _export_patients(self, filepath: Path, include_details: bool):
        """Export patient database"""
        
        # Try to load real patient data from CSV
        try:
            df = pd.read_csv("data/sample_patients.csv")
        except FileNotFoundError:
            # Create mock data if CSV doesn't exist
            df = pd.DataFrame({
                'patient_id': [f'P{i:03d}' for i in range(1, 51)],
                'first_name': ['John', 'Jane', 'Mike'] * 16 + ['Sarah', 'Tom'],
                'last_name': ['Doe', 'Smith', 'Johnson'] * 16 + ['Wilson', 'Brown'],
                'dob': pd.date_range('1960-01-01', periods=50, freq='365D').strftime('%Y-%m-%d'),
                'email': [f'patient{i}@email.com' for i in range(1, 51)],
                'phone': [f'555-{1000+i:04d}' for i in range(50)],
                'patient_type': ['new', 'returning'] * 25,
                'insurance_carrier': ['BlueCross', 'Aetna', 'Cigna', 'UnitedHealth'] * 12 + ['BlueCross', 'Aetna']
            })
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Patients', index=False)
            
            if include_details:
                # Patient statistics
                stats = {
                    'Patient Type': ['New', 'Returning'],
                    'Count': [len(df[df['patient_type']=='new']), len(df[df['patient_type']=='returning'])]
                }
                stats_df = pd.DataFrame(stats)
                stats_df.to_excel(writer, sheet_name='Patient_Stats', index=False)
    
    def _export_doctor_schedules(self, filepath: Path):
        """Export doctor schedules"""
        
        # Try to load from existing Excel file
        try:
            existing_df = pd.read_excel("data/doctor_schedules.xlsx", sheet_name="All_Schedules")
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                existing_df.to_excel(writer, sheet_name='Doctor_Schedules', index=False)
        except FileNotFoundError:
            # Create mock schedule data
            dates = pd.date_range('2024-09-01', periods=14, freq='D')
            schedule_data = []
            
            doctors = ['Dr. Sarah Johnson', 'Dr. Michael Chen', 'Dr. Emily Rodriguez']
            locations = ['Main Clinic', 'Downtown Branch', 'Suburban Office']
            times = ['09:00', '09:30', '10:00', '10:30', '11:00', '14:00', '14:30', '15:00', '15:30', '16:00']
            
            for date in dates:
                if date.weekday() < 5:  # Weekdays only
                    for doctor in doctors:
                        for time in times[:5]:  # 5 slots per doctor per day
                            schedule_data.append({
                                'Date': date.strftime('%Y-%m-%d'),
                                'Time': time,
                                'Doctor': doctor,
                                'Location': locations[doctors.index(doctor) % 3],
                                'Available': True,
                                'Duration': 30
                            })
            
            df = pd.DataFrame(schedule_data)
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Doctor_Schedules', index=False)
    
    def _export_analytics(self, filepath: Path, start_date, end_date):
        """Export analytics summary"""
        
        # Mock analytics data
        analytics_data = {
            'appointments_scheduled': 145,
            'appointments_completed': 132,
            'no_show_rate': 5.2,
            'new_patients': 42,
            'returning_patients': 103,
            'average_duration': 38.5,
            'revenue_estimated': 12450.00,
            'form_completion_rate': 92.3,
            'reminder_response_rate': 78.6
        }
        
        # Convert to DataFrame
        metrics_df = pd.DataFrame([
            {'Metric': 'Appointments Scheduled', 'Value': analytics_data['appointments_scheduled']},
            {'Metric': 'Appointments Completed', 'Value': analytics_data['appointments_completed']},
            {'Metric': 'No-Show Rate (%)', 'Value': analytics_data['no_show_rate']},
            {'Metric': 'New Patients', 'Value': analytics_data['new_patients']},
            {'Metric': 'Returning Patients', 'Value': analytics_data['returning_patients']},
            {'Metric': 'Average Duration (min)', 'Value': analytics_data['average_duration']},
            {'Metric': 'Estimated Revenue ($)', 'Value': analytics_data['revenue_estimated']},
            {'Metric': 'Form Completion Rate (%)', 'Value': analytics_data['form_completion_rate']},
            {'Metric': 'Reminder Response Rate (%)', 'Value': analytics_data['reminder_response_rate']}
        ])
        
        # Daily breakdown
        daily_data = pd.DataFrame({
            'Date': pd.date_range(start_date, end_date, freq='D'),
            'Appointments': [5, 8, 6, 7, 9, 4, 2] * 2,  # Mock daily appointments
            'New_Patients': [2, 3, 1, 2, 3, 1, 0] * 2,
            'No_Shows': [0, 1, 0, 0, 1, 0, 0] * 2
        })
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            metrics_df.to_excel(writer, sheet_name='Key_Metrics', index=False)
            daily_data.to_excel(writer, sheet_name='Daily_Breakdown', index=False)
            
            # Doctor performance
            doctor_performance = pd.DataFrame({
                'Doctor': ['Dr. Sarah Johnson', 'Dr. Michael Chen', 'Dr. Emily Rodriguez'],
                'Appointments': [48, 41, 56],
                'Patient_Satisfaction': [4.7, 4.5, 4.8],
                'No_Show_Rate': [4.2, 6.1, 5.4],
                'Revenue': [4200, 3650, 4600]
            })
            doctor_performance.to_excel(writer, sheet_name='Doctor_Performance', index=False)