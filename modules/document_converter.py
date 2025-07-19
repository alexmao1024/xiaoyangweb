"""
统一文档转换模块
整合本地转换（pypandoc, pandas）和 Docling 转换功能
"""

import os
import logging
import pandas as pd
import pypandoc
from .docling_service import get_docling_processor, is_docling_available
from .markdown_processor import parse_markdown_to_structured_data
from .caj_converter import CAJConverter, convert_caj_to_pdf

logger = logging.getLogger(__name__)

class DocumentConverter:
    """统一文档转换器"""
    
    def __init__(self):
        """初始化转换器"""
        self.docling_processor = get_docling_processor()
    
    def convert_document(self, input_path: str, output_path: str, export_format: str) -> None:
        """
        转换文档
        
        Args:
            input_path: 输入文件路径
            output_path: 输出文件路径
            export_format: 导出格式
            
        Raises:
            Exception: 转换失败时抛出异常
        """
        file_extension = self._get_file_extension(input_path)
        export_format = export_format.upper()
        
        logger.debug(f"文件扩展名: {file_extension}, 目标格式: {export_format}")
        logger.info(f"开始转换: {input_path} -> {output_path} (格式: {export_format})")
        
        # 根据文件类型和目标格式选择转换策略
        if file_extension == 'caj':
            # CAJ文件转换（自动处理真正的CAJ和伪装的PDF）
            logger.debug("选择CAJ转换策略")
            self._convert_caj_file(input_path, output_path, export_format)
        elif file_extension == 'md' and export_format in ['PDF', 'DOCX', 'XLSX']:
            # Markdown 本地转换
            logger.debug("选择本地Markdown转换策略")
            self._convert_markdown_local(input_path, output_path, export_format)
        elif self._should_use_docling(file_extension, export_format):
            # 使用 Docling 转换
            logger.debug("选择Docling转换策略")
            self._convert_with_docling(input_path, output_path, export_format)
        else:
            # 回退到外部 API（如果配置了的话）
            logger.debug("没有可用的转换策略")
            raise Exception(f"不支持的转换: {file_extension} -> {export_format}")
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _should_use_docling(self, file_extension: str, export_format: str) -> bool:
        """判断是否应该使用 Docling 转换"""
        if not is_docling_available():
            return False
        
        # 需要 OCR 或复杂解析的格式
        complex_formats = ['pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'html']
        return file_extension in complex_formats
    
    def _convert_markdown_local(self, input_path: str, output_path: str, export_format: str) -> None:
        """本地转换 Markdown 文件"""
        try:
            if export_format == 'PDF':
                self._markdown_to_pdf(input_path, output_path)
            elif export_format == 'DOCX':
                self._markdown_to_docx(input_path, output_path)
            elif export_format == 'XLSX':
                self._markdown_to_excel(input_path, output_path)
            else:
                raise Exception(f"不支持的 Markdown 转换格式: {export_format}")
        except Exception as e:
            logger.error(f"Markdown 本地转换失败: {e}")
            raise
    
    def _convert_with_docling(self, input_path: str, output_path: str, export_format: str) -> None:
        """使用 Docling 转换文档"""
        try:
            # Docling 目前主要支持转换为 MARKDOWN 和 TEXT
            if export_format in ['MARKDOWN', 'TEXT']:
                content, file_extension = self.docling_processor.convert_document(
                    input_path, export_format
                )
                
                # 写入输出文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                logger.info(f"Docling 转换成功: {output_path}")
            else:
                # 对于其他格式，先转换为 Markdown，然后本地转换
                content, _ = self.docling_processor.convert_document(input_path, "MARKDOWN")
                
                # 创建临时 Markdown 文件
                temp_md_path = input_path + ".temp.md"
                try:
                    with open(temp_md_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # 使用本地转换处理 Markdown -> 目标格式
                    self._convert_markdown_local(temp_md_path, output_path, export_format)
                finally:
                    # 清理临时文件
                    if os.path.exists(temp_md_path):
                        os.remove(temp_md_path)
                        
        except Exception as e:
            logger.error(f"Docling 转换失败: {e}")
            raise
    
    def _markdown_to_pdf(self, input_path: str, output_path: str) -> None:
        """Markdown 转 PDF"""
        try:
            logger.info(f"Pandoc PDF 转换: {input_path} -> {output_path}")
            extra_args = ['--pdf-engine=xelatex', '-V', 'mainfont=SimSun']
            pypandoc.convert_file(input_path, 'pdf', outputfile=output_path, extra_args=extra_args)
            logger.info("Pandoc PDF 转换成功")
        except Exception as e:
            logger.error(f"Pandoc PDF 转换失败: {e}")
            raise
    
    def _markdown_to_docx(self, input_path: str, output_path: str) -> None:
        """Markdown 转 DOCX"""
        try:
            logger.info(f"Pandoc DOCX 转换: {input_path} -> {output_path}")
            pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
            logger.info("Pandoc DOCX 转换成功")
        except Exception as e:
            logger.error(f"Pandoc DOCX 转换失败: {e}")
            raise
    
    def _markdown_to_excel(self, input_path: str, output_path: str) -> None:
        """Markdown 转 Excel"""
        try:
            logger.info(f"Markdown 转 Excel: {input_path} -> {output_path}")
            
            # 读取 Markdown 文件
            with open(input_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # 解析 Markdown 内容
            parsed_data = parse_markdown_to_structured_data(md_content)
            
            # 创建 Excel 文件
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                if parsed_data['tables']:
                    # 如果有表格，每个表格一个工作表
                    for i, table_data in enumerate(parsed_data['tables']):
                        sheet_name = f'表格_{i+1}' if len(parsed_data['tables']) > 1 else '表格'
                        table_data.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # 创建文档结构工作表
                if parsed_data['structure']:
                    structure_df = pd.DataFrame(parsed_data['structure'])
                    structure_df.to_excel(writer, sheet_name='文档结构', index=False)
                
                # 如果没有表格和结构化数据，创建一个包含全文的工作表
                if not parsed_data['tables'] and not parsed_data['structure']:
                    lines = [line for line in md_content.split('\n') if line.strip()]
                    df = pd.DataFrame({'内容': lines})
                    df.to_excel(writer, sheet_name='文档内容', index=False)
            
            logger.info("Markdown 转 Excel 成功")
        except Exception as e:
            logger.error(f"Markdown 转 Excel 失败: {e}")
            raise
    
    def _convert_caj_file(self, input_path: str, output_path: str, export_format: str) -> None:
        """
        转换CAJ文件
        
        Args:
            input_path: CAJ文件路径
            output_path: 输出文件路径
            export_format: 目标格式
        """
        try:
            export_format = export_format.upper()
            
            # 首先检查文件类型（不使用上下文管理器）
            converter = CAJConverter()
            
            # 检查是否为伪装成CAJ的PDF文件
            if converter.is_pdf_disguised_as_caj(input_path):
                logger.info("检测到CAJ文件实际为PDF格式，直接处理")
                
                if export_format == 'PDF':
                    # 直接复制文件
                    import shutil
                    shutil.copy2(input_path, output_path)
                    logger.info(f"PDF文件复制成功: {output_path}")
                else:
                    # 使用Docling转换到其他格式
                    logger.info(f"将PDF文件转换为{export_format}")
                    self._convert_with_docling(input_path, output_path, export_format)
                
                return
            
            # 检查是否为真正的CAJ文件
            if not converter.is_caj_file(input_path):
                raise ValueError("不是有效的CAJ文件")
            
            # 处理真正的CAJ文件
            logger.info("检测到真正的CAJ文件，使用caj2pdf转换")
            
            if export_format != 'PDF':
                # 先转换为PDF，再转换为目标格式
                logger.info(f"CAJ文件需要先转换为PDF，再转换为{export_format}")
                
                # 创建临时PDF文件
                import tempfile
                temp_dir = tempfile.mkdtemp()
                
                try:
                    # 步骤1: CAJ -> PDF
                    logger.info("步骤1: 将CAJ文件转换为PDF")
                    with CAJConverter() as conv_ctx:
                        pdf_path = conv_ctx.convert_to_pdf(input_path, temp_dir)
                        
                        # 提取大纲（可选）
                        try:
                            conv_ctx.extract_outlines(input_path, pdf_path)
                            logger.info("成功提取CAJ文件大纲信息")
                        except Exception as e:
                            logger.warning(f"大纲提取失败，但不影响转换: {e}")
                    
                    # 步骤2: PDF -> 目标格式
                    if export_format in ['MARKDOWN', 'TEXT', 'DOCX', 'XLSX']:
                        logger.info(f"步骤2: 将PDF转换为{export_format}")
                        self._convert_with_docling(pdf_path, output_path, export_format)
                    else:
                        raise Exception(f"不支持将CAJ文件转换为{export_format}格式")
                        
                finally:
                    # 清理临时文件
                    import shutil
                    try:
                        shutil.rmtree(temp_dir)
                    except:
                        pass
            else:
                # 直接转换为PDF
                logger.info("直接将CAJ文件转换为PDF")
                output_dir = os.path.dirname(output_path)
                
                with CAJConverter() as conv_ctx:
                    pdf_path = conv_ctx.convert_to_pdf(input_path, output_dir)
                    
                    # 如果输出路径不同，移动文件
                    if pdf_path != output_path:
                        import shutil
                        shutil.move(pdf_path, output_path)
                    
                    # 提取大纲（可选）
                    try:
                        conv_ctx.extract_outlines(input_path, output_path)
                        logger.info("成功提取CAJ文件大纲信息")
                    except Exception as e:
                        logger.warning(f"大纲提取失败，但不影响转换: {e}")
            
            logger.info(f"CAJ文件转换成功: {input_path} -> {output_path}")
            
        except Exception as e:
            logger.error(f"CAJ文件转换失败: {e}")
            raise

# 全局转换器实例
document_converter = DocumentConverter()

def get_document_converter() -> DocumentConverter:
    """获取文档转换器实例"""
    return document_converter 