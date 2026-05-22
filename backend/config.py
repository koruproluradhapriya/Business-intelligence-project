import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'insightiq-dev-secret-change-in-prod')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True') == 'True'

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'insightiq-jwt-secret-change-in-prod')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # MongoDB
    MONGO_URI = os.environ.get('MONGO_URI', '')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', os.environ.get('MONGO_DB_NAME', 'InsightIQ'))
    MONGO_DB_NAME = DATABASE_NAME
    MONGO_CONNECT_RETRIES = int(os.environ.get('MONGO_CONNECT_RETRIES', '3'))
    MONGO_SERVER_SELECTION_TIMEOUT_MS = int(os.environ.get('MONGO_SERVER_SELECTION_TIMEOUT_MS', '15000'))
    MONGO_CONNECT_TIMEOUT_MS = int(os.environ.get('MONGO_CONNECT_TIMEOUT_MS', '15000'))
    MONGO_SOCKET_TIMEOUT_MS = int(os.environ.get('MONGO_SOCKET_TIMEOUT_MS', '30000'))
    MONGO_MAX_POOL_SIZE = int(os.environ.get('MONGO_MAX_POOL_SIZE', '30'))
    MONGO_MIN_POOL_SIZE = int(os.environ.get('MONGO_MIN_POOL_SIZE', '1'))
    ALLOW_DB_FALLBACK = os.environ.get('ALLOW_DB_FALLBACK', 'False') == 'True'

    # File uploads
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'json', 'tsv', 'parquet'}

    # AI / Anthropic
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')
    ANTHROPIC_MODEL = os.environ.get('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514')

    # Offline mode (disables external API calls)
    OFFLINE_MODE = os.environ.get('OFFLINE_MODE', 'False') == 'True'

    # CORS
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:3000').split(',')


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)


config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
