import mysql.connector
from mysql.connector import Error
from config import Config
import json
import jwt
from functools import wraps
from flask import request, jsonify
from datetime import datetime, timedelta, timezone

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def parse_form_data(form_data):
    """Parse JSON string form data into dictionary"""
    if isinstance(form_data, str):
        try:
            return json.loads(form_data)
        except json.JSONDecodeError:
            return {}
    return form_data

def format_tax_form_response(tax_form, files=None):
    """Format tax form data for API response"""
    form_data = parse_form_data(tax_form['form_data'])
    
    response = {
        'id': tax_form['id'],
        'user_id': tax_form['user_id'],
        'form_type': tax_form['form_type'],
        'status': tax_form['status'],
        'notes': tax_form['notes'],
        'created_at': tax_form['created_at'].isoformat() if tax_form['created_at'] else None,
        'updated_at': tax_form['updated_at'].isoformat() if tax_form['updated_at'] else None,
        'form_data': form_data
    }
    
    if files:
        response['files'] = files
        
    return response

def generate_jwt_token(user_id, email, role):
    """Generate JWT token for authenticated user"""
    try:
        payload = {
            'user_id': user_id,
            'email': email,
            'role': role,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24),  # Token expires in 24 hours
            'iat': datetime.now(timezone.utc)
        }
        token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm='HS256')
        return token
    except Exception as e:
        print(f"Error generating JWT token: {e}")
        return None

def verify_jwt_token(token):
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return {'error': 'Token has expired'}
    except jwt.InvalidTokenError:
        return {'error': 'Invalid token'}
    except Exception as e:
        print(f"Error verifying JWT token: {e}")
        return {'error': 'Token verification failed'}

def jwt_required(roles=None):
    """Decorator to require JWT authentication for routes
    
    Args:
        roles (list): List of roles allowed to access the endpoint. If None, any authenticated user can access.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get token from Authorization header
                auth_header = request.headers.get('Authorization')
                if not auth_header:
                    return jsonify({'error': 'Authorization header is required'}), 401
                
                # Extract token from "Bearer <token>" format
                try:
                    token = auth_header.split(' ')[1]
                except IndexError:
                    return jsonify({'error': 'Invalid authorization header format. Use: Bearer <token>'}), 401
                
                # Verify token
                payload = verify_jwt_token(token)
                if 'error' in payload:
                    return jsonify({'error': payload['error']}), 401
                
                # Check if user role is allowed
                if roles and payload.get('role') not in roles:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                
                # Add user info to request context
                request.current_user = {
                    'user_id': payload.get('user_id'),
                    'email': payload.get('email'),
                    'role': payload.get('role')
                }
                
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"JWT validation error: {e}")
                return jsonify({'error': 'Authentication failed'}), 401
                
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return jwt_required(roles=['admin'])(f)

def client_or_admin_required(f):
    """Decorator to require client or admin role"""
    return jwt_required(roles=['client', 'admin'])(f)

def get_current_user():
    """Get current authenticated user from request context"""
    return getattr(request, 'current_user', None)