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
            :limit="1"
            v-model:file-list="fileList"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持格式：PDF、Word、Excel、Markdown、HTML、TXT 等
              </div>
            </template>
          </el-upload>
        </div>

        <!-- 转换设置 -->
        <div v-if="selectedFile" class="conversion-settings">
          <el-divider>转换设置</el-divider>
          
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="输入文件">
                <el-input :value="selectedFile.name" readonly>
                  <template #prepend>
                    <el-icon><Document /></el-icon>
                  </template>
                </el-input>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="目标格式">
                <el-select 
                  v-model="exportFormat" 
                  placeholder="请选择导出格式"
                  style="width: 100%"
                >
                  <el-option
                    v-for="format in availableFormats"
                    :key="format.value"
                    :label="format.label"
                    :value="format.value"
                  >
                    <div class="format-option">
                      <el-icon>
                        <component :is="format.icon" />
                      </el-icon>
                      <span>[[ format.label ]]</span>
                      <el-tag v-if="format.recommended" size="small" type="success">推荐</el-tag>
                    </div>
                  </el-option>
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
        <div v-if="selectedFile" class="convert-actions">
          <el-button 
            type="primary" 
            size="large"
            :loading="converting"
            :disabled="!exportFormat"
            @click="handleConvert"
            class="convert-button"
          >
            <el-icon v-if="!converting"><Magic /></el-icon>
            [[ converting ? '转换中...' : '开始转换' ]]
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

        <!-- 转换进度 -->
        <div v-if="converting" class="progress-section">
          <el-progress 
            :percentage="progress" 
            :stroke-width="8"
            :show-text="true"
            striped
            striped-flow
            class="progress-bar"
          />
                     <p class="progress-text">[[ progressText ]]</p>
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
      if (!this.selectedFile) return [];
      
      const fileExt = this.getFileExtension(this.selectedFile.name);
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
      
      const info = {
        'MARKDOWN': {
          title: 'Markdown 格式',
          description: '适合文档编辑和版本控制，支持表格、链接等丰富格式'
        },
        'PDF': {
          title: 'PDF 格式', 
          description: '便于分享和打印，保持格式不变'
        },
        'DOCX': {
          title: 'Word 文档',
          description: '适合进一步编辑和协作'
        },
        'XLSX': {
          title: 'Excel 表格',
          description: '将表格数据导出为可编辑的电子表格'
        },
        'TEXT': {
          title: '纯文本',
          description: '去除所有格式，保留纯文本内容'
        }
      };
      
      return info[this.exportFormat] || null;
    }
  },

  mounted() {
    this.checkServerStatus();
  },

  methods: {
    // 服务状态检查
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
    },

    // 文件处理
    handleFileChange(file) {
      this.selectedFile = file.raw || file;
      this.exportFormat = '';
      console.log('File selected:', this.selectedFile);
    },

    handleRemoveFile() {
      this.selectedFile = null;
      this.exportFormat = '';
      this.fileList = [];
    },

    handleReset() {
      this.handleRemoveFile();
      this.progress = 0;
      this.progressText = '';
    },

    // 格式处理
    getFileExtension(filename) {
      return filename.split('.').pop().toLowerCase();
    },

    getAvailableFormats(fileExt) {
      const formatMappings = {
        'pdf': ['markdown', 'text'],
        'docx': ['markdown', 'text'], 
        'doc': ['markdown', 'text'],
        'txt': ['markdown', 'text'],
        'html': ['markdown', 'text'],
        'md': ['markdown', 'text', 'pdf', 'docx', 'xlsx'],
        'xlsx': ['markdown', 'text'],
        'xls': ['markdown', 'text']
      };
      
      return formatMappings[fileExt] || ['markdown', 'text'];
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

    // 转换处理
    async handleConvert() {
      if (!this.selectedFile || !this.exportFormat) {
        this.$message.warning('请选择文件和目标格式');
        return;
      }

      this.converting = true;
      this.progress = 0;
      this.progressText = '准备上传文件...';

      try {
        // 启动流畅的进度动画
        this.startSmoothProgress();
        
        const formData = new FormData();
        formData.append('file', this.selectedFile);
        formData.append('export_format', this.exportFormat);

        const response = await fetch('/convert', {
          method: 'POST',
          body: formData
        });

        // 转换完成，快速推进到90%
        this.updateProgress(90, '转换完成，准备下载...');

        if (response.ok) {
          const contentType = response.headers.get('content-type');
          
          if (contentType && !contentType.includes('application/json')) {
            // 成功转换，下载文件
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            
            // 构建下载文件名
            const originalName = this.selectedFile.name.split('.').slice(0, -1).join('.');
            let extension = this.exportFormat.toLowerCase();
            if (extension === 'markdown') extension = 'md';
            const downloadName = `${originalName}.${extension}`;
            
            // 创建下载链接
            const a = document.createElement('a');
            a.href = url;
            a.download = downloadName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.updateProgress(100, '下载完成！');
            
            // 添加到历史记录
            this.addToHistory(this.selectedFile.name, this.exportFormat, true);
            
            this.$message.success('转换成功！');
            
            // 3秒后重置
            setTimeout(() => {
              this.handleReset();
              this.converting = false;
            }, 2000);
            
          } else {
            // 服务器返回错误
            const errorData = await response.json();
            throw new Error(errorData.error || '转换失败');
          }
        } else {
          throw new Error(`服务器错误：${response.status}`);
        }

      } catch (error) {
        console.error('转换失败:', error);
        this.addToHistory(this.selectedFile.name, this.exportFormat, false, error.message);
        this.$message.error(`转换失败: ${error.message}`);
        this.converting = false;
        this.progress = 0;
        this.progressText = '';
      }
    },

    updateProgress(percentage, text) {
      this.progress = percentage;
      this.progressText = text;
    },

    // 启动流畅的进度动画
    startSmoothProgress() {
      let currentProgress = 0;
      const stages = [
        { progress: 15, text: '正在上传文件...', duration: 800 },
        { progress: 35, text: '文件上传完成', duration: 500 },
        { progress: 50, text: '服务器分析中...', duration: 1000 },
        { progress: 75, text: '正在转换格式...', duration: 1500 },
        { progress: 85, text: '转换处理中...', duration: 2000 }
      ];

      let stageIndex = 0;
      
      const animateProgress = () => {
        if (stageIndex >= stages.length || !this.converting) {
          return;
        }
        
        const stage = stages[stageIndex];
        const increment = (stage.progress - currentProgress) / 20; // 分20步完成
        
        const stepAnimation = () => {
          if (currentProgress < stage.progress && this.converting) {
            currentProgress += increment;
            this.progress = Math.min(currentProgress, stage.progress);
            this.progressText = stage.text;
            
            setTimeout(stepAnimation, stage.duration / 20);
          } else {
            // 当前阶段完成，进入下一阶段
            stageIndex++;
            currentProgress = stage.progress;
            setTimeout(animateProgress, 200); // 短暂停顿后进入下一阶段
          }
        };
        
        stepAnimation();
      };
      
      // 立即开始第一阶段
      this.updateProgress(5, '准备上传文件...');
      setTimeout(animateProgress, 300);
    },

    addToHistory(fileName, targetFormat, success, error = null) {
      const historyItem = {
        fileName,
        targetFormat,
        success,
        error,
        timestamp: new Date().toLocaleString()
      };
      
      this.conversionHistory.unshift(historyItem);
      
      // 保持最新的5条记录
      if (this.conversionHistory.length > 5) {
        this.conversionHistory = this.conversionHistory.slice(0, 5);
      }
    }
  }
};

// 注册全局组件
window.DocumentConverter = DocumentConverter; 