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

# 尝试导入pdf2docx
try:
    from pdf2docx import Converter as PDF2DOCXConverter
    PDF2DOCX_AVAILABLE = True
    logger.info("pdf2docx库可用，支持直接PDF转Word")
except ImportError:
    PDF2DOCX_AVAILABLE = False
    logger.warning("pdf2docx库不可用，PDF转Word将使用Markdown中转")

# 尝试导入docx2pdf
try:
    from docx2pdf import convert as docx2pdf_convert
    DOCX2PDF_AVAILABLE = True
    logger.info("docx2pdf库可用，支持微软Word直接转换")
except ImportError:
    DOCX2PDF_AVAILABLE = False
    logger.warning("docx2pdf库不可用，DOCX转PDF将使用pypandoc")

# 确保pandoc可用（conda安装，速度最快）
try:
    pypandoc.get_pandoc_version()
    logger.info("Pandoc已安装")
except OSError:
    logger.info("Pandoc未找到，正在使用conda安装...")
    try:
        import subprocess
        result = subprocess.run(['conda', 'install', '-c', 'conda-forge', 'pandoc', '-y'], 
                              capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            logger.info("Conda安装pandoc成功")
        else:
            logger.error(f"Conda安装失败: {result.stderr}")
    except Exception as e:
        logger.error(f"Conda安装pandoc失败: {e}")
except Exception as e:
    logger.warning(f"检查Pandoc版本失败: {e}")

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
        elif file_extension == 'pdf' and export_format == 'DOCX' and PDF2DOCX_AVAILABLE:
            # PDF直接转Word（保持格式）
            logger.debug("选择pdf2docx直接转换策略")
            self._convert_pdf_to_docx_direct(input_path, output_path)
        elif file_extension in ['docx', 'doc'] and export_format == 'PDF':
            # DOCX/DOC使用pandoc直接转PDF（需要LaTeX引擎）
            logger.debug("选择pandoc直接转换策略")
            self._convert_docx_to_pdf_with_pandoc(input_path, output_path)
        elif file_extension == 'md' and export_format in ['PDF', 'DOCX', 'XLSX']:
            # Markdown 本地转换
            logger.debug("选择本地Markdown转换策略")
            self._convert_markdown_local(input_path, output_path, export_format)
        elif self._should_use_docling(file_extension, export_format):
            # 使用 Docling 转换
            logger.debug("选择Docling转换策略")
            self._convert_with_docling(input_path, output_path, export_format)
        else:
            logger.debug("没有可用的转换策略")
            raise Exception(f"不支持的转换: {file_extension} -> {export_format}")
    
    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    def _should_use_docling(self, file_extension: str, export_format: str) -> bool:
        """判断是否应该使用 Docling 转换"""
        if not is_docling_available():
            return False
        
        # PDF转DOCX优先使用pdf2docx
        if file_extension == 'pdf' and export_format == 'DOCX' and PDF2DOCX_AVAILABLE:
            return False
        
        # DOCX/DOC转PDF优先使用pypandoc
        if file_extension in ['docx', 'doc'] and export_format == 'PDF':
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
        except OSError as e:
            if "No pandoc was found" in str(e):
                logger.error("Pandoc未安装，请运行: conda install -c conda-forge pandoc")
                raise Exception("Pandoc未安装")
            else:
                logger.error(f"Pandoc PDF 转换失败: {e}")
                raise
        except Exception as e:
            logger.error(f"Pandoc PDF 转换失败: {e}")
            raise
    
    def _markdown_to_docx(self, input_path: str, output_path: str) -> None:
        """Markdown 转 DOCX"""
        try:
            logger.info(f"Pandoc DOCX 转换: {input_path} -> {output_path}")
            pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
            logger.info("Pandoc DOCX 转换成功")
        except OSError as e:
            if "No pandoc was found" in str(e):
                logger.error("Pandoc未安装，请运行: conda install -c conda-forge pandoc")
                raise Exception("Pandoc未安装")
            else:
                logger.error(f"Pandoc DOCX 转换失败: {e}")
                raise
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
    
    def _convert_pdf_to_docx_direct(self, input_path: str, output_path: str) -> None:
        """直接PDF转DOCX（保持格式）"""
        try:
            logger.info(f"pdf2docx 直接转换: {input_path} -> {output_path}")
            
            # 直接转换
            cv = PDF2DOCXConverter(input_path)
            cv.convert(
                output_path, 
                start=0, 
                end=None,
                multi_processing=False,  # 禁用多进程避免兼容性问题
                cpu_count=1  # 使用单线程
            )
            cv.close()
            logger.info("✅ pdf2docx 直接转换成功")
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 友好的错误提示
            if "colorspace" in error_msg or "png" in error_msg:
                logger.warning(f"pdf2docx遇到图像兼容性问题: {e}")
                logger.info("📋 提示：此PDF可能包含特殊格式的图像，将使用OCR方案处理")
            elif "font" in error_msg:
                logger.warning(f"pdf2docx遇到字体问题: {e}")
            else:
                logger.error(f"pdf2docx转换失败: {e}")
            
            logger.info("🔄 自动回退到Docling + OCR方案...")
            
            # 回退到原来的方式
            try:
                self._convert_with_docling(input_path, output_path, "DOCX")
                logger.info("✅ 回退转换成功（可能格式略有差异）")
            except Exception as fallback_e:
                logger.error(f"❌ 回退转换也失败: {fallback_e}")
                raise Exception(f"PDF转Word失败: pdf2docx错误={e}, 回退错误={fallback_e}")
    
    def _convert_docx_to_pdf_with_pandoc(self, input_path: str, output_path: str) -> None:
        """使用pandoc直接转换DOCX为PDF（推荐方案）"""
        try:
            logger.info(f"pypandoc 转换: {input_path} -> {output_path}")
            
            # 自动检测可用的LaTeX引擎
            engines = ['xelatex', 'pdflatex', 'lualatex']
            available_engine = None
            
            for engine in engines:
                try:
                    import subprocess
                    result = subprocess.run([engine, '--version'], 
                                          capture_output=True, timeout=5)
                    if result.returncode == 0:
                        available_engine = engine
                        logger.info(f"✅ 检测到可用的LaTeX引擎: {engine}")
                        break
                except:
                    continue
            
            if not available_engine:
                logger.warning("⚠️ 未检测到LaTeX引擎，尝试默认转换")
                # 不指定引擎，让pandoc自己选择
                pypandoc.convert_file(input_path, 'pdf', outputfile=output_path)
            else:
                # 使用检测到的引擎，配置中文支持
                extra_args = [f'--pdf-engine={available_engine}']
                
                if available_engine == 'xelatex':
                    # XeLaTeX对中文支持最好
                    extra_args.extend([
                        '-V', 'mainfont=PingFang SC',  # macOS中文字体
                        '-V', 'CJKmainfont=PingFang SC'
                    ])
                elif available_engine == 'lualatex':
                    # LuaLaTeX也支持中文
                    extra_args.extend([
                        '-V', 'mainfont=PingFang SC'
                    ])
                
                logger.info(f"🔧 使用引擎: {available_engine}")
                pypandoc.convert_file(
                    input_path, 
                    'pdf', 
                    outputfile=output_path,
                    extra_args=extra_args
                )
            
            # 验证转换结果
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                logger.info("✅ pypandoc 转换成功")
            else:
                raise Exception("转换完成但输出文件无效")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            if "not found" in error_msg or "engine" in error_msg:
                logger.warning(f"LaTeX引擎问题: {e}")
                logger.info("🔄 回退到Docling + HTML方案...")
                
                # 回退到Docling方案
                try:
                    self._convert_with_docling(input_path, output_path, "PDF")
                    logger.info("✅ 回退转换成功")
                except Exception as fallback_e:
                    logger.error(f"❌ 回退转换也失败: {fallback_e}")
                    raise Exception(f"DOCX转PDF失败: pandoc错误={e}, Docling错误={fallback_e}")
            else:
                logger.error(f"pypandoc转换失败: {e}")
                raise Exception(f"DOCX转PDF失败: {e}")
    
    def _convert_docx_to_pdf_direct(self, input_path: str, output_path: str) -> None:
        """直接DOCX转PDF（保持格式）"""
        try:
            logger.info(f"pypandoc 直接转换: {input_path} -> {output_path}")
            
            # 使用pandoc直接转换DOCX到PDF，保持格式
            extra_args = [
                '--pdf-engine=xelatex',
                '-V', 'mainfont=SimSun',  # 支持中文
                '--from=docx',
                '--to=pdf'
            ]
            
            pypandoc.convert_file(
                input_path, 
                'pdf', 
                outputfile=output_path, 
                extra_args=extra_args
            )
            logger.info("✅ pypandoc DOCX转PDF成功")
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 友好的错误提示
            if "no pandoc was found" in error_msg:
                logger.error("Pandoc未安装，请运行: conda install -c conda-forge pandoc")
                raise Exception("Pandoc未安装")
            elif "xelatex" in error_msg:
                logger.warning(f"XeLaTeX引擎问题: {e}")
                logger.info("🔄 尝试使用默认PDF引擎...")
                
                # 回退到默认引擎
                try:
                    pypandoc.convert_file(input_path, 'pdf', outputfile=output_path)
                    logger.info("✅ 使用默认引擎转换成功")
                except Exception as fallback_e:
                    logger.error(f"❌ 默认引擎也失败: {fallback_e}")
                    raise Exception(f"DOCX转PDF失败: {fallback_e}")
            else:
                logger.error(f"pypandoc DOCX转PDF失败: {e}")
                logger.info("🔄 自动回退到Docling + OCR方案...")
                
                # 回退到Docling方案
                try:
                    self._convert_with_docling(input_path, output_path, "PDF")
                    logger.info("✅ 回退转换成功（可能格式略有差异）")
                except Exception as fallback_e:
                    logger.error(f"❌ 回退转换也失败: {fallback_e}")
                    raise Exception(f"DOCX转PDF失败: pypandoc错误={e}, 回退错误={fallback_e}")
    
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
                    # 对于其他格式，创建临时PDF文件并使用PDF转换逻辑
                    import tempfile
                    import shutil
                    
                    temp_dir = tempfile.mkdtemp()
                    try:
                        # 创建临时PDF文件（正确的扩展名）
                        temp_pdf_name = "temp_pdf_file.pdf"
                        temp_pdf_path = os.path.join(temp_dir, temp_pdf_name)
                        shutil.copy2(input_path, temp_pdf_path)
                        logger.info(f"创建临时PDF文件: {temp_pdf_path}")
                        
                        # 使用PDF转换逻辑处理
                        if export_format == 'DOCX' and PDF2DOCX_AVAILABLE:
                            logger.info("使用pdf2docx直接转换为DOCX")
                            self._convert_pdf_to_docx_direct(temp_pdf_path, output_path)
                        else:
                            logger.info(f"将PDF文件转换为{export_format}")
                            self._convert_with_docling(temp_pdf_path, output_path, export_format)
                            
                    finally:
                        # 清理临时文件
                        try:
                            shutil.rmtree(temp_dir)
                        except:
                            pass
                
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
                    if export_format == 'DOCX' and PDF2DOCX_AVAILABLE:
                        logger.info("步骤2: 使用pdf2docx直接转换为DOCX")
                        self._convert_pdf_to_docx_direct(pdf_path, output_path)
                    elif export_format in ['MARKDOWN', 'TEXT', 'DOCX', 'XLSX']:
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