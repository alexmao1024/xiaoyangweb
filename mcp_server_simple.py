#!/usr/bin/env python3
"""
简化的MCP文档转换服务器 - 使用FastMCP
"""

import os
import sys
import requests
import logging
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_server_simple.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("document-converter-simple")

# 支持的格式映射
SUPPORTED_FORMATS = {
    'pdf': ['MARKDOWN', 'TEXT', 'DOCX'],
    'doc': ['MARKDOWN', 'TEXT', 'PDF'],
    'docx': ['MARKDOWN', 'TEXT', 'PDF'],
    'txt': ['MARKDOWN', 'PDF', 'DOCX'],
    'md': ['PDF', 'DOCX', 'TEXT']
}

# 创建FastMCP服务器
mcp = FastMCP("document-converter")

def convert_document_with_api(file_path: str, export_format: str) -> bytes:
    """使用外部API转换文档"""
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            data = {'export_format': export_format.upper()}
            
            response = requests.post(
                f"{Config.SERVER_URL}/convert",
                files=files,
                data=data,
                timeout=Config.TIMEOUT
            )
            response.raise_for_status()
            return response.content
    except Exception as e:
        logger.error(f"API转换失败: {e}")
        raise

@mcp.tool()
def convert_document(input_file_path: str, output_format: str, output_file_path: str = None) -> str:
    """
    转换文档格式。支持 PDF、Word、Markdown、文本等格式之间的转换。
    
    Args:
        input_file_path: 要转换的输入文件的完整路径
        output_format: 目标输出格式 (MARKDOWN, TEXT, PDF, DOCX)
        output_file_path: 输出文件的完整路径（可选，如果不提供将自动生成）
    
    Returns:
        转换结果的详细信息
    """
    logger.info(f"收到转换请求: {input_file_path} -> {output_format}")
    
    # 参数验证
    if not input_file_path:
        return "错误: 必须提供输入文件路径"
    
    if not os.path.exists(input_file_path):
        return f"错误: 输入文件不存在: {input_file_path}"
    
    output_format = output_format.upper()
    if output_format not in ["MARKDOWN", "TEXT", "PDF", "DOCX"]:
        return f"错误: 不支持的输出格式: {output_format}"
    
    # 检查文件格式兼容性
    file_ext = Path(input_file_path).suffix.lower().lstrip('.')
    if file_ext not in SUPPORTED_FORMATS:
        return f"错误: 不支持的输入文件格式: {file_ext}"
    
    if output_format not in SUPPORTED_FORMATS[file_ext]:
        return f"错误: {file_ext} 格式不支持转换为 {output_format}"
    
    # 生成输出文件路径
    if not output_file_path:
        input_path = Path(input_file_path)
        output_ext = output_format.lower()
        if output_ext == 'markdown':
            output_ext = 'md'
        output_file_path = str(input_path.parent / f"{input_path.stem}_converted.{output_ext}")
    
    try:
        # 执行转换
        result_content = convert_document_with_api(input_file_path, output_format)
        
        # 保存结果
        with open(output_file_path, 'wb') as f:
            f.write(result_content)
        
        file_size = len(result_content)
        return f"转换成功!\n输入文件: {input_file_path}\n输出文件: {output_file_path}\n输出格式: {output_format}\n文件大小: {file_size} 字节"
        
    except Exception as e:
        logger.error(f"转换失败: {e}")
        return f"转换失败: {str(e)}"

@mcp.tool()
def check_conversion_service() -> str:
    """
    检查外部文档转换服务的状态和可用性
    
    Returns:
        服务状态信息
    """
    try:
        response = requests.get(f"{Config.SERVER_URL}/", timeout=5)
        if response.ok:
            return f"✅ 外部转换服务正常\n服务地址: {Config.SERVER_URL}\n状态码: {response.status_code}"
        else:
            return f"⚠️ 外部转换服务异常\n服务地址: {Config.SERVER_URL}\n状态码: {response.status_code}"
    except Exception as e:
        return f"❌ 无法连接到外部转换服务\n服务地址: {Config.SERVER_URL}\n错误: {str(e)}"

@mcp.tool()
def get_supported_formats(input_format: str = None) -> str:
    """
    获取支持的文件格式和转换组合
    
    Args:
        input_format: 输入文件格式（可选），如果提供则返回该格式支持的输出格式
    
    Returns:
        支持的格式信息
    """
    if input_format:
        input_format = input_format.lower()
        if input_format in SUPPORTED_FORMATS:
            output_formats = SUPPORTED_FORMATS[input_format]
            return f"输入格式 '{input_format}' 支持的输出格式: {', '.join(output_formats)}"
        else:
            return f"不支持的输入格式: {input_format}"
    else:
        format_info = []
        for input_fmt, output_fmts in SUPPORTED_FORMATS.items():
            format_info.append(f"{input_fmt}: {', '.join(output_fmts)}")
        
        return "支持的文档格式转换:\n" + "\n".join(format_info)

if __name__ == "__main__":
    logger.info("启动简化版MCP文档转换服务器...")
    try:
        mcp.run()
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1) 