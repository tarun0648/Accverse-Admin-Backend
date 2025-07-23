import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MYSQL_HOST = os.getenv('MYSQL_HOST', '16.176.52.161')
    MYSQL_USER = os.getenv('MYSQL_USER', 'remote_user')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Accverse@1234')
    MYSQL_DB = os.getenv('MYSQL_DB', 'Accverse')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    
    # File upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/opt/app/accverse-backend/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size 

    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USER = os.getenv('EMAIL_USER', 'kaurnancy186@gmail.com')
    EMAIL_PASS = os.getenv('EMAIL_PASS', 'pwnc mmiy rfkn gttd')
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production-please-make-it-long-and-random')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours in seconds