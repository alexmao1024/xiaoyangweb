# 文档转换工具

这是一个简单的文档转换工具前端界面，用于将各种文档格式转换为Markdown或纯文本格式。

## 功能特点

- 支持多种文件格式：PDF、Word、Excel、PowerPoint、HTML等
- 简单直观的用户界面
- 实时转换状态显示
- 支持转换结果预览和下载
- 自动检测服务器状态

## 安装说明

1. 确保已安装Conda环境

2. 创建新的虚拟环境并激活：
```bash
conda create -n doc_converter python=3.9
conda activate doc_converter
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 激活虚拟环境：
```bash
conda activate doc_converter
```

2. 启动应用：
```bash
streamlit run app.py
```

3. 在浏览器中访问应用（默认地址：http://localhost:8501）

## 注意事项

- 确保转换服务器（192.168.1.145:8000）正常运行
- 大文件转换可能需要较长时间，请耐心等待
- 如遇到转换失败，请检查文件格式是否支持 