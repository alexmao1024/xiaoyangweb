"""
Markdown 处理模块
处理 Markdown 文档的解析和结构化
"""

import re
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def parse_markdown_to_structured_data(md_content: str) -> dict:
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
        logger.error(f"解析Markdown内容失败: {e}")
        return {'tables': [], 'structure': []}

def extract_markdown_tables(md_content: str) -> list:
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

def extract_html_style_tables(md_content: str) -> list:
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

def extract_document_structure(lines: list) -> list:
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