import os

class Config:
    # Server Configuration
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = True
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    
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
        'caj': 'application/caj',  # 中国知网CAJ格式
    }
    
    # Conversion Settings
    CONVERSION_TIMEOUT = 300  # seconds
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS 