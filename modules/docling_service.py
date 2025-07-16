"""
Docling 文档处理模块
集成 OCR 和高级文档转换功能
"""

import os
import logging
from pathlib import Path
from typing import Literal, Optional, Tuple

logger = logging.getLogger(__name__)

# 检查 Docling 是否可用
try:
    from docling.document_converter import DocumentConverter, WordFormatOption, PowerpointFormatOption, HTMLFormatOption, \
        MarkdownFormatOption, AsciiDocFormatOption, ExcelFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, OcrMacOptions, AcceleratorDevice, AcceleratorOptions
    from docling.document_converter import PdfFormatOption, ImageFormatOption
    DOCLING_AVAILABLE = True
    logger.info("Docling 模块导入成功")
except ImportError as e:
    DOCLING_AVAILABLE = False
    logger.warning(f"Docling 模块导入失败: {e}")

class DoclingProcessor:
    """Docling 文档处理器"""
    
    def __init__(self, models_dir: Optional[str] = None):
        """
        初始化 Docling 处理器
        
        Args:
            models_dir: 模型文件目录，如果为 None 则使用默认路径
        """
        self.models_dir = Path(models_dir) if models_dir else Path("./models/RapidOCR")
        self.converter = None
        self._setup_models()
        self._init_converter()
    
    def _setup_models(self):
        """设置 OCR 模型路径"""
        self.det_model_path = str(self.models_dir / "PP-OCRv4/en_PP-OCRv3_det_infer.onnx")
        self.rec_model_path = str(self.models_dir / "PP-OCRv4/ch_PP-OCRv4_rec_server_infer.onnx")
        self.cls_model_path = str(self.models_dir / "PP-OCRv3/ch_ppocr_mobile_v2.0_cls_train.onnx")

        # 检查模型文件是否存在
        if (os.path.exists(self.det_model_path) and
            os.path.exists(self.rec_model_path) and
            os.path.exists(self.cls_model_path)):
            logger.info("RapidOCR 模型文件已找到")
            self.models_available = True
        else:
            logger.warning("RapidOCR 模型文件未找到，OCR功能可能无法正常工作")
            self.models_available = False
    
    def _init_converter(self):
        """初始化文档转换器"""
        if not DOCLING_AVAILABLE:
            logger.error("Docling 不可用，无法初始化转换器")
            return
        
        try:
            # 配置加速器选项
            accelerator_options = AcceleratorOptions(
                num_threads=8, 
                device=AcceleratorDevice.MPS  # 苹果 M 系列芯片使用 MPS
            )
            
            # 配置 OCR 选项
            if self.models_available:
                ocr_options = RapidOcrOptions(
                    det_model_path=self.det_model_path,
                    rec_model_path=self.rec_model_path,
                    cls_model_path=self.cls_model_path,
                )
            else:
                ocr_options = OcrMacOptions()
                ocr_options.lang = ['en-US', 'zh-Hans']
            
            # 配置管道选项
            pipeline_options = PdfPipelineOptions(ocr_options=ocr_options)
            pipeline_options.accelerator_options = accelerator_options
            
            # 初始化转换器
            self.converter = DocumentConverter()
            
            # 设置支持的格式
            self.converter.allowed_formats = [
                InputFormat.PDF,
                InputFormat.IMAGE,
                InputFormat.DOCX,
                InputFormat.XLSX,
                InputFormat.PPTX,
                InputFormat.HTML,
                InputFormat.ASCIIDOC,
                InputFormat.CSV,
                InputFormat.MD,
            ]
            
            # 设置格式选项
            self.converter.format_to_options = {
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
                InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
                InputFormat.DOCX: WordFormatOption(),
                InputFormat.PPTX: PowerpointFormatOption(),
                InputFormat.HTML: HTMLFormatOption(),
                InputFormat.MD: MarkdownFormatOption(),
                InputFormat.ASCIIDOC: AsciiDocFormatOption(),
                InputFormat.CSV: ExcelFormatOption(),
                InputFormat.XLSX: ExcelFormatOption(),
            }
            
            logger.info("Docling 转换器初始化成功")
            
        except Exception as e:
            logger.error(f"初始化 Docling 转换器失败: {e}")
            self.converter = None
    
    def is_available(self) -> bool:
        """检查 Docling 是否可用"""
        return DOCLING_AVAILABLE and self.converter is not None
    
    def convert_document(self, file_path: str, export_format: Literal["MARKDOWN", "TEXT"] = "MARKDOWN") -> Tuple[str, str]:
        """
        转换文档
        
        Args:
            file_path: 输入文件路径
            export_format: 导出格式 (MARKDOWN 或 TEXT)
            
        Returns:
            Tuple[content, file_extension]: 转换后的内容和文件扩展名
            
        Raises:
            Exception: 转换失败时抛出异常
        """
        if not self.is_available():
            raise Exception("Docling 转换器不可用")
        
        try:
            logger.info(f"开始转换文档: {file_path}")
            
            # 执行转换
            result = self.converter.convert(source=str(file_path))
            
            if result.status.name == "SUCCESS" or result.status.name == "PARTIAL_SUCCESS":
                doc = result.document
                
                # 根据格式导出内容
                if export_format.upper() == "MARKDOWN":
                    content = doc.export_to_markdown()
                    file_extension = "md"
                else:
                    content = doc.export_to_text()
                    file_extension = "txt"
                
                logger.info(f"文档转换成功: {file_path}")
                return content, file_extension
            else:
                error_msg = f"转换失败: {result.status.name}"
                if result.errors:
                    error_msg += f", 错误: {result.errors}"
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"转换文档时发生错误: {e}")
            raise

# 全局实例
docling_processor = DoclingProcessor()

def get_docling_processor() -> DoclingProcessor:
    """获取 Docling 处理器实例"""
    return docling_processor

def is_docling_available() -> bool:
    """检查 Docling 是否可用"""
    return docling_processor.is_available() 