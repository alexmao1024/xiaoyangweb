import os
import io
import logging
from flask import Flask, request, jsonify, send_file, render_template
import pypandoc
import requests
import pandas as pd
import re
from config import Config

# --- 日志配置 ---
log_file = 'app.log'

# 使用追加模式，避免因文件被占用而导致的启动错误
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
# --- 日志配置结束 ---

app = Flask(__name__)
app.config.from_object(Config)

# 确保上传和输出目录存在
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['OUTPUT_FOLDER']):
    os.makedirs(app.config['OUTPUT_FOLDER'])

@app.route('/')
def home():
    """渲染首页 - 小羊的工具箱"""
    return render_template('home.html')

@app.route('/convert-tool')
def convert_tool():
    """渲染文档转换工具页面"""
    return render_template('index.html')

@app.route('/check_server')
def check_server():
    """检查外部转换服务的状态"""
    try:
        # 使用根路径 '/' 进行健康检查
        response = requests.get(f"{app.config['SERVER_URL']}/", timeout=5)
        if response.ok:
            logging.info("外部API服务状态正常")
            return jsonify({'status': True})
        else:
            logging.warning(f"外部API服务状态异常，状态码: {response.status_code}")
            return jsonify({'status': False})
    except requests.exceptions.RequestException as e:
        logging.error(f"无法连接到外部API服务: {e}")
        return jsonify({'status': False})

@app.route('/convert', methods=['POST'])
def convert():
    """处理文件转换请求"""
    if 'file' not in request.files:
        logging.error("请求中没有文件部分")
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    export_format = request.form.get('export_format', 'MARKDOWN').upper()

    if file.filename == '':
        logging.error("没有选择文件")
        return jsonify({'error': 'No selected file'}), 400

    if not Config.allowed_file(file.filename):
        logging.error(f"文件类型不允许: {file.filename}")
        return jsonify({'error': 'File type not allowed'}), 400

    filename = file.filename
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    output_path = None

    try:
        file.save(input_path)
        logging.info(f"文件已保存到: {input_path}")

        file_extension = filename.rsplit('.', 1)[1].lower()
        output_filename_base = filename.rsplit('.', 1)[0]
        
        output_ext = export_format.lower()
        if output_ext == 'markdown': output_ext = 'md'
        output_filename = f"{output_filename_base}.{output_ext}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)

        if file_extension == 'md' and export_format in ['PDF', 'DOCX', 'XLSX']:
            logging.info(f"开始本地转换为 {export_format}...")
            if export_format == 'PDF':
                markdown_to_pdf(input_path, output_path)
            elif export_format == 'DOCX':
                markdown_to_docx(input_path, output_path)
            elif export_format == 'XLSX':
                markdown_to_excel(input_path, output_path)
        else:
            logging.info(f"使用外部API进行转换，目标格式: {export_format}")
            convert_with_api(input_path, output_path, export_format)
        
        logging.info(f"转换成功: {output_path}")

        # --- 新的文件处理和发送逻辑 ---
        # 1. 将输出文件读入内存
        with open(output_path, 'rb') as f:
            buffer = io.BytesIO(f.read())
        
        # 2. 立即从磁盘删除临时输出文件
        os.remove(output_path)
        logging.info(f"已将输出文件读入内存并删除磁盘文件: {output_path}")

        buffer.seek(0)
        
        # 3. 直接使用 send_file，它会自动处理好包含中文名的响应头
        mimetype = app.config['ALLOWED_EXTENSIONS'].get(output_ext, 'application/octet-stream')
        
        return send_file(
            buffer,
            mimetype=mimetype,
            as_attachment=True,
            download_name=output_filename
        )

    except Exception as e:
        logging.error(f"转换过程中发生严重错误: {e}", exc_info=True)
        if output_path and os.path.exists(output_path):
            os.remove(output_path) # 如果出错，也尝试清理
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500
    
    finally:
        # 只清理输入文件
        if input_path and os.path.exists(input_path):
            os.remove(input_path)
            logging.info(f"已清理输入文件: {input_path}")


