"""
CAJ转PDF转换模块
使用caj2pdf库进行中国知网CAJ格式文件转换
"""
import os
import sys
import tempfile
import shutil
import subprocess
from pathlib import Path
import logging

# 添加caj2pdf到Python路径
current_dir = Path(__file__).parent.parent
caj2pdf_path = current_dir / "thirdlib" / "caj2pdf"
sys.path.insert(0, str(caj2pdf_path))

logger = logging.getLogger(__name__)

class CAJConverter:
    """CAJ转PDF转换器"""
    
    def __init__(self):
        self.caj2pdf_dir = caj2pdf_path
        self.original_cwd = None
        
    def __enter__(self):
        """进入上下文管理器，切换到caj2pdf目录"""
        self.original_cwd = os.getcwd()
        os.chdir(self.caj2pdf_dir)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，恢复原始目录"""
        if self.original_cwd:
            os.chdir(self.original_cwd)
    
    def is_caj_file(self, file_path):
        """
        检查文件是否为CAJ格式
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否为CAJ文件
        """
        if not os.path.exists(file_path):
            return False
            
        # 检查文件扩展名
        if not file_path.lower().endswith('.caj'):
            return False
            
        # 检查文件头部特征
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)  # 读取更多字节进行判断
                
                # 检查是否是PDF文件（很多CAJ文件实际是PDF）
                if header.startswith(b'%PDF'):
                    logger.info(f"检测到CAJ文件实际为PDF格式: {file_path}")
                    return False  # 不是真正的CAJ文件，是PDF文件
                
                # CAJ文件的常见头部标识
                if header.startswith(b'CAJ') or header.startswith(b'HN') or header[0:1] == b'\xc8':
                    return True
                    
        except Exception as e:
            logger.warning(f"检查CAJ文件头部时出错: {e}")

        return False
    
    def is_pdf_disguised_as_caj(self, file_path):
        """
        检查扩展名为.caj的文件是否实际是PDF
        
        Args:
            file_path (str): 文件路径
            
        Returns:
            bool: 是否为伪装成CAJ的PDF文件
        """
        if not os.path.exists(file_path):
            return False
            
        if not file_path.lower().endswith('.caj'):
            return False
            
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                return header.startswith(b'%PDF')
        except Exception as e:
            logger.warning(f"检查PDF头部时出错: {e}")
            return False
    
    def get_caj_info(self, caj_file_path):
        """
        获取CAJ文件信息
        
        Args:
            caj_file_path (str): CAJ文件路径
            
        Returns:
            dict: 文件信息
        """
        if not self.is_caj_file(caj_file_path):
            raise ValueError("不是有效的CAJ文件")
            
        try:
            # 导入cajparser
            import cajparser
            
            # 解析CAJ文件
            parser = cajparser.CAJParser(caj_file_path)
            
            info = {
                'format': getattr(parser, 'format', 'unknown'),
                'page_count': getattr(parser, 'page_num', 0),
                'toc_count': getattr(parser, 'toc_num', 0),
                'file_size': os.path.getsize(caj_file_path),
                'file_name': os.path.basename(caj_file_path)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"获取CAJ文件信息失败: {e}")
            raise Exception(f"解析CAJ文件失败: {e}")
    
    def convert_to_pdf(self, caj_file_path, output_dir=None):
        """
        将CAJ文件转换为PDF
        
        Args:
            caj_file_path (str): CAJ文件路径
            output_dir (str): 输出目录，如果为None则使用临时目录
            
        Returns:
            str: 生成的PDF文件路径
        """
        # 检查是否为真正的CAJ文件或伪装的PDF文件
        if not self.is_caj_file(caj_file_path) and not self.is_pdf_disguised_as_caj(caj_file_path):
            raise ValueError("不是有效的CAJ文件或PDF文件")
        
        # 如果是伪装成CAJ的PDF文件，直接复制
        if self.is_pdf_disguised_as_caj(caj_file_path):
            logger.info(f"文件实际为PDF格式，直接复制: {caj_file_path}")
            
            # 准备输出路径
            if output_dir is None:
                output_dir = tempfile.mkdtemp()
                
            input_filename = os.path.basename(caj_file_path)
            output_filename = os.path.splitext(input_filename)[0] + '.pdf'
            output_path = os.path.join(output_dir, output_filename)
            
            # 直接复制文件
            import shutil
            shutil.copy2(caj_file_path, output_path)
            logger.info(f"PDF文件复制成功: {output_path}")
            return output_path
            
        # 准备输出路径
        if output_dir is None:
            output_dir = tempfile.mkdtemp()
            
        input_filename = os.path.basename(caj_file_path)
        output_filename = os.path.splitext(input_filename)[0] + '.pdf'
        output_path = os.path.join(output_dir, output_filename)
        
        try:
            logger.info(f"开始转换CAJ文件: {caj_file_path}")
            logger.info(f"输出路径: {output_path}")
            
            # 使用caj2pdf命令行工具进行转换
            cmd = [
                sys.executable, 
                'caj2pdf', 
                'convert', 
                caj_file_path,
                '-o', output_path
            ]
            
            # 执行转换命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=self.caj2pdf_dir
            )
            
            if result.returncode == 0:
                if os.path.exists(output_path):
                    logger.info(f"CAJ转PDF成功: {output_path}")
                    return output_path
                else:
                    raise Exception("转换完成但找不到输出文件")
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                if "Unknown file type" in error_msg:
                    raise Exception("不支持的CAJ文件类型，请检查文件格式")
                elif "No such file" in error_msg:
                    raise Exception("输入文件不存在或路径错误")
                else:
                    raise Exception(f"转换失败: {error_msg}")
                    
        except subprocess.TimeoutExpired:
            raise Exception("转换超时，文件可能过大或格式复杂")
        except Exception as e:
            logger.error(f"CAJ转PDF失败: {e}")
            # 清理可能的部分文件
            if os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
            raise
    
    def extract_outlines(self, caj_file_path, pdf_file_path):
        """
        从CAJ文件提取大纲并添加到PDF文件
        
        Args:
            caj_file_path (str): CAJ文件路径
            pdf_file_path (str): PDF文件路径
            
        Returns:
            str: 处理后的PDF文件路径
        """
        if not self.is_caj_file(caj_file_path):
            raise ValueError("不是有效的CAJ文件")
            
        if not os.path.exists(pdf_file_path):
            raise ValueError("PDF文件不存在")
            
        try:
            logger.info(f"提取CAJ大纲到PDF: {caj_file_path} -> {pdf_file_path}")
            
            # 使用caj2pdf命令行工具提取大纲
            cmd = [
                sys.executable,
                'caj2pdf',
                'outlines',
                caj_file_path,
                '-o', pdf_file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1分钟超时
                cwd=self.caj2pdf_dir
            )
            
            if result.returncode == 0:
                logger.info("大纲提取成功")
                return pdf_file_path
            else:
                error_msg = result.stderr.strip() or result.stdout.strip()
                logger.warning(f"大纲提取失败: {error_msg}")
                # 大纲提取失败不影响主要转换功能
                return pdf_file_path
                
        except Exception as e:
            logger.warning(f"大纲提取失败: {e}")
            # 大纲提取失败不影响主要转换功能
            return pdf_file_path


def convert_caj_to_pdf(caj_file_path, output_dir=None):
    """
    便捷函数：将CAJ文件转换为PDF
    
    Args:
        caj_file_path (str): CAJ文件路径
        output_dir (str): 输出目录
        
    Returns:
        str: 生成的PDF文件路径
    """
    with CAJConverter() as converter:
        return converter.convert_to_pdf(caj_file_path, output_dir)


def get_caj_file_info(caj_file_path):
    """
    便捷函数：获取CAJ文件信息
    
    Args:
        caj_file_path (str): CAJ文件路径
        
    Returns:
        dict: 文件信息
    """
    with CAJConverter() as converter:
        return converter.get_caj_info(caj_file_path) 