// API服务模块 - 处理前后端通信
class ApiService {
  constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  // 通用请求方法
  async request(url, options = {}) {
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
      },
      cache: 'no-cache'
    };

    // 合并选项
    const finalOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers
      }
    };

    try {
      const response = await fetch(this.baseUrl + url, finalOptions);
      
      // 如果是文件下载，直接返回response
      if (options.expectFile) {
        return response;
      }

      // 检查内容类型
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || `HTTP ${response.status}`);
        }
        return data;
      } else {
        // 非JSON响应
        if (!response.ok) {
          const text = await response.text();
          throw new Error(`HTTP ${response.status}: ${text}`);
        }
        return response;
      }
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  // GET请求
  async get(url, params = {}) {
    const urlParams = new URLSearchParams(params);
    const fullUrl = urlParams.toString() ? `${url}?${urlParams}` : url;
    
    return this.request(fullUrl, {
      method: 'GET'
    });
  }

  // POST请求
  async post(url, data = {}) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // 文件上传
  async uploadFile(url, formData, onProgress = null) {
    const options = {
      method: 'POST',
      body: formData,
      expectFile: true
    };

    // 移除Content-Type头，让浏览器自动设置
    delete options.headers;

    // 如果提供了进度回调，创建XMLHttpRequest
    if (onProgress) {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            const percentComplete = (event.loaded / event.total) * 100;
            onProgress(percentComplete);
          }
        };

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve(xhr.response);
          } else {
            reject(new Error(`HTTP ${xhr.status}`));
          }
        };

        xhr.onerror = () => reject(new Error('网络错误'));
        
        xhr.open('POST', this.baseUrl + url);
        xhr.responseType = 'blob';
        xhr.send(formData);
      });
    }

    return this.request(url, options);
  }

  // 检查服务器状态
  async checkServerStatus() {
    try {
      const data = await this.get('/check_server');
      return {
        success: true,
        status: data.status,
        doclingAvailable: data.docling_available,
        message: data.status ? '服务正常' : '服务异常'
      };
    } catch (error) {
      return {
        success: false,
        status: false,
        doclingAvailable: false,
        message: error.message || '连接失败'
      };
    }
  }

  // 文档转换
  async convertDocument(file, exportFormat, onProgress = null) {
    if (!file || !exportFormat) {
      throw new Error('缺少必要参数：文件或导出格式');
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('export_format', exportFormat.toUpperCase());

    try {
      const response = await this.uploadFile('/convert', formData, onProgress);
      
      if (response instanceof Response) {
        // 检查响应类型
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
          // 错误响应
          const errorData = await response.json();
          throw new Error(errorData.error || '转换失败');
        } else {
          // 成功响应，返回文件blob
          const blob = await response.blob();
          return {
            success: true,
            blob: blob,
            filename: this.generateFilename(file.name, exportFormat)
          };
        }
      } else {
        // XMLHttpRequest响应
        return {
          success: true,
          blob: response,
          filename: this.generateFilename(file.name, exportFormat)
        };
      }
    } catch (error) {
      console.error('文档转换失败:', error);
      throw error;
    }
  }

  // 生成输出文件名
  generateFilename(originalName, exportFormat) {
    const baseName = originalName.split('.').slice(0, -1).join('.');
    let extension = exportFormat.toLowerCase();
    
    if (extension === 'markdown') {
      extension = 'md';
    }
    
    return `${baseName}.${extension}`;
  }

  // 下载文件
  downloadBlob(blob, filename) {
    try {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = filename;
      
      document.body.appendChild(a);
      a.click();
      
      // 清理
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      return true;
    } catch (error) {
      console.error('下载文件失败:', error);
      return false;
    }
  }

  // 获取支持的文件格式
  getSupportedFormats() {
    return {
      input: [
        { ext: 'pdf', label: 'PDF文档', icon: 'Document' },
        { ext: 'docx', label: 'Word文档', icon: 'Document' },
        { ext: 'doc', label: 'Word文档(旧版)', icon: 'Document' },
        { ext: 'xlsx', label: 'Excel表格', icon: 'Grid' },
        { ext: 'xls', label: 'Excel表格(旧版)', icon: 'Grid' },
        { ext: 'md', label: 'Markdown', icon: 'Document' },
        { ext: 'html', label: 'HTML网页', icon: 'Document' },
        { ext: 'txt', label: '纯文本', icon: 'DocumentCopy' }
      ],
      output: [
        { value: 'MARKDOWN', label: 'Markdown', icon: 'Document' },
        { value: 'TEXT', label: '纯文本', icon: 'DocumentCopy' },
        { value: 'PDF', label: 'PDF', icon: 'Document' },
        { value: 'DOCX', label: 'Word文档', icon: 'Document' },
        { value: 'XLSX', label: 'Excel表格', icon: 'Grid' }
      ]
    };
  }

  // 验证文件格式
  validateFile(file) {
    if (!file) {
      return { valid: false, message: '请选择文件' };
    }

    const maxSize = 16 * 1024 * 1024; // 16MB
    if (file.size > maxSize) {
      return { valid: false, message: '文件大小不能超过16MB' };
    }

    const supportedExts = this.getSupportedFormats().input.map(f => f.ext);
    const fileExt = file.name.split('.').pop().toLowerCase();
    
    if (!supportedExts.includes(fileExt)) {
      return { valid: false, message: '不支持的文件格式' };
    }

    return { valid: true, message: '文件验证通过' };
  }
}

// 创建全局API服务实例
window.apiService = new ApiService();

// 导出模块
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ApiService;
} 