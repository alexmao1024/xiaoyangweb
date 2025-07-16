"""
文档转换路由模块
处理文档转换相关的API路由
"""

import os
import io
import logging
from flask import Blueprint, request, jsonify, send_file, current_app
from config import Config
from modules.document_converter import get_document_converter
from modules.docling_service import is_docling_available

logger = logging.getLogger(__name__)

# 创建蓝图
convert_bp = Blueprint('convert', __name__)

@convert_bp.route('/check_server')
def check_server():
    """检查服务状态"""
    try:
        # 检查 Docling 服务是否可用
        docling_status = is_docling_available()
        
        logger.info(f"服务状态检查 - Docling: {'可用' if docling_status else '不可用'}")
        return jsonify({'status': True, 'docling_available': docling_status})
    except Exception as e:
        logger.error(f"检查服务状态失败: {e}")
        return jsonify({'status': False, 'error': str(e)})

@convert_bp.route('/convert', methods=['POST'])
def convert():
    """处理文件转换请求"""
    if 'file' not in request.files:
        logger.error("请求中没有文件部分")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    export_format = request.form.get('export_format', 'MARKDOWN').upper()

    if file.filename == '':
        logger.error("没有选择文件")
        return jsonify({'error': 'No selected file'}), 400

    if not Config.allowed_file(file.filename):
        logger.error(f"文件类型不允许: {file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400

    filename = file.filename
    input_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    output_path = None

    try:
        # 保存上传的文件
        file.save(input_path)
        logger.info(f"文件已保存到: {input_path}")
        logger.debug(f"上传文件大小: {os.path.getsize(input_path)} bytes")

        # 生成输出文件路径
        file_extension = filename.rsplit('.', 1)[1].lower()
        output_filename_base = filename.rsplit('.', 1)[0]
        logger.debug(f"输入文件扩展名: {file_extension}, 基础文件名: {output_filename_base}")
        
        output_ext = export_format.lower()
        if output_ext == 'markdown': 
            output_ext = 'md'
        elif output_ext == 'xlsx':
            output_ext = 'xlsx'
        
        output_filename = f"{output_filename_base}.{output_ext}"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)

        # 使用统一的文档转换器
        converter = get_document_converter()
        converter.convert_document(input_path, output_path, export_format)
        
        logger.info(f"转换成功: {output_path}")

        # 将输出文件读入内存
        with open(output_path, 'rb') as f:
            buffer = io.BytesIO(f.read())
        
        # 立即从磁盘删除临时输出文件
        os.remove(output_path)
        logger.info(f"已将输出文件读入内存并删除磁盘文件: {output_path}")

        buffer.seek(0)
        
        # 返回文件
        mimetype = current_app.config['ALLOWED_EXTENSIONS'].get(output_ext, 'application/octet-stream')
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        logger.error(f"转换过程中发生严重错误: {e}", exc_info=True)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    finally:
        # 清理输入文件
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
            logger.info(f"已清理输入文件: {input_path}") 