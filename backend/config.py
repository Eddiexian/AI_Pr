import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-123'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Defaults
    MODE = 'DEV' # 'DEV' or 'PROD'

class DevConfig(Config):
    MODE = 'DEV'
    # Use SQLite for local dev of Layout DB (simulating SQL Server)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///layout_manager.db' 
    
    # Mock Data Flags
    USE_MOCK_DATA = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    MODE = 'TEST'

class ProdConfig(Config):
    MODE = 'PROD'
    # SQL Server Connection String Example (Update with real creds later)
    # Driver={ODBC Driver 17 for SQL Server};Server=myServerAddress;Database=myDataBase;Uid=myUsername;Pwd=myPassword;
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQL_SERVER_URI') or 'mssql+pyodbc://user:pass@server/db?driver=ODBC+Driver+17+for+SQL+Server'
    
    # Oracle Connection Strings (for raw data)
    ORACLE_CELODS_URI = os.environ.get('ORACLE_CELODS_URI')
    ORACLE_BEOL_URI = os.environ.get('ORACLE_BEOL_URI')
    
    USE_MOCK_DATA = False

config = {
    'development': DevConfig,
    'production': ProdConfig,
    'testing': TestingConfig,
    'default': DevConfig
}
