import os

class Config:
    # Server Configuration
    SERVER_URL = os.getenv('SERVER_URL', 'http://192.168.1.145:8002')
    PORT = int(os.getenv('PORT', 5000))  # Railway 会提供 PORT 环境变量
    DEBUG = os.getenv('RAILWAY_ENVIRONMENT') != 'production'  # 在Railway生产环境中关闭DEBUG
    
    # File Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'doc': 'application/msword',
        'txt': 'text/plain',
        'md': 'text/markdown',
        'html': 'text/html',
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'xls': 'application/vnd.ms-excel',
    }
    
    # Conversion Settings
    CONVERSION_TIMEOUT = 300  # seconds
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS 