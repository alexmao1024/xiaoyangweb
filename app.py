"""
小羊的工具箱 - 主应用
一个充满爱意的个人工具箱项目
"""

import os
import logging

# 在导入任何其他模块之前设置离线模式
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'

from flask import Flask
from config import Config

# 导入路由模块
from routes.main_routes import main_bp
from routes.convert_routes import convert_bp

# --- 日志配置 ---
log_file = 'app.log'

# 使用追加模式，避免因文件被占用而导致的启动错误
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# --- 日志配置结束 ---

def create_app():
    """创建 Flask 应用实例"""
    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保上传和输出目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(app.config['OUTPUT_FOLDER']):
        os.makedirs(app.config['OUTPUT_FOLDER'])

    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(convert_bp)

    logging.info("🐑 小羊的工具箱启动成功！")
    
    return app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )