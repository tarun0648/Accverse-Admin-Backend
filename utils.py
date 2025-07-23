import mysql.connector
from mysql.connector import Error
from config import Config
import json

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