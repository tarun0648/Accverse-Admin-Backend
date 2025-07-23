from utils import get_db_connection, format_tax_form_response
from mysql.connector import Error
import json
import os
from decimal import Decimal
from datetime import timedelta, datetime, timezone
import smtplib
from email.mime.text import MIMEText
from config import Config

def get_user_tax_forms(user_id):
    """Get all tax forms for a specific user"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        # Get tax forms
        query = """
            SELECT * FROM tax_forms 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id,))
        tax_forms = cursor.fetchall()
        
        # Get associated files for each tax form
        for tax_form in tax_forms:
            files_query = """
                SELECT * FROM tax_form_files 
                WHERE tax_form_id = %s
            """
            cursor.execute(files_query, (tax_form['id'],))
            files = cursor.fetchall()
            tax_form['files'] = files
            
        cursor.close()
        conn.close()
        
        return [format_tax_form_response(form) for form in tax_forms]
        
    except Error as e:
        print(f"Error fetching tax forms: {e}")
        return None

def get_tax_form_by_id(form_id):
    """Get a specific tax form by ID"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        # Get tax form
        query = """
            SELECT * FROM tax_forms 
            WHERE id = %s
        """
        cursor.execute(query, (form_id,))
        tax_form = cursor.fetchone()
        
        if tax_form:
            # Get associated files
            files_query = """
                SELECT * FROM tax_form_files 
                WHERE tax_form_id = %s
            """
            cursor.execute(files_query, (form_id,))
            files = cursor.fetchall()
            tax_form['files'] = files
            
        cursor.close()
        conn.close()
        
        return format_tax_form_response(tax_form) if tax_form else None
        
    except Error as e:
        print(f"Error fetching tax form: {e}")
        return None

def get_tax_forms_by_type(user_id, form_type):
    """Get tax forms of a specific type for a user"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        # Get tax forms
        query = """
            SELECT * FROM tax_forms 
            WHERE user_id = %s AND form_type = %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (user_id, form_type))
        tax_forms = cursor.fetchall()
        
        # Get associated files for each tax form
        for tax_form in tax_forms:
            files_query = """
                SELECT * FROM tax_form_files 
                WHERE tax_form_id = %s
            """
            cursor.execute(files_query, (tax_form['id'],))
            files = cursor.fetchall()
            tax_form['files'] = files
            
        cursor.close()
        conn.close()
        
        return [format_tax_form_response(form) for form in tax_forms]
        
    except Error as e:
        print(f"Error fetching tax forms: {e}")
        return None

def get_all_users():
    """Get all users from the database"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT id, name, email, phone, address, role, is_verified, created_at, updated_at 
            FROM users 
            ORDER BY created_at DESC
        """
        cursor.execute(query)
        users = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return users
        
    except Error as e:
        print(f"Error fetching users: {e}")
        return None

def get_all_clients():
    """Get all users with the 'client' role"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE role = 'client' ORDER BY created_at DESC"
        cursor.execute(query)
        clients = cursor.fetchall()
        cursor.close()
        conn.close()
        return clients
    except Error as e:
        print(f"Error fetching clients: {e}")
        return None

def get_all_appointments():
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM appointments ORDER BY appointment_date DESC, appointment_time DESC"
        cursor.execute(query)
        appointments = cursor.fetchall()
        cursor.close()
        conn.close()
        # Convert timedelta fields to string
        for apt in appointments:
            for k, v in apt.items():
                if isinstance(v, timedelta):
                    # Convert to string in HH:MM:SS format
                    apt[k] = str(v)
        return appointments
    except Error as e:
        print(f"Error fetching appointments: {e}")
        return None