def markdown_to_pdf(input_path, output_path):
    try:
        logging.info(f"Pandoc PDF 转换: 从 {input_path} 到 {output_path}")
        extra_args = ['--pdf-engine=xelatex', '-V', 'mainfont=SimSun']
        pypandoc.convert_file(input_path, 'pdf', outputfile=output_path, extra_args=extra_args)
        logging.info("Pandoc PDF 转换成功")
    except Exception as e:
        logging.error(f"Pandoc PDF 转换失败: {e}", exc_info=True)
        raise e

def markdown_to_docx(input_path, output_path):
    try:
        logging.info(f"Pandoc DOCX 转换: 从 {input_path} 到 {output_path}")
        pypandoc.convert_file(input_path, 'docx', outputfile=output_path)
        logging.info("Pandoc DOCX 转换成功")
    except Exception as e:
        logging.error(f"Pandoc DOCX 转换失败: {e}", exc_info=True)
        raise e

def markdown_to_excel(input_path, output_path):
    try:
        logging.info(f"Markdown 转 Excel: 从 {input_path} 到 {output_path}")
        
        # 读取Markdown文件
        with open(input_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 解析Markdown内容
        parsed_data = parse_markdown_to_structured_data(md_content)
        
        # 创建Excel文件
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
        
        logging.info("Markdown 转 Excel 成功")
    except Exception as e:
        logging.error(f"Markdown 转 Excel 失败: {e}", exc_info=True)
        raise e

def parse_markdown_to_structured_data(md_content):
    """解析Markdown内容，提取表格和结构化数据"""
    try:
        result = {
            'tables': [],
            'structure': []
        }
        
        lines = md_content.split('\n')
        
        # 1. 解析标准Markdown表格
        markdown_tables = extract_markdown_tables(md_content)
        result['tables'].extend(markdown_tables)
        
        # 2. 解析HTML风格的表格
        html_tables = extract_html_style_tables(md_content)
        result['tables'].extend(html_tables)
        
        # 3. 解析文档结构（标题、段落等）
        structure_data = extract_document_structure(lines)
        result['structure'] = structure_data
        
        return result
        
    except Exception as e:
        logging.error(f"解析Markdown内容失败: {e}")
        return {'tables': [], 'structure': []}

def extract_markdown_tables(md_content):
    """提取标准Markdown表格"""
    tables = []
    # 查找Markdown表格 - 更精确的模式
    table_pattern = r'\|(.+?)\|\s*\n\|[-:\s\|]+\|\s*\n((?:\|.+?\|\s*(?:\n|$))+)'
    matches = re.findall(table_pattern, md_content, re.MULTILINE | re.DOTALL)
    
    for header_row, data_rows in matches:
        # 解析表头 - 保留所有分割后的部分，包括空的
        header_parts = header_row.split('|')
        headers = []
        for part in header_parts:
            headers.append(part.strip())
        # 移除开头和结尾的空列（如果存在）
        while headers and not headers[0]:
            headers.pop(0)
        while headers and not headers[-1]:
            headers.pop()
        
        if not headers:
            continue
            
        # 解析数据行
        rows = []
        for row_line in data_rows.strip().split('\n'):
            if row_line.strip() and '|' in row_line:
                # 分割列，保留所有部分
                row_parts = row_line.split('|')
                cols = []
                for part in row_parts:
                    cols.append(part.strip())
                
                # 移除开头和结尾的空列
                while cols and not cols[0]:
                    cols.pop(0)
                while cols and not cols[-1]:
                    cols.pop()
                
                # 确保列数与表头匹配
                if len(cols) > len(headers):
                    cols = cols[:len(headers)]
                elif len(cols) < len(headers):
                    cols.extend([''] * (len(headers) - len(cols)))
                
                if cols:  # 只添加非空行
                    rows.append(cols)
        
        if rows:
            df = pd.DataFrame(rows, columns=headers)
            tables.append(df)
    
    return tables

def extract_html_style_tables(md_content):
    """提取HTML风格的表格（如验收报告中的表格）"""
    tables = []
    
    # 首先移除已经被标准Markdown表格识别的部分，避免重复解析
    # 找到所有标准Markdown表格的位置
    markdown_table_pattern = r'\|(.+?)\|\s*\n\|[-:\s\|]+\|\s*\n((?:\|.+?\|\s*(?:\n|$))+)'
    
    # 创建一个副本用于处理
    content_copy = md_content
    
    # 移除标准Markdown表格部分
    for match in re.finditer(markdown_table_pattern, md_content, re.MULTILINE | re.DOTALL):
        content_copy = content_copy.replace(match.group(0), '')
    
    # 在剩余内容中寻找其他表格模式
    # 模式1: 键值对表格（如验收报告）- 至少3列的表格
    kv_pattern = r'\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]*?)\s*\|'
    kv_matches = re.findall(kv_pattern, content_copy)
    
    if kv_matches:
        # 将键值对转换为表格
        processed_rows = []
        for match in kv_matches:
            # 过滤掉明显是表格分隔符的行
            if not any('---' in cell or '===' in cell or '___' in cell for cell in match):
                row = [cell.strip() for cell in match]
                # 过滤掉全空的行
                if any(cell for cell in row):
                    processed_rows.append(row)
        
        if processed_rows and len(processed_rows) > 1:  # 至少要有2行数据才算表格
            # 确定最大列数
            max_cols = max(len(row) for row in processed_rows)
            
            # 补齐所有行到相同列数
            for row in processed_rows:
                while len(row) < max_cols:
                    row.append('')
            
            # 使用第一行作为表头，如果看起来像表头的话
            if processed_rows:
                first_row = processed_rows[0]
                # 简单判断第一行是否像表头（通常比较短，包含关键词）
                if all(len(cell) < 50 for cell in first_row if cell):
                    headers = first_row
                    data_rows = processed_rows[1:]
                else:
                    headers = [f'列{i+1}' for i in range(max_cols)]
                    data_rows = processed_rows
                
                if data_rows:  # 确保有数据行
                    df = pd.DataFrame(data_rows, columns=headers)
                    tables.append(df)
    
    return tables

def extract_document_structure(lines):
    """提取文档结构"""
    structure = []
    current_section = ""
    content_buffer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 检测标题
        if line.startswith('**') and line.endswith('**'):
            # 保存上一节的内容
            if current_section and content_buffer:
                structure.append({
                    '章节': current_section,
                    '内容': '\n'.join(content_buffer)
                })
            
            # 开始新的章节
            current_section = line.strip('*').strip()
            content_buffer = []
        elif line.startswith('#'):
            # Markdown标题
            if current_section and content_buffer:
                structure.append({
                    '章节': current_section,
                    '内容': '\n'.join(content_buffer)
                })
            
            current_section = line.lstrip('#').strip()
            content_buffer = []
        else:
            # 普通内容
            if line and not line.startswith('|'):  # 排除表格行
                content_buffer.append(line)
    
    # 保存最后一节
    if current_section and content_buffer:
        structure.append({
            '章节': current_section,
            '内容': '\n'.join(content_buffer)
        })
    
    return structure

def convert_with_api(input_path, output_path, export_format):
    api_url = f"{app.config['SERVER_URL']}/convert"
    try:
        logging.info(f"准备调用外部API: {api_url}")
        with open(input_path, 'rb') as f:
            files = {'file': (os.path.basename(input_path), f)}
            data = {'export_format': export_format}
            response = requests.post(api_url, files=files, data=data, timeout=app.config['CONVERSION_TIMEOUT'])
        
        logging.info(f"API响应状态码: {response.status_code}")
        response.raise_for_status()

        with open(output_path, 'wb') as f:
            f.write(response.content)
        logging.info(f"API转换成功，文件已保存到 {output_path}")
    except requests.exceptions.RequestException as e:
        logging.error(f"调用外部API失败: {e}", exc_info=True)
        raise e
    except Exception as e:
        logging.error(f"处理API响应时发生未知错误: {e}", exc_info=True)
        raise e

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )