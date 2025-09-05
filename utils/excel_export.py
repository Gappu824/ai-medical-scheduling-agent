"""
Production Excel Export System with Real Data
RagaAI Assignment - Real Excel Generation with Database Integration
"""

import pandas as pd
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class ExcelExporter:
    """Production Excel export system with real database integration"""
    
    def __init__(self):
        self.exports_dir = Path("exports")
        self.exports_dir.mkdir(exist_ok=True)
        self.db_path = "medical_scheduling.db"
        
        logger.info("Production Excel Exporter initialized")
    
    def export_appointment_data(self, appointment_id: str) -> str:
        """Export specific appointment data with complete details"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get complete appointment details
            query = """
            SELECT 
                a.id as appointment_id,
                a.appointment_datetime,
                a.doctor,
                a.location,
                a.duration,
                a.status,
                a.created_at as booking_date,
                p.id as patient_id,
                p.first_name,
                p.last_name,
                p.dob,
                p.phone,
                p.email,
                p.patient_type,
                p.insurance_carrier,
                p.member_id,
                p.group_number,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.emergency_contact_relationship
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE a.id = ?
            """
            
            df = pd.read_sql_query(query, conn, params=[appointment_id])
            
            if df.empty:
                logger.warning(f"No appointment found with ID: {appointment_id}")
                return None
            
            # Get reminder data
            reminder_query = """
            SELECT 
                reminder_type,
                scheduled_time,
                sent,
                email_sent,
                sms_sent,
                response_received,
                attempts
            FROM reminders
            WHERE appointment_id = ?
            ORDER BY scheduled_time
            """
            
            reminders_df = pd.read_sql_query(reminder_query, conn, params=[appointment_id])
            
            # Get response data
            response_query = """
            SELECT 
                response_type,
                response_channel,
                response_content,
                received_at
            FROM reminder_responses
            WHERE appointment_id = ?
            ORDER BY received_at
            """
            
            responses_df = pd.read_sql_query(response_query, conn, params=[appointment_id])
            
            conn.close()
            
            # Create Excel file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"appointment_{appointment_id}_{timestamp}.xlsx"
            filepath = self.exports_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main appointment details
                appointment_details = df.copy()
                appointment_details['patient_name'] = appointment_details['first_name'] + ' ' + appointment_details['last_name']
                appointment_details['appointment_date'] = pd.to_datetime(appointment_details['appointment_datetime']).dt.date
                appointment_details['appointment_time'] = pd.to_datetime(appointment_details['appointment_datetime']).dt.time
                
                appointment_details.to_excel(writer, sheet_name='Appointment_Details', index=False)
                
                # Patient information sheet
                patient_info = df[['patient_id', 'first_name', 'last_name', 'dob', 'phone', 'email', 
                                 'patient_type', 'insurance_carrier', 'member_id', 'group_number',
                                 'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship']].copy()
                patient_info.to_excel(writer, sheet_name='Patient_Information', index=False)
                
                # Reminder tracking
                if not reminders_df.empty:
                    reminders_df.to_excel(writer, sheet_name='Reminder_Tracking', index=False)
                
                # Patient responses
                if not responses_df.empty:
                    responses_df.to_excel(writer, sheet_name='Patient_Responses', index=False)
                
                # Summary sheet
                summary_data = {
                    'Field': [
                        'Appointment ID',
                        'Patient Name',
                        'Doctor',
                        'Date & Time',
                        'Location',
                        'Duration (minutes)',
                        'Patient Type',
                        'Status',
                        'Insurance Carrier',
                        'Reminders Scheduled',
                        'Reminders Sent',
                        'Patient Responses',
                        'Export Date'
                    ],
                    'Value': [
                        df.iloc[0]['appointment_id'],
                        f"{df.iloc[0]['first_name']} {df.iloc[0]['last_name']}",
                        df.iloc[0]['doctor'],
                        df.iloc[0]['appointment_datetime'],
                        df.iloc[0]['location'],
                        df.iloc[0]['duration'],
                        df.iloc[0]['patient_type'],
                        df.iloc[0]['status'],
                        df.iloc[0]['insurance_carrier'] or 'Not provided',
                        len(reminders_df),
                        len(reminders_df[reminders_df['sent'] == True]) if not reminders_df.empty else 0,
                        len(responses_df),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            logger.info(f"✅ Appointment export created: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Appointment export failed: {e}")
            return None
    
    def export_patient_list(self, start_date: datetime = None, end_date: datetime = None, 
                           patient_type: str = None) -> str:
        """Export patient list with filtering options"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Build query with filters
            where_conditions = []
            params = []
            
            if start_date:
                where_conditions.append("p.created_at >= ?")
                params.append(start_date.strftime('%Y-%m-%d'))
            
            if end_date:
                where_conditions.append("p.created_at <= ?")
                params.append(end_date.strftime('%Y-%m-%d'))
            
            if patient_type:
                where_conditions.append("p.patient_type = ?")
                params.append(patient_type)
            
            where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
            
            # Main patient query
            query = f"""
            SELECT 
                p.id as patient_id,
                p.first_name,
                p.last_name,
                p.dob,
                p.phone,
                p.email,
                p.patient_type,
                p.insurance_carrier,
                p.member_id,
                p.group_number,
                p.emergency_contact_name,
                p.emergency_contact_phone,
                p.emergency_contact_relationship,
                p.created_at,
                COUNT(a.id) as total_appointments,
                MAX(a.appointment_datetime) as last_appointment,
                MIN(a.appointment_datetime) as first_appointment
            FROM patients p
            LEFT JOIN appointments a ON p.id = a.patient_id
            {where_clause}
            GROUP BY p.id
            ORDER BY p.last_name, p.first_name
            """
            
            patients_df = pd.read_sql_query(query, conn, params=params)
            
            if patients_df.empty:
                logger.warning("No patients found with specified criteria")
                return None
            
            # Calculate ages
            patients_df['dob'] = pd.to_datetime(patients_df['dob'])
            patients_df['age'] = (datetime.now() - patients_df['dob']).dt.days // 365
            patients_df['full_name'] = patients_df['first_name'] + ' ' + patients_df['last_name']
            
            # Create filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"patient_list_{timestamp}.xlsx"
            filepath = self.exports_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Main patient list
                export_columns = [
                    'patient_id', 'full_name', 'first_name', 'last_name', 'dob', 'age',
                    'phone', 'email', 'patient_type', 'insurance_carrier', 'member_id',
                    'group_number', 'total_appointments', 'first_appointment', 'last_appointment',
                    'emergency_contact_name', 'emergency_contact_phone', 'emergency_contact_relationship'
                ]
                
                patients_export = patients_df[export_columns].copy()
                patients_export.to_excel(writer, sheet_name='Patient_List', index=False)
                
                # Statistics sheet
                stats_data = {
                    'Metric': [
                        'Total Patients',
                        'New Patients',
                        'Returning Patients',
                        'Average Age',
                        'Patients with Appointments',
                        'Patients with Insurance',
                        'Most Common Insurance',
                        'Age Range',
                        'Export Date',
                        'Filter Applied'
                    ],
                    'Value': [
                        len(patients_df),
                        len(patients_df[patients_df['patient_type'] == 'new']),
                        len(patients_df[patients_df['patient_type'] == 'returning']),
                        f"{patients_df['age'].mean():.1f} years",
                        len(patients_df[patients_df['total_appointments'] > 0]),
                        len(patients_df[patients_df['insurance_carrier'].notna()]),
                        patients_df['insurance_carrier'].mode().iloc[0] if not patients_df['insurance_carrier'].mode().empty else 'None',
                        f"{patients_df['age'].min()}-{patients_df['age'].max()} years",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        f"Date: {start_date} to {end_date}, Type: {patient_type}" if any([start_date, end_date, patient_type]) else 'None'
                    ]
                }
                
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Statistics', index=False)
                
                # Insurance breakdown
                if patients_df['insurance_carrier'].notna().any():
                    insurance_breakdown = patients_df['insurance_carrier'].value_counts().reset_index()
                    insurance_breakdown.columns = ['Insurance_Carrier', 'Patient_Count']
                    insurance_breakdown['Percentage'] = (insurance_breakdown['Patient_Count'] / len(patients_df) * 100).round(1)
                    insurance_breakdown.to_excel(writer, sheet_name='Insurance_Breakdown', index=False)
                
                # Age demographics
                age_bins = [0, 18, 30, 50, 70, 100]
                age_labels = ['<18', '18-30', '31-50', '51-70', '70+']
                patients_df['age_group'] = pd.cut(patients_df['age'], bins=age_bins, labels=age_labels, right=False)
                
                age_demographics = patients_df['age_group'].value_counts().reset_index()
                age_demographics.columns = ['Age_Group', 'Count']
                age_demographics['Percentage'] = (age_demographics['Count'] / len(patients_df) * 100).round(1)
                age_demographics.to_excel(writer, sheet_name='Age_Demographics', index=False)
            
            conn.close()
            
            logger.info(f"✅ Patient list export created: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Patient list export failed: {e}")
            return None
    
    def export_analytics_summary(self, start_date: datetime, end_date: datetime) -> str:
        """Export comprehensive analytics summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get appointment statistics
            appointments_query = """
            SELECT 
                a.id,
                a.appointment_datetime,
                a.doctor,
                a.location,
                a.duration,
                a.status,
                p.patient_type,
                p.insurance_carrier,
                DATE(a.appointment_datetime) as appointment_date
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            WHERE DATE(a.appointment_datetime) BETWEEN ? AND ?
            """
            
            appointments_df = pd.read_sql_query(appointments_query, conn, 
                                              params=[start_date.strftime('%Y-%m-%d'), 
                                                     end_date.strftime('%Y-%m-%d')])
            
            # Get reminder statistics
            reminders_query = """
            SELECT 
                r.reminder_type,
                r.sent,
                r.email_sent,
                r.sms_sent,
                r.response_received,
                DATE(r.scheduled_time) as reminder_date
            FROM reminders r
            JOIN appointments a ON r.appointment_id = a.id
            WHERE DATE(a.appointment_datetime) BETWEEN ? AND ?
            """
            
            reminders_df = pd.read_sql_query(reminders_query, conn,
                                           params=[start_date.strftime('%Y-%m-%d'),
                                                  end_date.strftime('%Y-%m-%d')])
            
            # Get patient statistics
            patients_query = """
            SELECT 
                patient_type,
                insurance_carrier,
                DATE(created_at) as registration_date
            FROM patients
            WHERE DATE(created_at) BETWEEN ? AND ?
            """
            
            patients_df = pd.read_sql_query(patients_query, conn,
                                          params=[start_date.strftime('%Y-%m-%d'),
                                                 end_date.strftime('%Y-%m-%d')])
            
            conn.close()
            
            # Create analytics export
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"analytics_summary_{timestamp}.xlsx"
            filepath = self.exports_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Executive Summary
                total_appointments = len(appointments_df)
                total_patients = len(patients_df)
                total_reminders = len(reminders_df)
                
                exec_summary = {
                    'Metric': [
                        'Report Period',
                        'Total Appointments',
                        'New Patient Appointments',
                        'Returning Patient Appointments',
                        'Appointment Completion Rate',
                        'New Patients Registered',
                        'Total Reminders Sent',
                        'Reminder Response Rate',
                        'Most Active Doctor',
                        'Most Popular Location',
                        'Average Appointment Duration',
                        'Generated On'
                    ],
                    'Value': [
                        f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                        total_appointments,
                        len(appointments_df[appointments_df['patient_type'] == 'new']),
                        len(appointments_df[appointments_df['patient_type'] == 'returning']),
                        f"{len(appointments_df[appointments_df['status'] == 'completed']) / total_appointments * 100:.1f}%" if total_appointments > 0 else "0%",
                        total_patients,
                        len(reminders_df[reminders_df['sent'] == True]) if not reminders_df.empty else 0,
                        f"{len(reminders_df[reminders_df['response_received'] == True]) / len(reminders_df[reminders_df['sent'] == True]) * 100:.1f}%" if not reminders_df.empty and len(reminders_df[reminders_df['sent'] == True]) > 0 else "0%",
                        appointments_df['doctor'].mode().iloc[0] if not appointments_df.empty and not appointments_df['doctor'].mode().empty else 'N/A',
                        appointments_df['location'].mode().iloc[0] if not appointments_df.empty and not appointments_df['location'].mode().empty else 'N/A',
                        f"{appointments_df['duration'].mean():.1f} minutes" if not appointments_df.empty else "N/A",
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ]
                }
                
                exec_df = pd.DataFrame(exec_summary)
                exec_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
                
                # Daily appointment trends
                if not appointments_df.empty:
                    daily_trends = appointments_df.groupby('appointment_date').agg({
                        'id': 'count',
                        'duration': 'sum',
                        'patient_type': lambda x: (x == 'new').sum()
                    }).reset_index()
                    daily_trends.columns = ['Date', 'Total_Appointments', 'Total_Minutes', 'New_Patients']
                    daily_trends['Returning_Patients'] = daily_trends['Total_Appointments'] - daily_trends['New_Patients']
                    daily_trends.to_excel(writer, sheet_name='Daily_Trends', index=False)
                
                # Doctor performance
                if not appointments_df.empty:
                    doctor_performance = appointments_df.groupby('doctor').agg({
                        'id': 'count',
                        'duration': ['sum', 'mean'],
                        'patient_type': lambda x: (x == 'new').sum()
                    }).reset_index()
                    doctor_performance.columns = ['Doctor', 'Total_Appointments', 'Total_Minutes', 'Avg_Duration', 'New_Patients']
                    doctor_performance['Returning_Patients'] = doctor_performance['Total_Appointments'] - doctor_performance['New_Patients']
                    doctor_performance['Revenue_Estimate'] = doctor_performance['Total_Minutes'] * 3  # $3 per minute estimate
                    doctor_performance.to_excel(writer, sheet_name='Doctor_Performance', index=False)
                
                # Location utilization
                if not appointments_df.empty:
                    location_util = appointments_df.groupby('location').agg({
                        'id': 'count',
                        'duration': 'sum'
                    }).reset_index()
                    location_util.columns = ['Location', 'Total_Appointments', 'Total_Minutes']
                    location_util['Utilization_Percentage'] = (location_util['Total_Minutes'] / location_util['Total_Minutes'].sum() * 100).round(1)
                    location_util.to_excel(writer, sheet_name='Location_Utilization', index=False)
                
                # Reminder effectiveness
                if not reminders_df.empty:
                    reminder_effectiveness = reminders_df.groupby('reminder_type').agg({
                        'sent': 'sum',
                        'email_sent': 'sum',
                        'sms_sent': 'sum',
                        'response_received': 'sum'
                    }).reset_index()
                    reminder_effectiveness['Response_Rate'] = (reminder_effectiveness['response_received'] / reminder_effectiveness['sent'] * 100).round(1)
                    reminder_effectiveness.to_excel(writer, sheet_name='Reminder_Effectiveness', index=False)
                
                # Raw data sheets
                if not appointments_df.empty:
                    appointments_df.to_excel(writer, sheet_name='Raw_Appointments', index=False)
                
                if not reminders_df.empty:
                    reminders_df.to_excel(writer, sheet_name='Raw_Reminders', index=False)
                
                if not patients_df.empty:
                    patients_df.to_excel(writer, sheet_name='Raw_Patients', index=False)
            
            logger.info(f"✅ Analytics summary export created: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Analytics export failed: {e}")
            return None
    
    def export_reminder_report(self, start_date: datetime, end_date: datetime) -> str:
        """Export detailed reminder system report"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get detailed reminder data
            query = """
            SELECT 
                r.id as reminder_id,
                r.appointment_id,
                r.reminder_type,
                r.scheduled_time,
                r.sent,
                r.email_sent,
                r.sms_sent,
                r.response_received,
                r.attempts,
                r.last_attempt,
                a.appointment_datetime,
                a.doctor,
                a.location,
                p.first_name,
                p.last_name,
                p.email,
                p.phone,
                p.patient_type
            FROM reminders r
            JOIN appointments a ON r.appointment_id = a.id
            JOIN patients p ON a.patient_id = p.id
            WHERE DATE(r.scheduled_time) BETWEEN ? AND ?
            ORDER BY r.scheduled_time
            """
            
            reminders_df = pd.read_sql_query(query, conn,
                                           params=[start_date.strftime('%Y-%m-%d'),
                                                  end_date.strftime('%Y-%m-%d')])
            
            # Get response data
            responses_query = """
            SELECT 
                rr.appointment_id,
                rr.response_type,
                rr.response_channel,
                rr.response_content,
                rr.received_at,
                a.appointment_datetime,
                p.first_name,
                p.last_name
            FROM reminder_responses rr
            JOIN appointments a ON rr.appointment_id = a.id
            JOIN patients p ON a.patient_id = p.id
            WHERE DATE(rr.received_at) BETWEEN ? AND ?
            ORDER BY rr.received_at
            """
            
            responses_df = pd.read_sql_query(responses_query, conn,
                                           params=[start_date.strftime('%Y-%m-%d'),
                                                  end_date.strftime('%Y-%m-%d')])
            
            conn.close()
            
            # Create reminder report
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"reminder_report_{timestamp}.xlsx"
            filepath = self.exports_dir / filename
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Summary sheet
                if not reminders_df.empty:
                    summary_stats = {
                        'Metric': [
                            'Report Period',
                            'Total Reminders Scheduled',
                            'Reminders Successfully Sent',
                            'Email Reminders Sent',
                            'SMS Reminders Sent',
                            'Total Patient Responses',
                            'Overall Response Rate',
                            'Initial Reminder Response Rate',
                            'Form Check Response Rate',
                            'Final Confirmation Response Rate',
                            'Average Attempts per Reminder'
                        ],
                        'Value': [
                            f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                            len(reminders_df),
                            len(reminders_df[reminders_df['sent'] == True]),
                            len(reminders_df[reminders_df['email_sent'] == True]),
                            len(reminders_df[reminders_df['sms_sent'] == True]),
                            len(responses_df),
                            f"{len(reminders_df[reminders_df['response_received'] == True]) / len(reminders_df[reminders_df['sent'] == True]) * 100:.1f}%" if len(reminders_df[reminders_df['sent'] == True]) > 0 else "0%",
                            f"{len(reminders_df[(reminders_df['reminder_type'] == 'initial') & (reminders_df['response_received'] == True)]) / len(reminders_df[(reminders_df['reminder_type'] == 'initial') & (reminders_df['sent'] == True)]) * 100:.1f}%" if len(reminders_df[(reminders_df['reminder_type'] == 'initial') & (reminders_df['sent'] == True)]) > 0 else "0%",
                            f"{len(reminders_df[(reminders_df['reminder_type'] == 'form_check') & (reminders_df['response_received'] == True)]) / len(reminders_df[(reminders_df['reminder_type'] == 'form_check') & (reminders_df['sent'] == True)]) * 100:.1f}%" if len(reminders_df[(reminders_df['reminder_type'] == 'form_check') & (reminders_df['sent'] == True)]) > 0 else "0%",
                            f"{len(reminders_df[(reminders_df['reminder_type'] == 'final_confirmation') & (reminders_df['response_received'] == True)]) / len(reminders_df[(reminders_df['reminder_type'] == 'final_confirmation') & (reminders_df['sent'] == True)]) * 100:.1f}%" if len(reminders_df[(reminders_df['reminder_type'] == 'final_confirmation') & (reminders_df['sent'] == True)]) > 0 else "0%",
                            f"{reminders_df['attempts'].mean():.1f}"
                        ]
                    }
                    
                    summary_df = pd.DataFrame(summary_stats)
                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed reminder data
                if not reminders_df.empty:
                    reminders_export = reminders_df.copy()
                    reminders_export['patient_name'] = reminders_export['first_name'] + ' ' + reminders_export['last_name']
                    reminders_export.to_excel(writer, sheet_name='Reminder_Details', index=False)
                
                # Patient responses
                if not responses_df.empty:
                    responses_export = responses_df.copy()
                    responses_export['patient_name'] = responses_export['first_name'] + ' ' + responses_export['last_name']
                    responses_export.to_excel(writer, sheet_name='Patient_Responses', index=False)
                
                # Reminder type breakdown
                if not reminders_df.empty:
                    type_breakdown = reminders_df.groupby('reminder_type').agg({
                        'reminder_id': 'count',
                        'sent': 'sum',
                        'email_sent': 'sum',
                        'sms_sent': 'sum',
                        'response_received': 'sum',
                        'attempts': 'mean'
                    }).reset_index()
                    type_breakdown.columns = ['Reminder_Type', 'Total_Scheduled', 'Total_Sent', 'Email_Sent', 'SMS_Sent', 'Responses', 'Avg_Attempts']
                    type_breakdown['Response_Rate'] = (type_breakdown['Responses'] / type_breakdown['Total_Sent'] * 100).round(1)
                    type_breakdown.to_excel(writer, sheet_name='Type_Breakdown', index=False)
            
            logger.info(f"✅ Reminder report export created: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Reminder report export failed: {e}")
            return None
    
    def get_export_history(self) -> List[Dict]:
        """Get history of recent exports"""
        try:
            exports = []
            
            for file_path in self.exports_dir.glob("*.xlsx"):
                stat = file_path.stat()
                exports.append({
                    'filename': file_path.name,
                    'filepath': str(file_path),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'type': self._determine_export_type(file_path.name)
                })
            
            # Sort by creation time, newest first
            exports.sort(key=lambda x: x['created_at'], reverse=True)
            
            return exports[:20]  # Return last 20 exports
            
        except Exception as e:
            logger.error(f"❌ Error getting export history: {e}")
            return []
    
    def _determine_export_type(self, filename: str) -> str:
        """Determine export type from filename"""
        if filename.startswith('appointment_'):
            return 'Single Appointment'
        elif filename.startswith('patient_list_'):
            return 'Patient List'
        elif filename.startswith('analytics_summary_'):
            return 'Analytics Summary'
        elif filename.startswith('reminder_report_'):
            return 'Reminder Report'
        else:
            return 'Unknown'
    
    def cleanup_old_exports(self, days_to_keep: int = 30):
        """Clean up old export files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            deleted_count = 0
            
            for file_path in self.exports_dir.glob("*.xlsx"):
                if datetime.fromtimestamp(file_path.stat().st_ctime) < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
            
            logger.info(f"🧹 Cleaned up {deleted_count} old export files")
            
        except Exception as e:
            logger.error(f"❌ Error cleaning up exports: {e}")