def get_files_for_form(form_id: str):
    print(f"Fetching files for form_id: {form_id}")
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    query = "SELECT files FROM tax_form_files WHERE tax_form_id = %s"
    print(f"Executing query: {query} with form_id={form_id}")
    cursor.execute(query, (form_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    
    all_files = []
    print(f"Found {len(rows)} rows")
    
    for row in rows:
        if row and row['files']:
            try:
                print(f"Processing row with files: {row['files'][:100]}...")  # Print first 100 chars for debugging
                files_list = json.loads(row['files'])
                if isinstance(files_list, list):
                    for file in files_list:
                        # Keep only necessary fields
                        file_info = {
                            'file_name': file.get('file_name'),
                            'file_type': file.get('file_type'),
                            'file_size': file.get('file_size'),
                            'field_name': file.get('field_name'),
                            'form_id': form_id
                        }
                        all_files.append(file_info)
            except Exception as e:
                print(f"Error parsing files JSON: {e}")
                print(f"Problematic row: {row}")
    
    print(f"Returning {len(all_files)} files")
    return all_files

def get_all_services():
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM services ORDER BY name"
        cursor.execute(query)
        services = cursor.fetchall()
        cursor.close()
        conn.close()
        # Convert Decimal and timedelta fields
        for s in services:
            for k, v in s.items():
                if isinstance(v, Decimal):
                    s[k] = float(v)
                elif isinstance(v, timedelta):
                    s[k] = int(v.total_seconds() // 60)  # minutes
        return services
    except Error as e:
        print(f"Error fetching services: {e}")
        return None 

def get_form_payments(user_id):
    """Get all form payments for a specific user"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT fp.*, tf.form_type as form_type_name
            FROM form_payments fp
            LEFT JOIN tax_forms tf ON fp.form_id = tf.id
            WHERE fp.user_id = %s
            ORDER BY fp.created_at DESC
        """
        cursor.execute(query, (user_id,))
        payments = cursor.fetchall()
        
        # Convert Decimal to float and format dates for JSON serialization
        for payment in payments:
            if isinstance(payment['amount'], Decimal):
                payment['amount'] = float(payment['amount'])
            # Format date fields
            if payment.get('payment_date'):
                payment['payment_date'] = payment['payment_date'].isoformat()
            if payment.get('created_at'):
                payment['created_at'] = payment['created_at'].isoformat()
            if payment.get('updated_at'):
                payment['updated_at'] = payment['updated_at'].isoformat()
        
        cursor.close()
        conn.close()
        
        return payments
        
    except Error as e:
        print(f"Error fetching form payments: {e}")
        return None 

def get_all_form_payments():
    """Get all form payments for all users"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT fp.*, tf.form_type as form_type_name
            FROM form_payments fp
            LEFT JOIN tax_forms tf ON fp.form_id = tf.id
            ORDER BY fp.created_at DESC
        """
        cursor.execute(query)
        payments = cursor.fetchall()
        for payment in payments:
            if isinstance(payment['amount'], Decimal):
                payment['amount'] = float(payment['amount'])
            if payment.get('payment_date'):
                payment['payment_date'] = payment['payment_date'].isoformat()
            if payment.get('created_at'):
                payment['created_at'] = payment['created_at'].isoformat()
            if payment.get('updated_at'):
                payment['updated_at'] = payment['updated_at'].isoformat()
        cursor.close()
        conn.close()
        return payments
    except Error as e:
        print(f"Error fetching all form payments: {e}")
        return None

def get_all_tax_forms_by_type(form_type):
    """Get all tax forms of a specific type for all users"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT * FROM tax_forms 
            WHERE form_type = %s
            ORDER BY created_at DESC
        """
        cursor.execute(query, (form_type,))
        tax_forms = cursor.fetchall()
        # Get associated files for each tax form
        for tax_form in tax_forms:
            files_query = """
                SELECT * FROM tax_form_files 
                WHERE tax_form_id = %s
            """
            cursor.execute(files_query, (tax_form['id'],))
            files = cursor.fetchall()
            tax_form['files'] = files
        cursor.close()
        conn.close()
        return [format_tax_form_response(form) for form in tax_forms]
    except Error as e:
        print(f"Error fetching all tax forms by type: {e}")
        return None

def get_form_pricing_configs():
    """Get all form pricing configurations"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT * FROM form_pricing_configs 
            ORDER BY form_type
        """
        cursor.execute(query)
        configs = cursor.fetchall()
        
        # Convert JSON strings to Python objects and Decimal to float
        for config in configs:
            if config.get('pricing_options'):
                config['pricing_options'] = json.loads(config['pricing_options'])
                # Convert Decimal to float in pricing options
                for option in config['pricing_options']:
                    if isinstance(option.get('price'), Decimal):
                        option['price'] = float(option['price'])
            
            if config.get('add_ons'):
                config['add_ons'] = json.loads(config['add_ons'])
                # Convert Decimal to float in add-ons
                for addon in config['add_ons']:
                    if isinstance(addon.get('price'), Decimal):
                        addon['price'] = float(addon['price'])
            
            # Convert Decimal to float in main config
            if isinstance(config.get('gst_rate'), Decimal):
                config['gst_rate'] = float(config['gst_rate'])
        
        cursor.close()
        conn.close()
        
        return configs
        
    except Error as e:
        print(f"Error fetching form pricing configs: {e}")
        return None

def update_form_pricing_config(config_id, data):
    """Update a form pricing configuration"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        # Convert Python objects to JSON strings
        if 'pricing_options' in data:
            data['pricing_options'] = json.dumps(data['pricing_options'])
        if 'add_ons' in data:
            data['add_ons'] = json.dumps(data['add_ons'])
        
        # Build the update query dynamically based on provided fields
        update_fields = []
        values = []
        excluded_fields = ['id', 'created_at', 'updated_at']  # Fields to exclude from update
        
        for key, value in data.items():
            if key not in excluded_fields:  # Don't update excluded fields
                update_fields.append(f"{key} = %s")
                values.append(value)
        
        if not update_fields:
            return None
            
        query = f"""
            UPDATE form_pricing_configs 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """
        values.append(config_id)
        
        cursor.execute(query, tuple(values))
        conn.commit()
        
        # Get the updated record
        select_query = "SELECT * FROM form_pricing_configs WHERE id = %s"
        cursor.execute(select_query, (config_id,))
        updated_config = cursor.fetchone()
        
        # Convert JSON strings back to Python objects and Decimal to float
        if updated_config.get('pricing_options'):
            updated_config['pricing_options'] = json.loads(updated_config['pricing_options'])
            # Convert Decimal to float in pricing options
            for option in updated_config['pricing_options']:
                if isinstance(option.get('price'), Decimal):
                    option['price'] = float(option['price'])
        
        if updated_config.get('add_ons'):
            updated_config['add_ons'] = json.loads(updated_config['add_ons'])
            # Convert Decimal to float in add-ons
            for addon in updated_config['add_ons']:
                if isinstance(addon.get('price'), Decimal):
                    addon['price'] = float(addon['price'])
        
        # Convert Decimal to float in main config
        if isinstance(updated_config.get('gst_rate'), Decimal):
            updated_config['gst_rate'] = float(updated_config['gst_rate'])
        
        cursor.close()
        conn.close()
        
        return updated_config
        
    except Error as e:
        print(f"Error updating form pricing config: {e}")
        return None 

def get_notifications(user_id=None, limit=50, offset=0, include_archived=False):
    """Get notifications for a user or all notifications if user_id is None"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT n.*, u.name as user_name 
            FROM notifications n
            LEFT JOIN users u ON n.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if user_id is not None:
            query += " AND n.user_id = %s"
            params.append(user_id)
            
        if not include_archived:
            query += " AND n.is_archived = FALSE"
            
        query += " ORDER BY n.created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        notifications = cursor.fetchall()
        
        # Convert JSON strings to Python objects
        for notification in notifications:
            if notification.get('metadata'):
                notification['metadata'] = json.loads(notification['metadata'])
        
        cursor.close()
        conn.close()
        
        return notifications
        
    except Error as e:
        print(f"Error fetching notifications: {e}")
        return None

def mark_notification_read(notification_id):
    """Mark a notification as read"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE id = %s
        """
        cursor.execute(query, (notification_id,))
        conn.commit()
        
        # Get the updated notification
        select_query = "SELECT * FROM notifications WHERE id = %s"
        cursor.execute(select_query, (notification_id,))
        notification = cursor.fetchone()
        
        if notification and notification.get('metadata'):
            notification['metadata'] = json.loads(notification['metadata'])
        
        cursor.close()
        conn.close()
        
        return notification
        
    except Error as e:
        print(f"Error marking notification as read: {e}")
        return None

def archive_notification(notification_id):
    """Archive a notification"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            UPDATE notifications 
            SET is_archived = TRUE 
            WHERE id = %s
        """
        cursor.execute(query, (notification_id,))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"Error archiving notification: {e}")
        return None

def unarchive_notification(notification_id):
    """Unarchive a notification"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor(dictionary=True)
        
        query = """
            UPDATE notifications 
            SET is_archived = FALSE 
            WHERE id = %s
        """
        cursor.execute(query, (notification_id,))
        conn.commit()
        
        # Get the updated notification
        select_query = "SELECT * FROM notifications WHERE id = %s"
        cursor.execute(select_query, (notification_id,))
        notification = cursor.fetchone()
        
        if notification and notification.get('metadata'):
            notification['metadata'] = json.loads(notification['metadata'])
        
        cursor.close()
        conn.close()
        
        return notification
        
    except Error as e:
        print(f"Error unarchiving notification: {e}")
        return None 

def mark_all_notifications_read(user_id=None):
    """Mark all unread notifications for a user as read, or all if user_id is None"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        
        query = """
            UPDATE notifications 
            SET is_read = TRUE 
            WHERE is_read = FALSE
        """
        params = []

        if user_id is not None:
            query += " AND user_id = %s"
            params.append(user_id)

        cursor.execute(query, tuple(params))
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except Error as e:
        print(f"Error marking all notifications as read: {e}")
        return None 

def get_user_by_email(email):
    """Get a user by email (including password hash and role)"""
    try:
        conn = get_db_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT id, name, email, password, role, is_verified
            FROM users
            WHERE email = %s
            LIMIT 1
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error fetching user by email: {e}")
        return None 

def set_reset_token(user_id, token, expiry):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE id=%s",
        (token, expiry, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_reset_token(token):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM users WHERE reset_token=%s",
        (token,)
    )
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def clear_reset_token(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET reset_token=NULL, reset_token_expiry=NULL WHERE id=%s",
        (user_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()

def update_user_password(user_id, hashed_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password=%s WHERE id=%s",
        (hashed_password, user_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

def send_reset_email(email, token):
    reset_link = f"http://localhost:8080/reset-password?token={token}"
    subject = "Password Reset Request"
    body = f"""
    Hello,

    We received a request to reset your password. Click the link below to set a new password:

    {reset_link}

    If you did not request this, you can safely ignore this email.

    Thanks,
    Your Company Team
    """
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = Config.EMAIL_USER
    msg['To'] = email

    try:
        with smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT) as server:
            server.starttls()
            server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
            server.sendmail(Config.EMAIL_USER, [email], msg.as_string())
        print(f"Reset email sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}") 

def get_dashboard_main_widgets_data():
    """Fetches data for the main dashboard widgets: stats, revenue trend, and upcoming appointments."""
    conn = get_db_connection()
    if not conn:
        return None
    
    cursor = conn.cursor(dictionary=True)
    
    try:
        # 1. Dashboard Stats
        
        # Total clients (users with role 'client')
        cursor.execute("SELECT COUNT(*) as total FROM users WHERE role = 'client';")
        total_users = cursor.fetchone()['total']

        # Monthly Revenue & Pending Payments (Current and Previous Month)
        query = """
            SELECT
                SUM(CASE WHEN payment_status = 'completed' AND MONTH(payment_date) = MONTH(CURDATE()) AND YEAR(payment_date) = YEAR(CURDATE()) THEN amount ELSE 0 END) as current_month_revenue,
                SUM(CASE WHEN payment_status = 'completed' AND MONTH(payment_date) = MONTH(CURDATE() - INTERVAL 1 MONTH) AND YEAR(payment_date) = YEAR(CURDATE() - INTERVAL 1 MONTH) THEN amount ELSE 0 END) as prev_month_revenue,
                SUM(CASE WHEN payment_status = 'pending' THEN amount ELSE 0 END) as total_pending
            FROM form_payments;
        """
        cursor.execute(query)
        payment_stats = cursor.fetchone()

        # New clients (Current and Previous Month)
        query = """
            SELECT
                COUNT(CASE WHEN MONTH(created_at) = MONTH(CURDATE()) AND YEAR(created_at) = YEAR(CURDATE()) THEN id END) as current_month_clients,
                COUNT(CASE WHEN MONTH(created_at) = MONTH(CURDATE() - INTERVAL 1 MONTH) AND YEAR(created_at) = YEAR(CURDATE() - INTERVAL 1 MONTH) THEN id END) as prev_month_clients
            FROM users
            WHERE role = 'client';
        """
        cursor.execute(query)
        client_stats = cursor.fetchone()

        def get_change(current, previous):
            if previous is None or previous == 0:
                return 100 if current > 0 else 0
            return round(((current - previous) / previous) * 100)

        stats = {
            "totalClients": total_users,
            "monthlyRevenue": float(payment_stats.get('current_month_revenue') or 0.0),
            "pendingPayments": float(payment_stats.get('total_pending') or 0.0),
            "changes": {
                "clients": get_change(client_stats.get('current_month_clients'), client_stats.get('prev_month_clients')),
                "revenue": get_change(payment_stats.get('current_month_revenue'), payment_stats.get('prev_month_revenue')),
                "payments": 0 # This change metric is no longer relevant for total pending
            }
        }
        
        # 2. Revenue Trend (last 14 days)
        # Using DATE() is common for MySQL to group by the date part of a datetime column.
        revenue_query = """
            SELECT
                DATE(payment_date) as date,
                SUM(amount) as revenue
            FROM form_payments
            WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 14 DAY)
            GROUP BY DATE(payment_date)
            ORDER BY date ASC;
        """
        cursor.execute(revenue_query)
        revenue_data = cursor.fetchall()

        # Create a complete 14-day date range to ensure the chart is continuous
        revenue_map = {item['date']: item['revenue'] for item in revenue_data}
        revenue_trend = []
        today = datetime.now(timezone.utc).date()
        for i in range(15):
            day = today - timedelta(days=i)
            revenue_trend.append({
                "date": day.strftime('%Y-%m-%d'),
                "revenue": float(revenue_map.get(day, 0.0))
            })
        revenue_trend.reverse() # Order from oldest to newest

        # 3. Upcoming Appointments (next 5)
        # Combine appointment_date and appointment_time to create a full datetime for comparison
        appointments_query = """
            SELECT
                a.id,
                TIMESTAMP(a.appointment_date, a.appointment_time) as start_time,
                u.name as user_name,
                s.name as service_name
            FROM appointments a
            JOIN users u ON a.user_id = u.id
            JOIN services s ON a.service_id = s.id
            WHERE TIMESTAMP(a.appointment_date, a.appointment_time) > NOW()
            ORDER BY start_time ASC
            LIMIT 5;
        """
        cursor.execute(appointments_query)
        upcoming_appointments = cursor.fetchall()
        
        return {
            "stats": stats,
            "revenue_trend": revenue_trend,
            "upcoming_appointments": upcoming_appointments
        }
    except Exception as e:
        print(f"Error fetching dashboard data: {e}")
        return None
    finally:
        cursor.close()
        conn.close() 

def get_client_growth_data():
    """Fetches client growth data for the last 6 months."""
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    try:
        # Get client counts grouped by month for the last 6 months
        query = """
            SELECT
                DATE_FORMAT(created_at, '%Y-%m') as month,
                COUNT(id) as new_clients
            FROM users
            WHERE role = 'client' AND created_at >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
            GROUP BY month
            ORDER BY month ASC;
        """
        cursor.execute(query)
        client_growth = cursor.fetchall()
        
        # Format for the chart on the frontend
        # Example: { "month": "Jun", "clients": 202 }
        formatted_data = []
        for row in client_growth:
            # Convert '2023-06' to 'Jun'
            month_abbr = datetime.strptime(row['month'], '%Y-%m').strftime('%b')
            formatted_data.append({
                "month": month_abbr,
                "clients": row['new_clients']
            })
            
        return formatted_data
    except Exception as e:
        print(f"Error fetching client growth data: {e}")
        return None
    finally:
        cursor.close()
        conn.close() 