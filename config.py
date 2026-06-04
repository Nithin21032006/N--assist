import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'n_assist_fallback_secret_key')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database Configuration
    db_host = os.getenv('MYSQL_HOST')
    db_user = os.getenv('MYSQL_USER')
    db_pass = os.getenv('MYSQL_PASSWORD', '')
    db_name = os.getenv('MYSQL_DB')
    db_port = os.getenv('MYSQL_PORT', '3306')
    
    if db_host and db_user and db_name:
        # Construct MySQL connection URL using PyMySQL
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        USING_MYSQL = True
        print(f"[Config] Using MySQL Database: {db_name} at {db_host}")
    else:
        # Fallback to local SQLite database
        base_dir = os.path.abspath(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'n_assist.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        USING_MYSQL = False
        print(f"[Config] MySQL not configured. Falling back to local SQLite: {db_path}")

    # Email SMTP Settings
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'n-assist-no-reply@gmail.com')

    # Twilio / WhatsApp Settings
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER', 'whatsapp:+14155238886')
