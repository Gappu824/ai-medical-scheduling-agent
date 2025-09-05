"""
Database Migrations for Complete Reminder System
RagaAI Assignment - Additional Tables for Reminder Tracking and Response Handling
"""

import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def run_reminder_system_migrations(db_path: str = "medical_scheduling.db"):
    """Run all migrations needed for the complete reminder system"""
    
    migrations = [
        create_reminder_actions_table,
        create_reminder_responses_table, 
        add_reminder_tracking_fields,
        create_indexes_for_performance,
        populate_sample_reminder_data
    ]
    
    conn = sqlite3.connect(db_path)
    
    for migration in migrations:
        try:
            migration_name = migration.__name__
            logger.info(f"Running migration: {migration_name}")
            migration(conn)
            logger.info(f"✅ Migration completed: {migration_name}")
        except Exception as e:
            logger.error(f"❌ Migration failed: {migration_name} - {e}")
            conn.rollback()
            raise e
    
    conn.commit()
    conn.close()
    logger.info("✅ All reminder system migrations completed successfully")

def create_reminder_actions_table(conn: sqlite3.Connection):
    """Create table to track reminder actions (URLs, response tracking)"""
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminder_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id TEXT NOT NULL,
        reminder_type TEXT NOT NULL,
        action_data TEXT, -- JSON data with URLs and tracking info
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (appointment_id) REFERENCES appointments (id)
    )
    """)

def create_reminder_responses_table(conn: sqlite3.Connection):
    """Create table to track patient responses to reminders"""
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reminder_responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        appointment_id TEXT NOT NULL,
        response_type TEXT NOT NULL, -- form_completed, visit_confirmed, visit_cancelled, etc.
        response_data TEXT, -- JSON data with response details
        response_channel TEXT DEFAULT 'unknown', -- email, sms, web
        received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (appointment_id) REFERENCES appointments (id)
    )
    """)

def add_reminder_tracking_fields(conn: sqlite3.Connection):
    """Add additional tracking fields to existing reminders table"""
    
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(reminders)")
    existing_columns = [column[1] for column in cursor.fetchall()]
    
    # Add sent_at timestamp if not exists
    if 'sent_at' not in existing_columns:
        cursor.execute("""
        ALTER TABLE reminders 
        ADD COLUMN sent_at TIMESTAMP
        """)
    
    # Add delivery_status if not exists
    if 'delivery_status' not in existing_columns:
        cursor.execute("""
        ALTER TABLE reminders 
        ADD COLUMN delivery_status TEXT DEFAULT 'pending'
        """)
    
    # Add channel (email/sms) if not exists
    if 'channel' not in existing_columns:
        cursor.execute("""
        ALTER TABLE reminders 
        ADD COLUMN channel TEXT DEFAULT 'email'
        """)
    
    # Add priority if not exists
    if 'priority' not in existing_columns:
        cursor.execute("""
        ALTER TABLE reminders 
        ADD COLUMN priority TEXT DEFAULT 'normal'
        """)

def create_indexes_for_performance(conn: sqlite3.Connection):
    """Create indexes for better performance on reminder queries"""
    
    cursor = conn.cursor()
    
    # Index for finding due reminders
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reminders_due 
    ON reminders (scheduled_time, sent) 
    WHERE sent = FALSE
    """)
    
    # Index for appointment lookups
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reminders_appointment 
    ON reminders (appointment_id, reminder_type)
    """)
    
    # Index for response tracking
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_reminder_responses_appointment 
    ON reminder_responses (appointment_id, received_at)
    """)
    
    # Index for patient phone lookups (for SMS responses)
    cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_patients_phone 
    ON patients (phone)
    """)

