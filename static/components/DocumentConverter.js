// 文档转换器Vue组件
const DocumentConverter = {
  delimiters: ['[[', ']]'],  // 使用自定义分隔符避免与Jinja2冲突
  template: `
    <div class="document-converter">
      <el-card class="converter-card">
        <template #header>
          <div class="card-header">
            <h2>
              <el-icon><Document /></el-icon>
              文档转换工具
            </h2>
            <p>支持多种文档格式的智能转换</p>
          </div>
        </template>

        <!-- 服务状态显示 -->
        <el-alert
          v-if="serverStatus.show"
          :title="serverStatus.title"
          :type="serverStatus.type"
          :description="serverStatus.description"
          show-icon
          :closable="false"
          class="status-alert"
        />

        <!-- 文件上传区域 -->
        <div class="upload-section">
          <el-upload
            ref="uploadRef"
            class="upload-dragger"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :before-remove="handleRemoveFile"
            :accept="acceptedTypes"
            :limit="10"
            multiple
            v-model:file-list="fileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em><br>
              <small>支持批量上传，最多10个文件</small>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：PDF、Word、Excel、Markdown、HTML、TXT 等
              </div>
            </template>
          </el-upload>
        </div>

        <!-- 转换设置 -->
        <div v-if="fileList.length > 0" class="conversion-settings">
          <el-row :gutter="20">
            <el-col :span="24">
              <el-form-item label="目标格式">
                <el-select
                  v-model="exportFormat"
                  placeholder="选择转换后的格式"
                  size="large"
                  style="width: 100%"
                >
                  <el-option-group label="推荐格式">
                    <el-option
                      v-for="format in availableFormats.filter(f => f.recommended)"
                      :key="format.value"
                      :label="format.label"
                      :value="format.value"
                    >
                      <div class="format-option">
                        <el-icon><component :is="format.icon" /></el-icon>
                        <span>[[ format.label ]]</span>
                        <el-tag size="small" type="success">推荐</el-tag>
                      </div>
                    </el-option>
                  </el-option-group>
                  <el-option-group label="其他格式">
                    <el-option
                      v-for="format in availableFormats.filter(f => !f.recommended)"
                      :key="format.value"
                      :label="format.label"
                      :value="format.value"
                    >
                      <div class="format-option">
                        <el-icon><component :is="format.icon" /></el-icon>
                        <span>[[ format.label ]]</span>
                      </div>
                    </el-option>
                  </el-option-group>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 格式说明 -->
          <el-alert
            v-if="formatInfo"
            :title="formatInfo.title"
            :description="formatInfo.description"
            type="info"
            show-icon
            :closable="false"
            class="format-info"
          />
        </div>

        <!-- 转换按钮 -->
        <div v-if="fileList.length > 0" class="convert-actions">
          <el-button 
            type="primary" 
            size="large"
            :loading="converting"
            :disabled="!exportFormat"
            @click="handleBatchConvert"
            class="convert-button"
          >
            <el-icon v-if="!converting"><Magic /></el-icon>
            [[ converting ? '批量转换中...' : '开始转换 (' + fileList.length + '个文件)' ]]
          </el-button>
          
          <el-button 
            size="large"
            @click="handleReset"
            class="reset-button"
          >
            <el-icon><Refresh /></el-icon>
            重新选择
          </el-button>
        </div>

        <!-- 批量转换进度 -->
        <div v-if="converting" class="progress-section">
          <div class="batch-progress-header">
            <span class="progress-title">批量转换进度</span>
            <span class="progress-count">[[ completedFiles ]] / [[ totalFiles ]] 个文件</span>
          </div>
          <el-progress 
            :percentage="overallProgress" 
            :stroke-width="8"
            :show-text="true"
            striped
            striped-flow
            class="progress-bar"
          />
          <p class="progress-text">[[ progressText ]]</p>
          
          <!-- 当前处理文件 -->
          <div v-if="currentProcessingFile" class="current-file">
            <el-icon><Document /></el-icon>
            <span>正在处理：[[ currentProcessingFile ]]</span>
          </div>
        </div>
      </el-card>

      <!-- 转换历史 -->
      <el-card v-if="conversionHistory.length > 0" class="history-card">
        <template #header>
          <div class="card-header">
            <h3>
              <el-icon><Clock /></el-icon>
              最近转换记录
            </h3>
          </div>
        </template>
        
        <el-timeline>
          <el-timeline-item
            v-for="(item, index) in conversionHistory"
            :key="index"
            :timestamp="item.timestamp"
            :type="item.success ? 'success' : 'danger'"
          >
            <div class="history-item">
              <div class="history-main">
                <strong>[[ item.fileName ]]</strong>
                <el-icon><Right /></el-icon>
                <strong>[[ item.targetFormat ]]</strong>
              </div>
              <div class="history-status">
                <el-tag :type="item.success ? 'success' : 'danger'" size="small">
                  [[ item.success ? '转换成功' : '转换失败' ]]
                </el-tag>
                <span v-if="item.error" class="error-text">[[ item.error ]]</span>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </el-card>
    </div>
  `,
  
  data() {
    return {
      fileList: [],
      selectedFile: null,
      exportFormat: '',
      converting: false,
      progress: 0,
      progressText: '',
      // 批量转换相关
      overallProgress: 0,
      completedFiles: 0,
      totalFiles: 0,
      currentProcessingFile: '',
      conversionHistory: [],
      serverStatus: {
        show: false,
        type: 'info',
        title: '',
        description: ''
      }
    }
  },

  computed: {
    acceptedTypes() {
      return '.pdf,.docx,.doc,.txt,.md,.html,.xlsx,.xls';
    },

    availableFormats() {
      if (this.fileList.length === 0) return [];
      
      // 如果有多个文件，返回通用格式
      if (this.fileList.length > 1) {
        const formats = ['markdown', 'text', 'pdf', 'docx', 'xlsx'];
        return formats.map(format => ({
          value: format.toUpperCase(),
          label: this.getFormatLabel(format),
          icon: this.getFormatIcon(format),
          recommended: false
        }));
      }
      
      // 单文件时保持原有逻辑
      const fileExt = this.getFileExtension(this.fileList[0].name);
      const formats = this.getAvailableFormats(fileExt);
      
      return formats.map(format => ({
        value: format.toUpperCase(),
        label: this.getFormatLabel(format),
        icon: this.getFormatIcon(format),
        recommended: this.isRecommendedFormat(fileExt, format)
      }));
    },

    formatInfo() {
      if (!this.exportFormat) return null;
      
      const infos = {
        'MARKDOWN': {
          title: 'Markdown 格式',
          description: '通用文档标记语言，适合文档编写和版本控制'
        },
        'TEXT': {
          title: '纯文本格式',
          description: '去除所有格式，保留纯文本内容'
        },
        'PDF': {
          title: 'PDF 格式',
          description: '便携文档格式，适合打印和分享'
        },
        'DOCX': {
          title: 'Word 文档',
          description: 'Microsoft Word 格式，支持丰富的文档编辑'
        },
        'XLSX': {
          title: 'Excel 表格',
          description: 'Microsoft Excel 格式，适合数据和表格处理'
        }
      };
      
      return infos[this.exportFormat] || null;
    }
  },

  mounted() {
    this.checkServerStatus();
  },

  methods: {
    // 文件处理
    handleFileChange(file, fileList) {
      this.fileList = fileList;
      if (fileList.length === 1) {
        this.selectedFile = file.raw || file;
      }
    },

    handleRemoveFile(file, fileList) {
      this.fileList = fileList;
      if (fileList.length === 0) {
        this.selectedFile = null;
        this.exportFormat = '';
      }
    },

    // 工具函数
    getFileExtension(filename) {
      return filename.split('.').pop().toLowerCase();
    },

    getAvailableFormats(fileExtension) {
      const formatMap = {
        'pdf': ['markdown', 'text'],
        'docx': ['markdown', 'text', 'pdf'],
        'doc': ['markdown', 'text', 'pdf'],
        'txt': ['markdown', 'pdf', 'docx'],
        'md': ['pdf', 'docx', 'xlsx', 'text'],
        'html': ['markdown', 'text', 'pdf', 'docx'],
        'xlsx': ['markdown', 'text'],
        'xls': ['markdown', 'text']
      };
      
      return formatMap[fileExtension] || ['markdown', 'text', 'pdf'];
    },

    getFormatLabel(format) {
      const labels = {
        'markdown': 'Markdown',
        'text': '纯文本',
        'pdf': 'PDF',
        'docx': 'Word 文档',
        'xlsx': 'Excel 表格'
      };
      return labels[format] || format;
    },

    getFormatIcon(format) {
      const icons = {
        'markdown': 'Document',
        'text': 'DocumentCopy',
        'pdf': 'Document',
        'docx': 'Document',
        'xlsx': 'Grid'
      };
      return icons[format] || 'Document';
    },

    isRecommendedFormat(fileExt, targetFormat) {
      // 推荐格式逻辑
      if (fileExt === 'md' && targetFormat === 'pdf') return true;
      if (['pdf', 'docx'].includes(fileExt) && targetFormat === 'markdown') return true;
      return false;
    },

    // 批量转换处理
    async handleBatchConvert() {
      if (this.fileList.length === 0 || !this.exportFormat) {
        this.$message.warning('请选择文件和目标格式');
        return;
      }

      this.converting = true;
      this.overallProgress = 0;
      this.completedFiles = 0;
      this.totalFiles = this.fileList.length;
      this.progressText = '准备转换 ' + this.totalFiles + ' 个文件...';

      const successFiles = [];
      const failedFiles = [];

      try {
        for (let i = 0; i < this.fileList.length; i++) {
          const file = this.fileList[i];
          this.currentProcessingFile = file.name;
          this.progressText = '正在转换第 ' + (i + 1) + ' 个文件：' + file.name;

          try {
            const formData = new FormData();
            formData.append('file', file.raw || file);
            formData.append('export_format', this.exportFormat);

            const response = await fetch('/convert', {
              method: 'POST',
              body: formData
            });

            if (response.ok) {
              const contentType = response.headers.get('content-type');
              
              if (contentType && !contentType.includes('application/json')) {
                // 成功转换，下载文件
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                // 构建下载文件名
                const originalName = file.name.split('.').slice(0, -1).join('.');
                let extension = this.exportFormat.toLowerCase();
                if (extension === 'markdown') extension = 'md';
                const downloadName = originalName + '.' + extension;
                
                // 创建下载链接
                const a = document.createElement('a');
                a.href = url;
                a.download = downloadName;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);

                successFiles.push(file.name);
                this.addToHistory(file.name, this.exportFormat, true);
                
              } else {
                // 服务器返回错误
                const errorData = await response.json();
                throw new Error(errorData.error || '转换失败');
              }
            } else {
              throw new Error('服务器错误：' + response.status);
            }

          } catch (error) {
            console.error('转换失败:', error);
            failedFiles.push({name: file.name, error: error.message});
            this.addToHistory(file.name, this.exportFormat, false, error.message);
          }

          // 更新整体进度
          this.completedFiles = i + 1;
          this.overallProgress = Math.round((this.completedFiles / this.totalFiles) * 100);
        }

        // 转换完成
        this.currentProcessingFile = '';
        if (failedFiles.length === 0) {
          this.progressText = '全部转换完成！共 ' + successFiles.length + ' 个文件';
          this.$message.success('批量转换完成！');
        } else if (successFiles.length === 0) {
          this.progressText = '转换失败，请检查文件格式';
          this.$message.error('批量转换失败！');
        } else {
          this.progressText = '部分转换完成：成功 ' + successFiles.length + ' 个，失败 ' + failedFiles.length + ' 个';
          this.$message.warning('部分文件转换失败，请检查文件格式');
        }
        
        // 3秒后重置
        setTimeout(() => {
          this.handleReset();
          this.converting = false;
        }, 3000);

      } catch (error) {
        console.error('批量转换失败:', error);
        this.$message.error('批量转换失败: ' + error.message);
        this.converting = false;
        this.overallProgress = 0;
        this.progressText = '';
      }
    },

    // 重置
    handleReset() {
      this.fileList = [];
      this.selectedFile = null;
      this.exportFormat = '';
      this.converting = false;
      this.overallProgress = 0;
      this.completedFiles = 0;
      this.totalFiles = 0;
      this.currentProcessingFile = '';
      this.progressText = '';
      this.$refs.uploadRef?.clearFiles();
    },

    // 历史记录
    addToHistory(fileName, targetFormat, success, error = null) {
      const historyItem = {
        fileName,
        targetFormat: this.getFormatLabel(targetFormat.toLowerCase()),
        success,
        error,
        timestamp: new Date().toLocaleString()
      };
      
      this.conversionHistory.unshift(historyItem);
      
      // 只保留最近10条记录
      if (this.conversionHistory.length > 10) {
        this.conversionHistory = this.conversionHistory.slice(0, 10);
      }
    },

    // 服务器状态检查
    async checkServerStatus() {
      try {
        const response = await fetch('/check_server');
        const data = await response.json();

        if (data.status) {
          this.serverStatus = {
            show: true,
            type: 'success',
            title: '服务状态正常',
            description: '所有转换功能可正常使用'
          };
        } else {
          this.serverStatus = {
            show: true,
            type: 'error',
            title: '服务连接失败',
            description: '部分转换功能可能不可用，请稍后重试'
          };
        }
      } catch (error) {
        this.serverStatus = {
          show: true,
          type: 'error',
          title: '服务检查失败',
          description: '无法检查服务状态，请检查网络连接'
        };
      }
    }
  }
};

// 注册全局组件
window.DocumentConverter = DocumentConverter; 