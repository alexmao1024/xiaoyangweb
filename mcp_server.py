#!/usr/bin/env python3
"""
文档转换 MCP 服务器
提供文档格式转换功能的 Model Context Protocol 服务器
"""

import asyncio
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

import requests
import pypandoc
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ServerCapabilities
)

from config import Config

# 配置详细日志 - 输出到文件和控制台
import sys
log_file = Path(__file__).parent / "mcp_server.log"
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("document-converter-mcp")

# 启动时记录日志
logger.info("=" * 50)
logger.info("MCP 服务器启动")
logger.info(f"Python 版本: {sys.version}")
logger.info(f"工作目录: {Path.cwd()}")
logger.info(f"日志文件: {log_file}")
logger.info("=" * 50)

# 创建 MCP 服务器实例
server = Server("document-converter")

# 支持的文件格式映射
SUPPORTED_FORMATS = {
    'pdf': ['MARKDOWN', 'TEXT'],
    'docx': ['MARKDOWN', 'TEXT'], 
    'doc': ['MARKDOWN', 'TEXT'],
    'txt': ['MARKDOWN', 'TEXT'],
    'html': ['MARKDOWN', 'TEXT'],
    'md': ['MARKDOWN', 'TEXT', 'PDF', 'DOCX']
}

def convert_document_with_api(file_path: str, export_format: str) -> bytes:
    """使用外部 API 转换文档"""
    try:
        logger.info(f"调用外部API转换: {file_path} -> {export_format}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f)}
            data = {'export_format': export_format}
            response = requests.post(
                f"{Config.SERVER_URL}/convert", 
                files=files, 
                data=data, 
                timeout=Config.CONVERSION_TIMEOUT
            )
        
        response.raise_for_status()
        logger.info("API转换成功")
        return response.content
        
    except Exception as e:
        logger.error(f"API转换失败: {e}")
        raise

def convert_markdown_to_pdf(file_path: str) -> bytes:
    """使用 Pandoc 将 Markdown 转换为 PDF"""
    try:
        logger.info(f"使用Pandoc转换MD到PDF: {file_path}")
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf_path = temp_pdf.name
        
        extra_args = [
            '--pdf-engine=xelatex',
            '-V', 'CJKmainfont=SimSun',
            '-V', 'geometry:margin=1in',
            '--highlight-style=tango'
        ]
        
        pypandoc.convert_file(
            file_path,
            'pdf',
            outputfile=temp_pdf_path,
            extra_args=extra_args
        )
        
        with open(temp_pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        os.unlink(temp_pdf_path)
        logger.info("Pandoc PDF转换成功")
        return pdf_content
        
    except Exception as e:
        logger.error(f"Pandoc PDF转换失败: {e}")
        raise

def convert_markdown_to_docx(file_path: str) -> bytes:
    """使用 Pandoc 将 Markdown 转换为 DOCX"""
    try:
        logger.info(f"使用Pandoc转换MD到DOCX: {file_path}")
        
        with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_docx:
            temp_docx_path = temp_docx.name
        
        pypandoc.convert_file(file_path, 'docx', outputfile=temp_docx_path)
        
        with open(temp_docx_path, 'rb') as f:
            docx_content = f.read()
        
        os.unlink(temp_docx_path)
        logger.info("Pandoc DOCX转换成功")
        return docx_content
        
    except Exception as e:
        logger.error(f"Pandoc DOCX转换失败: {e}")
        raise

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出可用的工具"""
    logger.info("收到 list_tools 请求")
    tools = [
        Tool(
            name="convert_document",
            description="转换文档格式。支持 PDF、Word、Markdown、文本等格式之间的转换。",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_file_path": {
                        "type": "string",
                        "description": "要转换的输入文件的完整路径"
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["MARKDOWN", "TEXT", "PDF", "DOCX"],
                        "description": "目标输出格式"
                    },
                    "output_file_path": {
                        "type": "string",
                        "description": "输出文件的完整路径（可选，如果不提供将自动生成）"
                    }
                },
                "required": ["input_file_path", "output_format"]
            }
        ),
        Tool(
            name="check_conversion_service",
            description="检查外部文档转换服务的状态和可用性",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        ),
        Tool(
            name="get_supported_formats",
            description="获取支持的文件格式和转换组合",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_format": {
                        "type": "string",
                        "description": "输入文件格式（可选），如果提供则返回该格式支持的输出格式"
                    }
                },
                "additionalProperties": False
            }
        )
    ]
    logger.info(f"返回 {len(tools)} 个工具")
    return tools

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    """处理工具调用"""
    logger.info(f"收到工具调用: {name}, 参数: {arguments}")
    if arguments is None:
        arguments = {}
    
    try:
        if name == "convert_document":
            return await handle_convert_document(arguments)
        elif name == "check_conversion_service":
            return await handle_check_service(arguments)
        elif name == "get_supported_formats":
            return await handle_get_formats(arguments)
        else:
            raise ValueError(f"未知的工具: {name}")
            
    except Exception as e:
        logger.error(f"工具调用失败 {name}: {e}")
        return [TextContent(type="text", text=f"错误: {str(e)}")]

async def handle_convert_document(arguments: dict[str, Any]) -> list[TextContent]:
    """处理文档转换"""
    input_file_path = arguments.get("input_file_path")
    output_format = arguments.get("output_format", "").upper()
    output_file_path = arguments.get("output_file_path")
    
    if not input_file_path:
        return [TextContent(type="text", text="错误: 必须提供输入文件路径")]
    
    if not os.path.exists(input_file_path):
        return [TextContent(type="text", text=f"错误: 输入文件不存在: {input_file_path}")]
    
    if output_format not in ["MARKDOWN", "TEXT", "PDF", "DOCX"]:
        return [TextContent(type="text", text=f"错误: 不支持的输出格式: {output_format}")]
    
    # 检查文件格式兼容性
    file_ext = Path(input_file_path).suffix.lower().lstrip('.')
    if file_ext not in SUPPORTED_FORMATS:
        return [TextContent(type="text", text=f"错误: 不支持的输入文件格式: {file_ext}")]
    
    if output_format not in SUPPORTED_FORMATS[file_ext]:
        return [TextContent(type="text", text=f"错误: {file_ext} 格式不支持转换为 {output_format}")]
    
    # 生成输出文件路径
    if not output_file_path:
        input_path = Path(input_file_path)
        output_ext = output_format.lower()
        if output_ext == 'markdown':
            output_ext = 'md'
        output_file_path = str(input_path.parent / f"{input_path.stem}_converted.{output_ext}")
    
    try:
        # 执行转换
        if file_ext == 'md' and output_format == 'PDF':
            result_content = convert_markdown_to_pdf(input_file_path)
        elif file_ext == 'md' and output_format == 'DOCX':
            result_content = convert_markdown_to_docx(input_file_path)
        else:
            result_content = convert_document_with_api(input_file_path, output_format)
        
        # 保存结果
        with open(output_file_path, 'wb') as f:
            f.write(result_content)
        
        file_size = len(result_content)
        return [TextContent(
            type="text", 
            text=f"转换成功!\n输入文件: {input_file_path}\n输出文件: {output_file_path}\n输出格式: {output_format}\n文件大小: {file_size} 字节"
        )]
        
    except Exception as e:
        return [TextContent(type="text", text=f"转换失败: {str(e)}")]

async def handle_check_service(arguments: dict[str, Any]) -> list[TextContent]:
    """检查外部转换服务状态"""
    try:
        response = requests.get(f"{Config.SERVER_URL}/", timeout=5)
        if response.ok:
            return [TextContent(
                type="text", 
                text=f"✅ 外部转换服务正常\n服务地址: {Config.SERVER_URL}\n状态码: {response.status_code}"
            )]
        else:
            return [TextContent(
                type="text", 
                text=f"⚠️ 外部转换服务异常\n服务地址: {Config.SERVER_URL}\n状态码: {response.status_code}"
            )]
    except Exception as e:
        return [TextContent(
            type="text", 
            text=f"❌ 无法连接到外部转换服务\n服务地址: {Config.SERVER_URL}\n错误: {str(e)}"
        )]

async def handle_get_formats(arguments: dict[str, Any]) -> list[TextContent]:
    """获取支持的格式信息"""
    input_format = arguments.get("input_format")
    
    if input_format:
        input_format = input_format.lower()
        if input_format in SUPPORTED_FORMATS:
            output_formats = SUPPORTED_FORMATS[input_format]
            return [TextContent(
                type="text",
                text=f"输入格式 '{input_format}' 支持的输出格式: {', '.join(output_formats)}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"不支持的输入格式: {input_format}"
            )]
    else:
        format_info = []
        for input_fmt, output_fmts in SUPPORTED_FORMATS.items():
            format_info.append(f"{input_fmt}: {', '.join(output_fmts)}")
        
        return [TextContent(
            type="text",
            text="支持的文档格式转换:\n" + "\n".join(format_info)
        )]

async def main():
    """启动 MCP 服务器"""
    logger.info("正在启动 MCP 服务器...")
    try:
        # 通过 stdio 运行服务器
        async with stdio_server() as (read_stream, write_stream):
            logger.info("stdio 服务器已创建，开始运行...")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="document-converter",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools={}
                    )
                )
            )
    except Exception as e:
        logger.error(f"MCP 服务器运行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        logger.info("开始运行 asyncio.run(main())")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("MCP 服务器被用户中断")
    except Exception as e:
        logger.error(f"MCP 服务器异常退出: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 