# 文档转换 MCP 服务器

这个 MCP (Model Context Protocol) 服务器将您的文档转换功能包装成了可以被 AI 客户端调用的工具。

## 功能特性

- **文档格式转换**: 支持 PDF、Word、Markdown、文本等格式之间的转换
- **本地 Pandoc 转换**: Markdown 到 PDF/DOCX 的高质量转换
- **外部 API 集成**: 利用您现有的外部转换服务
- **服务状态检查**: 监控外部服务的可用性
- **格式兼容性查询**: 查看支持的文件格式组合

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置

确保您的 `config.py` 文件包含正确的配置：

```python
class Config:
    SERVER_URL = 'http://192.168.1.145:8002'  # 您的外部转换服务地址
    CONVERSION_TIMEOUT = 300  # 转换超时时间（秒）
    # ... 其他配置
```

## 运行 MCP 服务器

### 方法 1: 直接运行（用于测试）

```bash
python mcp_server.py
```

### 方法 2: 通过 MCP 客户端

将 MCP 服务器添加到您的 AI 客户端配置中。

#### 对于 Claude Desktop:

1. 找到 Claude Desktop 的配置文件:
   - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
   - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. 根据您的环境选择配置方案:

**方案 1: 直接使用虚拟环境的 Python（推荐）**
```json
{
  "mcpServers": {
    "document-converter": {
      "command": "D:/maoProject/xiaoyang/xiaoyangweb/.venv/Scripts/python.exe",
      "args": ["mcp_server.py"],
      "cwd": "D:/maoProject/xiaoyang/xiaoyangweb",
      "env": {}
    }
  }
}
```

**方案 2: 使用批处理脚本**
```json
{
  "mcpServers": {
    "document-converter": {
      "command": "D:/maoProject/xiaoyang/xiaoyangweb/start_mcp.bat",
      "args": [],
      "cwd": "D:/maoProject/xiaoyang/xiaoyangweb",
      "env": {}
    }
  }
}
```

**方案 3: 使用环境变量**
```json
{
  "mcpServers": {
    "document-converter": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "D:/maoProject/xiaoyang/xiaoyangweb",
      "env": {
        "PATH": "D:/maoProject/xiaoyang/xiaoyangweb/.venv/Scripts;%PATH%",
        "PYTHONPATH": "D:/maoProject/xiaoyang/xiaoyangweb/.venv/Lib/site-packages"
      }
    }
  }
}
```

**注意**: 将路径替换为您项目的实际路径。推荐使用方案 1，最简单可靠。

#### 对于其他 MCP 客户端:

使用提供的 `mcp_config.json` 文件，并根据您的客户端要求进行调整。

## 可用工具

### 1. convert_document

转换文档格式。

**参数:**
- `input_file_path` (必需): 输入文件的完整路径
- `output_format` (必需): 目标格式 (MARKDOWN, TEXT, PDF, DOCX)
- `output_file_path` (可选): 输出文件路径，不提供则自动生成

**示例:**
```
转换文件 D:/documents/report.pdf 为 Markdown 格式
```

### 2. check_conversion_service

检查外部转换服务的状态。

**示例:**
```
检查文档转换服务是否正常运行
```

### 3. get_supported_formats

查看支持的文件格式和转换组合。

**参数:**
- `input_format` (可选): 特定输入格式，查看其支持的输出格式

**示例:**
```
查看所有支持的文档格式
查看 PDF 格式支持哪些输出格式
```

## 支持的格式转换

| 输入格式 | 支持的输出格式 |
|---------|---------------|
| PDF     | MARKDOWN, TEXT |
| DOCX    | MARKDOWN, TEXT |
| DOC     | MARKDOWN, TEXT |
| TXT     | MARKDOWN, TEXT |
| HTML    | MARKDOWN, TEXT |
| MD      | MARKDOWN, TEXT, PDF, DOCX |

## 使用示例

在支持 MCP 的 AI 客户端中，您可以这样使用：

1. **转换文档**:
   ```
   请帮我将 D:/reports/年度总结.pdf 转换为 Markdown 格式
   ```

2. **检查服务状态**:
   ```
   检查一下文档转换服务是否正常
   ```

3. **查询支持格式**:
   ```
   Markdown 文件可以转换成什么格式？
   ```

## 故障排除

### 常见问题

1. **MiKTeX 警告**: 如果看到 MiKTeX 更新提醒，这是正常的，不会影响功能。

2. **Pandoc 未找到**: 确保已安装 Pandoc 和 MiKTeX（用于 PDF 转换）。

3. **外部服务连接失败**: 检查 `config.py` 中的 `SERVER_URL` 是否正确。

4. **权限错误**: 确保 Python 进程有权限读写指定的文件路径。

### 日志

MCP 服务器会输出详细的日志信息，帮助您诊断问题。

## 技术细节

- **协议**: Model Context Protocol (MCP)
- **通信方式**: stdio
- **异步处理**: 基于 asyncio
- **错误处理**: 完整的异常捕获和用户友好的错误消息

## 扩展

您可以轻松扩展这个 MCP 服务器：

1. 添加新的文档格式支持
2. 集成更多转换服务
3. 添加批量转换功能
4. 实现转换进度回调

修改 `mcp_server.py` 中的相应函数即可。 