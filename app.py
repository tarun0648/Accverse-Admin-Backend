from flask import Flask, jsonify, request, send_from_directory, send_file
from flask_cors import CORS
from methods import get_user_tax_forms, get_tax_form_by_id, get_tax_forms_by_type, get_all_users, get_all_clients, get_files_for_form, get_all_appointments, get_all_services, get_form_payments, get_form_pricing_configs, update_form_pricing_config, get_notifications, mark_notification_read, archive_notification, unarchive_notification, mark_all_notifications_read, get_all_form_payments, get_all_tax_forms_by_type, get_user_by_email, set_reset_token, send_reset_email, get_user_by_reset_token, clear_reset_token, update_user_password, get_db_connection, get_dashboard_main_widgets_data, get_client_growth_data
from utils import jwt_required, admin_required, client_or_admin_required, generate_jwt_token, get_current_user
import os
import bcrypt
import secrets
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True,
        "expose_headers": ["Content-Type", "Authorization"],
        "max_age": 3600
    }
})

UPLOADS_DIR = os.environ.get('UPLOADS_DIR', '/opt/app/accverse-backend/uploads/tax_forms').rstrip('/\\')

print("UPLOADS_DIR:", UPLOADS_DIR)

# Public endpoints (no authentication required)
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required.'}), 400

        user = get_user_by_email(email)
        if not user:
            return jsonify({'error': 'Invalid email or password.'}), 401

        # Check if user is admin
        if user['role'] != 'admin':
            return jsonify({'error': 'Access denied. Admins only.'}), 403

        # Check if user is verified
        if not user['is_verified']:
            return jsonify({'error': 'Account not verified.'}), 403

        # Check password
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return jsonify({'error': 'Invalid email or password.'}), 401

        # Generate JWT token
        token = generate_jwt_token(user['id'], user['email'], user['role'])
        if not token:
            return jsonify({'error': 'Failed to generate authentication token'}), 500

        return jsonify({
            'success': True, 
            'token': token,
            'user': {
                'id': user['id'],
                'name': user['name'],
                'email': user['email'],
                'role': user['role']
            }
        })
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/request-password-reset', methods=['POST'])
def request_password_reset():
    try:
        data = request.json
        email = data.get('email')
        user = get_user_by_email(email)
        if not user:
            return jsonify({'error': 'No account found with that email.'}), 404
        if user['role'] != 'admin':
            return jsonify({'error': 'Only admin accounts can reset password.'}), 403
        # Generate token and expiry
        token = secrets.token_urlsafe(32)
        expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        set_reset_token(user['id'], token, expiry)
        send_reset_email(user['email'], token)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Password reset request error: {e}")
        return jsonify({'error': 'Password reset request failed'}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        user = get_user_by_reset_token(token)
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Invalid or expired token.'}), 400
        # Check expiry
        expiry = user['reset_token_expiry']
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry < datetime.now(timezone.utc):
            return jsonify({'error': 'Token expired.'}), 400
        # Update password
        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        update_user_password(user['id'], hashed)
        clear_reset_token(user['id'])
        return jsonify({'success': True})
    except Exception as e:
        print(f"Password reset error: {e}")
        return jsonify({'error': 'Password reset failed'}), 500

# Protected endpoints (authentication required)
@app.route('/api/tax-forms/user/<int:user_id>', methods=['GET'])
@client_or_admin_required
def get_user_forms(user_id):
    """Get all tax forms for a specific user"""
    try:
        current_user = get_current_user()
        # Users can only access their own forms unless they're admin
        if current_user['role'] != 'admin' and current_user['user_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
            
        forms = get_user_tax_forms(user_id)
        if forms is None:
            return jsonify({'error': 'Failed to fetch tax forms'}), 500
        return jsonify(forms)
    except Exception as e:
        print(f"Get user forms error: {e}")
        return jsonify({'error': 'Failed to fetch tax forms'}), 500

@app.route('/api/dashboard/main_widgets', methods=['GET'])
@admin_required
def get_dashboard_widgets():
    """Get data for the main dashboard widgets"""
    try:
        data = get_dashboard_main_widgets_data()
        if data is None:
            return jsonify({'error': 'Failed to fetch dashboard data'}), 500
            
        # Serialize datetime objects to ISO 8601 format string
        for appt in data.get('upcoming_appointments', []):
            if 'start_time' in appt and isinstance(appt['start_time'], datetime):
                appt['start_time'] = appt['start_time'].isoformat()

        return jsonify(data)
    except Exception as e:
        print(f"Dashboard widgets error: {e}")
        return jsonify({'error': 'Failed to fetch dashboard data'}), 500

@app.route('/api/tax-forms/<form_id>', methods=['GET'])
@client_or_admin_required
def get_form(form_id):
    """Get details of a specific tax form by its ID"""
    try:
        form = get_tax_form_by_id(form_id)
        if form is None:
            return jsonify({'error': 'Tax form not found'}), 404
            
        current_user = get_current_user()
        # Users can only access their own forms unless they're admin
        if current_user['role'] != 'admin' and form['user_id'] != current_user['user_id']:
            return jsonify({'error': 'Access denied'}), 403
            
        return jsonify(form)
    except Exception as e:
        print(f"Get form error: {e}")
        return jsonify({'error': 'Failed to fetch tax form'}), 500

@app.route('/api/tax-forms/user/<int:user_id>/type/<form_type>', methods=['GET'])
@client_or_admin_required
def get_forms_by_type(user_id, form_type):
    """Get tax forms of a specific type for a user"""
    try:
        current_user = get_current_user()
        # Users can only access their own forms unless they're admin
        if current_user['role'] != 'admin' and current_user['user_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
            
        forms = get_tax_forms_by_type(user_id, form_type)
        if forms is None:
            return jsonify({'error': 'Failed to fetch tax forms'}), 500
        return jsonify(forms)
    except Exception as e:
        print(f"Get forms by type error: {e}")
        return jsonify({'error': 'Failed to fetch tax forms'}), 500

@app.route('/api/users', methods=['GET'])
@admin_required
def get_users():
    """Get all users"""
    try:
        users = get_all_users()
        if users is None:
            return jsonify({'error': 'Failed to fetch users'}), 500
        return jsonify(users)
    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

@app.route('/api/clients', methods=['GET'])
@admin_required
def get_clients():
    """Get all clients (users with role 'client')"""
    try:
        clients = get_all_clients()
        if clients is None:
            return jsonify({'error': 'Failed to fetch clients'}), 500
        return jsonify(clients)
    except Exception as e:
        print(f"Get clients error: {e}")
        return jsonify({'error': 'Failed to fetch clients'}), 500

@app.route('/api/tax-form-files/<form_id>', methods=['GET'])
@client_or_admin_required
def api_get_files_for_form(form_id):
    try:
        files = get_files_for_form(form_id)
        return jsonify(files)
    except Exception as e:
        print(f"Get files for form error: {e}")
        return jsonify({'error': 'Failed to fetch files'}), 500

@app.route('/api/appointments', methods=['GET'])
@admin_required
def get_appointments():
    try:
        appointments = get_all_appointments()
        if appointments is None:
            return jsonify({'error': 'Failed to fetch appointments'}), 500
        return jsonify(appointments)
    except Exception as e:
        print(f"Get appointments error: {e}")
        return jsonify({'error': 'Failed to fetch appointments'}), 500

@app.route('/api/services', methods=['GET'])
@jwt_required()
def get_services():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name, duration FROM services")
        services = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(services)
    except Exception as e:
        print(f"Get services error: {e}")
        return jsonify({'error': 'Failed to fetch services'}), 500

@app.route('/api/form-payments/user/<int:user_id>', methods=['GET'])
@client_or_admin_required
def get_user_form_payments(user_id):
    """Get all form payments for a specific user"""
    try:
        current_user = get_current_user()
        # Users can only access their own payments unless they're admin
        if current_user['role'] != 'admin' and current_user['user_id'] != user_id:
            return jsonify({'error': 'Access denied'}), 403
            
        payments = get_form_payments(user_id)
        if payments is None:
            return jsonify({'error': 'Failed to fetch form payments'}), 500
        return jsonify(payments)
    except Exception as e:
        print(f"Get user form payments error: {e}")
        return jsonify({'error': 'Failed to fetch form payments'}), 500

@app.route('/uploads/tax_forms/<path:filename>')
@jwt_required()
def serve_uploaded_file(filename):
    try:
        print("Original filename:", repr(filename))
        filename = filename.replace("\\", "/")
        print("Normalized filename:", repr(filename))
        file_path = f"{UPLOADS_DIR}/{filename}"
        print("Trying to send file:", file_path)
        print("UPLOADS_DIR exists:", os.path.isdir(UPLOADS_DIR))
        print("File exists:", os.path.isfile(file_path))
        dir_path = os.path.dirname(file_path)
        print("Directory listing for", dir_path, ":", os.listdir(dir_path) if os.path.isdir(dir_path) else "Not a directory")
        if not os.path.isfile(file_path):
            print("File not found!")
            return "File not found", 404
        return send_file(file_path)
    except Exception as e:
        print(f"Serve uploaded file error: {e}")
        return jsonify({'error': 'Failed to serve file'}), 500

@app.route('/api/tax-form-files/blob/<int:file_id>', methods=['GET'])
@jwt_required()
def get_tax_form_file_blob(file_id):
    try:
        print(f"Received request for file_id: {file_id}")
        conn = get_db_connection()
        print(f"Database connection: {conn}")
        cursor = conn.cursor(dictionary=True)
        print("Created DB cursor")
        query = 'SELECT file_name, file_type, file_blobs FROM tax_form_files WHERE id = %s'
        print(f"Executing query: {query} with file_id={file_id}")
        cursor.execute(query, (file_id,))
        file = cursor.fetchone()
        print(f"Fetched file row: {file}")
        cursor.close()
        print("Closed DB cursor")
        conn.close()
        print("Closed DB connection")
        if not file or not file['file_blobs']:
            print("File not found or file_blobs is empty")
            return 'File not found', 404
        from flask import send_file
        import io
        print(f"Preparing to send file: {file['file_name']}, type: {file['file_type']}, size: {len(file['file_blobs'])} bytes")
        return send_file(
            io.BytesIO(file['file_blobs']),
            mimetype=file['file_type'],
            as_attachment=False,
            download_name=file['file_name']
        )
    except Exception as e:
        print(f"Get tax form file blob error: {e}")
        return jsonify({'error': 'Failed to fetch file'}), 500

@app.route('/api/tax-form-files/<form_id>/file/<file_name>', methods=['GET'])
@client_or_admin_required
def api_get_file_blob(form_id, file_name):
    try:
        import json
        from flask import jsonify
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT files FROM tax_form_files WHERE tax_form_id = %s"
        cursor.execute(query, (form_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if row and row['files']:
            try:
                files_list = json.loads(row['files'])
                print(f"Looking for file_name: {file_name} in form_id: {form_id}")
                for file in files_list:
                    print(f"Comparing DB file_name: {file.get('file_name')} to requested: {file_name}")
                    if file.get('file_name') == file_name:
                        print("File matched!")
                        return jsonify({
                            'file_blob': file.get('file_blob'),
                            'file_type': file.get('file_type'),
                            'file_name': file.get('file_name')
                        })
                print("No file matched.")
                return jsonify({'error': 'File not found'}), 404
            except Exception as e:
                print(f"Error parsing files: {e}")
                return jsonify({'error': 'Error parsing files'}), 500
        print("No files found for form_id.")
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        print(f"Get file blob error: {e}")
        return jsonify({'error': 'Failed to fetch file'}), 500

@app.route('/api/form-pricing-configs', methods=['GET'])
@admin_required
def get_pricing_configs():
    """Get all form pricing configurations"""
    try:
        configs = get_form_pricing_configs()
        if configs is None:
            return jsonify({'error': 'Failed to fetch pricing configurations'}), 500
        return jsonify(configs)
    except Exception as e:
        print(f"Get pricing configs error: {e}")
        return jsonify({'error': 'Failed to fetch pricing configurations'}), 500

@app.route('/api/form-pricing-configs/<int:config_id>', methods=['PUT'])
@admin_required
def update_pricing_config(config_id):
    """Update a form pricing configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        updated_config = update_form_pricing_config(config_id, data)
        if updated_config is None:
            return jsonify({'error': 'Failed to update pricing configuration'}), 500
        return jsonify(updated_config)
    except Exception as e:
        print(f"Update pricing config error: {e}")
        return jsonify({'error': 'Failed to update pricing configuration'}), 500

@app.route('/api/notifications', methods=['GET'])
@jwt_required()
def get_notifications_route():
    """Get notifications with optional filtering"""
    try:
        current_user = get_current_user()
        user_id = request.args.get('user_id', type=int)
        
        # Non-admin users can only see their own notifications
        if current_user['role'] != 'admin':
            user_id = current_user['user_id']
        
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        include_archived = request.args.get('include_archived', 'false').lower() == 'true'
        
        notifications = get_notifications(user_id, limit, offset, include_archived)
        if notifications is None:
            return jsonify({'error': 'Failed to fetch notifications'}), 500
        return jsonify(notifications)
    except Exception as e:
        print(f"Get notifications error: {e}")
        return jsonify({'error': 'Failed to fetch notifications'}), 500

@app.route('/api/notifications/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_notification_read_route(notification_id):
    """Mark a notification as read"""
    try:
        notification = mark_notification_read(notification_id)
        if notification is None:
            return jsonify({'error': 'Failed to mark notification as read'}), 500
        return jsonify(notification)
    except Exception as e:
        print(f"Mark notification read error: {e}")
        return jsonify({'error': 'Failed to mark notification as read'}), 500

@app.route('/api/notifications/<int:notification_id>/archive', methods=['POST'])
@jwt_required()
def archive_notification_route(notification_id):
    """Archive a notification"""
    try:
        success = archive_notification(notification_id)
        if success is None:
            return jsonify({'error': 'Failed to archive notification'}), 500
        return jsonify({'success': True})
    except Exception as e:
        print(f"Archive notification error: {e}")
        return jsonify({'error': 'Failed to archive notification'}), 500

@app.route('/api/notifications/<int:notification_id>/unarchive', methods=['POST'])
@jwt_required()
def unarchive_notification_route(notification_id):
    """Unarchive a notification"""
    try:
        notification = unarchive_notification(notification_id)
        if notification is None:
            return jsonify({'error': 'Failed to unarchive notification'}), 500
        return jsonify(notification)
    except Exception as e:
        print(f"Unarchive notification error: {e}")
        return jsonify({'error': 'Failed to unarchive notification'}), 500

@app.route('/api/notifications/mark-all-read', methods=['POST'])
@jwt_required()
def mark_all_notifications_read_route():
    """Mark all unread notifications as read"""
    try:
        current_user = get_current_user()
        # Get user_id from request body or use current user
        user_id = request.json.get('user_id') if request.json else None
        
        # Non-admin users can only mark their own notifications as read
        if current_user['role'] != 'admin':
            user_id = current_user['user_id']

        success = mark_all_notifications_read(user_id=user_id)
        if success is None:
            return jsonify({'error': 'Failed to mark all notifications as read'}), 500
        return jsonify({'success': True})
    except Exception as e:
        print(f"Mark all notifications read error: {e}")
        return jsonify({'error': 'Failed to mark all notifications as read'}), 500

@app.route('/api/form-payments', methods=['GET'])
@admin_required
def get_all_form_payments_route():
    """Get all form payments for all users"""
    try:
        payments = get_all_form_payments()
        if payments is None:
            return jsonify({'error': 'Failed to fetch form payments'}), 500
        return jsonify(payments)
    except Exception as e:
        print(f"Get all form payments error: {e}")
        return jsonify({'error': 'Failed to fetch form payments'}), 500

@app.route('/api/tax-forms/type/<form_type>', methods=['GET'])
@admin_required
def get_all_tax_forms_by_type_route(form_type):
    """Get all tax forms of a specific type for all users"""
    try:
        forms = get_all_tax_forms_by_type(form_type)
        if forms is None:
            return jsonify({'error': 'Failed to fetch tax forms'}), 500
        return jsonify(forms)
    except Exception as e:
        print(f"Get all tax forms by type error: {e}")
        return jsonify({'error': 'Failed to fetch tax forms'}), 500

@app.route('/api/services/<int:service_id>', methods=['PUT'])
@admin_required
def update_service(service_id):
    try:
        data = request.json
        name = data.get('name')
        duration = data.get('duration')
        if not name or duration is None:
            return jsonify({'error': 'Name and duration are required.'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE services SET name=%s, duration=%s WHERE id=%s",
            (name, duration, service_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Update service error: {e}")
        return jsonify({'error': 'Failed to update service'}), 500

@app.route('/api/booking-config', methods=['GET'])
@admin_required
def get_booking_config():
    try:
        import datetime
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM booking_config LIMIT 1")
        config = cursor.fetchone()
        cursor.close()
        conn.close()
        if config:
            for k, v in config.items():
                # Convert datetime.time to string (e.g., '09:00:00')
                if isinstance(v, datetime.time):
                    config[k] = v.strftime('%H:%M:%S')
                # Convert datetime.timedelta to string (e.g., '01:30:00')
                elif isinstance(v, datetime.timedelta):
                    total_seconds = int(v.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    seconds = total_seconds % 60
                    config[k] = f"{hours:02}:{minutes:02}:{seconds:02}"
                # Convert any other non-serializable type to string
                elif not isinstance(v, (str, int, float, bool, type(None), dict, list)):
                    config[k] = str(v)
        return jsonify(config)
    except Exception as e:
        print(f"Get booking config error: {e}")
        return jsonify({'error': 'Failed to fetch booking configuration'}), 500

@app.route('/api/booking-config/<int:config_id>', methods=['PUT'])
@admin_required
def update_booking_config(config_id):
    try:
        data = request.json
        fields = [
            'working_hours_start', 'working_hours_end', 'slot_duration', 'buffer_between_appointments',
            'max_advance_booking_days', 'min_advance_booking_hours', 'max_appointments_per_day',
            'max_appointments_per_user', 'allowed_booking_days', 'holidays', 'timezone'
        ]
        values = [data.get(f) for f in fields]
        if None in values:
            return jsonify({'error': 'All fields are required.'}), 400
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE booking_config SET
                working_hours_start=%s,
                working_hours_end=%s,
                slot_duration=%s,
                buffer_between_appointments=%s,
                max_advance_booking_days=%s,
                min_advance_booking_hours=%s,
                max_appointments_per_day=%s,
                max_appointments_per_user=%s,
                allowed_booking_days=%s,
                holidays=%s,
                timezone=%s
            WHERE id=%s
        """, (*values, config_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        print(f"Update booking config error: {e}")
        return jsonify({'error': 'Failed to update booking configuration'}), 500

# Error handlers
@app.errorhandler(401)
def unauthorized(error):
    return jsonify({'error': 'Unauthorized access'}), 401

@app.errorhandler(403)
def forbidden(error):
    return jsonify({'error': 'Forbidden - insufficient permissions'}), 403

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)