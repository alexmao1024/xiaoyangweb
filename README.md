# 🐑 小羊的工具箱 (Xiaoyang's Toolbox)

这是一个充满爱意的个人项目，旨在为我最亲爱的老婆打造一个专属的、实用的在线工具箱。这里集成了各种能让生活和工作变得更简单、更方便的小工具。

## ✨ 项目特色

- **为爱设计**: 采用温馨可爱的UI/UX设计，使用体验轻松愉快。
- **模块化架构**: 基于独立的工具卡片，未来可以方便地扩展和添加更多新功能。
- **本地优先**: 所有服务均可在本地运行，保证数据安全和私密性。
- **一键访问**: 通过内网穿透技术，让她可以随时随地访问家里的这个专属工具箱。

---

## 🚀 当前已上线工具

### 📄 **文档转换工具**

- **功能**: 支持 PDF、Word、Markdown、Excel 等多种常用文档格式的相互转换。
- **技术亮点**:
  - **本地转换**: `md -> pdf/docx/xlsx` 等转换通过 `pypandoc` 和 `pandas` 本地完成，速度快。
  - **OCR增强**: 集成 `Docling` 和 `RapidOCR`，支持对扫描件PDF等进行OCR识别和转换。

---

## 🏗️ 项目架构

本项目采用模块化架构，集成了所有转换功能：

```
+--------------------------------+
|                                |
|        用户 (浏览器)            |
|                                |
+--------------------------------+
             |
             | (HTTP请求)
             v
+--------------------------------+
|                                |
|      小羊的工具箱 (集成应用)      |
|     - Flask 前后端             |
|     - UI界面 & 文档转换         |
|     - 集成 Docling & OCR       |
|                                |
+--------------------------------+
|    运行在本地电脑 (支持MPS加速)   |
```

- **模块化设计**: 转换功能分模块实现，便于扩展新工具
- **集成架构**: 所有功能在一个应用中，无需额外服务

---

## 🛠️ 技术栈

- **后端**: `Python`, `Flask`
- **文档转换**: `pypandoc`, `Docling`, `RapidOCR`
- **数据处理**: `Pandas`, `Openpyxl`
- **机器学习**: `Hugging Face Hub`, `MPS加速 (Apple Silicon)`
- **前端**: `原生 HTML5/CSS3/JavaScript (ES6+)`

---

## 本地开发与部署指南

### 1. 环境准备

确保您的电脑支持Python 3.8+，推荐使用苹果电脑以获得MPS加速支持。

### 2. 安装依赖与启动

- **创建虚拟环境**:

  ```bash
  python -m venv .venv
  # Windows
  .\.venv\Scripts\activate
  # macOS/Linux
  source .venv/bin/activate
  ```
- **安装依赖**:

  ```bash
  pip install -r requirements.txt
  ```
- **启动应用**:

  ```bash
  python app.py
  ```

  现在，您可以在浏览器中访问 `http://localhost:5000` 查看"小羊的工具箱"首页。

### 3. 公网访问 (Ngrok 内网穿透)

为了让您老婆在外面也能使用，我们需要 `ngrok`。

- **在你运行 `xiaoyangweb` 的电脑上安装并配置 `ngrok`**。
- **启动穿透**:

  ```bash
  ngrok http 5000
  ```

---

## 🌟 未来的工具 (计划中)

- [ ]  CAJ转PDF
- [ ]  抢票软件
- [ ]  个人知识库和对话工作台

---

## 第三方库引用

本项目使用了以下第三方开源库：

### CAJ转PDF功能
- **[caj2pdf](https://github.com/caj2pdf/caj2pdf)**
  - 许可证：GLWTPL (Good Luck With That Public License)
  - 用途：将中国知网CAJ格式文献转换为PDF
  - 版本：基于主分支最新版本
  - 预编译库：[caj2pdf-extra-libs](https://github.com/caj2pdf/caj2pdf-extra-libs)

### 文档处理
- **[Docling](https://github.com/DS4SD/docling)**：智能文档解析和转换
- **[RapidOCR](https://github.com/RapidAI/RapidOCR)**：光学字符识别

感谢所有开源项目的贡献者！

---

<p align="center">
  <em>用 ❤️ 为我最爱的人制作</em>
</p>