def populate_sample_reminder_data(conn: sqlite3.Connection):
    """Populate some sample reminder data for testing"""
    
    cursor = conn.cursor()
    
    # Check if we already have sample data
    cursor.execute("SELECT COUNT(*) FROM reminders")
    existing_count = cursor.fetchone()[0]
    
    if existing_count > 0:
        logger.info("Sample reminder data already exists, skipping population")
        return
    
    # Get some sample appointments
    cursor.execute("""
    SELECT id, appointment_datetime, patient_id 
    FROM appointments 
    WHERE appointment_datetime > datetime('now') 
    LIMIT 5
    """)
    
    appointments = cursor.fetchall()
    
    if not appointments:
        logger.info("No future appointments found for sample reminder data")
        return
    
    # Create sample reminders for each appointment
    for apt_id, apt_datetime, patient_id in appointments:
        apt_dt = datetime.fromisoformat(apt_datetime)
        
        # Schedule all three types of reminders
        reminders = [
            {
                "appointment_id": apt_id,
                "reminder_type": "initial",
                "scheduled_time": (apt_dt - timedelta(days=7)).isoformat(),
                "channel": "email"
            },
            {
                "appointment_id": apt_id, 
                "reminder_type": "form_check",
                "scheduled_time": (apt_dt - timedelta(days=1)).isoformat(),
                "channel": "both"
            },
            {
                "appointment_id": apt_id,
                "reminder_type": "final", 
                "scheduled_time": (apt_dt - timedelta(hours=2)).isoformat(),
                "channel": "sms",
                "priority": "high"
            }
        ]
        
        for reminder in reminders:
            cursor.execute("""
            INSERT INTO reminders (
                appointment_id, reminder_type, scheduled_time, 
                sent, channel, priority, created_at
            ) VALUES (?, ?, ?, FALSE, ?, ?, ?)
            """, (
                reminder["appointment_id"],
                reminder["reminder_type"], 
                reminder["scheduled_time"],
                reminder.get("channel", "email"),
                reminder.get("priority", "normal"),
                datetime.now().isoformat()
            ))
    
    logger.info(f"Created sample reminder data for {len(appointments)} appointments")

def create_reminder_statistics_view(conn: sqlite3.Connection):
    """Create a view for reminder statistics"""
    
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS reminder_stats AS
    SELECT 
        r.reminder_type,
        COUNT(*) as total_reminders,
        SUM(CASE WHEN r.sent = TRUE THEN 1 ELSE 0 END) as sent_count,
        SUM(CASE WHEN r.sent = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as send_rate,
        COUNT(resp.id) as response_count,
        COUNT(resp.id) * 100.0 / SUM(CASE WHEN r.sent = TRUE THEN 1 ELSE 0 END) as response_rate,
        r.channel,
        DATE(r.created_at) as date_created
    FROM reminders r
    LEFT JOIN reminder_responses resp ON r.appointment_id = resp.appointment_id
    WHERE r.created_at > date('now', '-30 days')
    GROUP BY r.reminder_type, r.channel, DATE(r.created_at)
    ORDER BY r.created_at DESC
    """)

def cleanup_old_reminder_data(conn: sqlite3.Connection, days_to_keep: int = 90):
    """Clean up old reminder data"""
    
    cursor = conn.cursor()
    
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # Delete old reminder responses
    cursor.execute("""
    DELETE FROM reminder_responses 
    WHERE received_at < ? AND processed = TRUE
    """, (cutoff_date.isoformat(),))
    
    responses_deleted = cursor.rowcount
    
    # Delete old reminder actions
    cursor.execute("""
    DELETE FROM reminder_actions 
    WHERE created_at < ?
    """, (cutoff_date.isoformat(),))
    
    actions_deleted = cursor.rowcount
    
    logger.info(f"Cleaned up {responses_deleted} old reminder responses and {actions_deleted} old reminder actions")

# Utility functions for reminder system
def get_reminder_system_status(db_path: str = "medical_scheduling.db") -> dict:
    """Get current status of the reminder system"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get counts of different reminder statuses
        cursor.execute("""
        SELECT 
            reminder_type,
            COUNT(*) as total,
            SUM(CASE WHEN sent = TRUE THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN scheduled_time <= datetime('now') AND sent = FALSE THEN 1 ELSE 0 END) as due
        FROM reminders 
        WHERE created_at > date('now', '-7 days')
        GROUP BY reminder_type
        """)
        
        reminder_stats = cursor.fetchall()
        
        # Get response stats
        cursor.execute("""
        SELECT response_type, COUNT(*) as count
        FROM reminder_responses 
        WHERE received_at > date('now', '-7 days')
        GROUP BY response_type
        """)
        
        response_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "reminder_stats": [
                {
                    "type": row[0],
                    "total": row[1],
                    "sent": row[2], 
                    "due": row[3]
                }
                for row in reminder_stats
            ],
            "response_stats": [
                {"type": row[0], "count": row[1]}
                for row in response_stats
            ],
            "status": "active",
            "last_checked": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting reminder system status: {e}")
        return {"status": "error", "error": str(e)}

# Import timedelta for migrations
from datetime import timedelta

if __name__ == "__main__":
    # Run migrations if called directly
    logging.basicConfig(level=logging.INFO)
    run_reminder_system_migrations()