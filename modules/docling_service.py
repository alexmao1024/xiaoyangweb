"""
Docling 文档处理模块
集成 OCR 和高级文档转换功能
"""

import os
import logging
from pathlib import Path
from typing import Literal, Optional, Tuple

# 完全禁用HuggingFace的网络连接检查
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'

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
        logger.info("🚀 开始初始化DoclingProcessor...")
        
        self.models_dir = Path(models_dir) if models_dir else Path("./models/RapidOCR")
        logger.info(f"模型目录设置为: {self.models_dir}")
        
        self.converter = None
        
        logger.info("开始设置模型...")
        self._setup_models()
        
        logger.info("开始初始化转换器...")
        self._init_converter()
        
        if self.is_available():
            logger.info("🎉 DoclingProcessor初始化完成!")
        else:
            logger.error("❌ DoclingProcessor初始化失败!")
    
    def _setup_models(self):
        """设置 OCR 模型路径"""
        self.det_model_path = str(self.models_dir / "PP-OCRv4/ch_PP-OCRv4_det_server_infer.onnx")
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
        logger.info("开始初始化Docling转换器...")
        
        if not DOCLING_AVAILABLE:
            logger.error("Docling 不可用，无法初始化转换器")
            logger.error("请检查docling库是否正确安装")
            return
        
        logger.info("Docling库可用，继续初始化...")
        
        try:
            # 配置加速器选项
            logger.debug("配置加速器选项...")
            accelerator_options = AcceleratorOptions(
                num_threads=8, 
                device=AcceleratorDevice.MPS  # 苹果 M 系列芯片使用 MPS
            )
            logger.info(f"加速器配置完成: MPS设备, 8线程")
            
            # 配置 OCR 选项
            logger.debug("配置OCR选项...")
            if self.models_available:
                logger.info("使用本地RapidOCR模型")
                logger.debug(f"检测模型: {self.det_model_path}")
                logger.debug(f"识别模型: {self.rec_model_path}")
                logger.debug(f"分类模型: {self.cls_model_path}")
                
                ocr_options = RapidOcrOptions(
                    det_model_path=self.det_model_path,
                    rec_model_path=self.rec_model_path,
                    cls_model_path=self.cls_model_path,
                )
                logger.info("RapidOCR选项配置完成")
            else:
                logger.warning("本地RapidOCR模型不可用，使用macOS OCR")
                ocr_options = OcrMacOptions()
                ocr_options.lang = ['en-US', 'zh-Hans']
                logger.info("macOS OCR选项配置完成")
            
            # 配置管道选项
            logger.debug("配置PDF管道选项...")
            pipeline_options = PdfPipelineOptions(ocr_options=ocr_options)
            pipeline_options.accelerator_options = accelerator_options
            logger.info("PDF管道选项配置完成")
            
            # 初始化转换器（强制使用本地文件）
            logger.debug("初始化DocumentConverter...")
            self.converter = DocumentConverter()
            logger.info("DocumentConverter创建成功")
            
            # 设置支持的格式
            logger.debug("设置支持的文件格式...")
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
            logger.debug(f"支持的格式: {len(self.converter.allowed_formats)}种")
            
            # 设置格式选项
            logger.debug("设置格式选项...")
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
            logger.info("格式选项配置完成")
            
            logger.info("✅ Docling 转换器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 初始化 Docling 转换器失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            logger.error(f"错误详情: {str(e)}")
            import traceback
            logger.error(f"完整堆栈:\n{traceback.format_exc()}")
            self.converter = None
    
    def is_available(self) -> bool:
        """检查 Docling 是否可用"""
        available = DOCLING_AVAILABLE and self.converter is not None
        logger.debug(f"Docling可用性检查: DOCLING_AVAILABLE={DOCLING_AVAILABLE}, converter存在={self.converter is not None}, 最终结果={available}")
        return available
    
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
        logger.info(f"准备转换文档: {file_path}, 目标格式: {export_format}")
        
        # 详细检查可用性
        if not DOCLING_AVAILABLE:
            logger.error("❌ Docling库不可用")
            raise Exception("Docling 库未正确安装或导入失败")
        
        if self.converter is None:
            logger.error("❌ Docling转换器为None，初始化可能失败")
            raise Exception("Docling 转换器初始化失败，请检查启动日志")
        
        logger.info("✅ Docling转换器可用，开始转换...")
        
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
docling_processor = None

def _create_docling_processor():
    """创建Docling处理器实例"""
    global docling_processor
    if docling_processor is None:
        try:
            logger.info("🚀 开始创建全局Docling处理器实例...")
            docling_processor = DoclingProcessor()
            logger.info("✅ 全局Docling处理器实例创建成功")
        except Exception as e:
            logger.error(f"❌ 创建全局Docling处理器实例失败: {e}")
            logger.error(f"错误类型: {type(e).__name__}")
            import traceback
            logger.error(f"完整堆栈:\n{traceback.format_exc()}")
            docling_processor = None
    return docling_processor

def get_docling_processor() -> DoclingProcessor:
    """获取 Docling 处理器实例"""
    return _create_docling_processor()

def is_docling_available() -> bool:
    """检查 Docling 是否可用"""
    processor = _create_docling_processor()
    available = DOCLING_AVAILABLE and processor is not None and processor.is_available()
    logger.debug(f"全局Docling可用性检查: DOCLING_AVAILABLE={DOCLING_AVAILABLE}, processor存在={processor is not None}, 最终结果={available}")
    return available 