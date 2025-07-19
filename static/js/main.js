// 小羊的工具箱 - Vue 3 主应用
const { createApp } = Vue;
const { ElMessage } = ElementPlus;

// 创建Vue应用
const app = createApp({
  delimiters: ['[[', ']]'],  // 使用自定义分隔符避免与Jinja2冲突
  data() {
    return {
      activeMenu: 'home',
      serverStatus: {
        type: 'info',
        text: '检查中...'
      },
      isMobile: false,
      sidebarCollapsed: true // 移动端默认收起
    }
  },

  mounted() {
    this.checkServerStatus();
    // 定期检查服务状态
    setInterval(this.checkServerStatus, 30000); // 每30秒检查一次
    
    // 检测移动端
    this.detectMobile();
    window.addEventListener('resize', this.detectMobile);
  },

  methods: {
    handleMenuSelect(index) {
      console.log('Menu selected:', index);
      this.activeMenu = index;
    },

    async checkServerStatus() {
      try {
        const response = await fetch('/check_server', {
          method: 'GET',
          cache: 'no-cache'
        });
        
        const data = await response.json();
        
        if (data.status) {
          this.serverStatus = {
            type: 'success',
            text: '运行正常'
          };
        } else {
          this.serverStatus = {
            type: 'warning', 
            text: '部分功能异常'
          };
        }
      } catch (error) {
        console.error('检查服务状态失败:', error);
        this.serverStatus = {
          type: 'danger',
          text: '连接失败'
        };
      }
    },

    // 全局消息提示方法
    showMessage(message, type = 'info') {
      ElMessage({
        message,
        type,
        duration: 3000,
        showClose: true
      });
    },

    // 检测移动端
    detectMobile() {
      this.isMobile = window.innerWidth <= 768;
    },

    // 切换侧边栏
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed;
    },

    // 返回主页
    goHome() {
      this.activeMenu = 'home';
      this.showMessage('欢迎回到首页！', 'success');
    }
  },

  // 全局提供方法
  provide() {
    return {
      showMessage: this.showMessage
    }
  }
});

// 注册Element Plus
app.use(ElementPlus);

// 注册Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

// 注册自定义组件
app.component('DocumentConverter', DocumentConverter);

// 全局属性
app.config.globalProperties.$message = ElMessage;

// 挂载应用
app.mount('#app');

// 标记样式已加载
document.body.classList.add('styles-loaded');

// 全局错误处理
app.config.errorHandler = (err, vm, info) => {
  console.error('Vue应用错误:', err, info);
  ElMessage.error('应用发生错误，请刷新页面重试');
};

// 添加一些有用的全局方法
window.app = app;
window.showMessage = (message, type = 'info') => {
  ElMessage({
    message,
    type,
    duration: 3000,
    showClose: true
  });
};

console.log('🐑 小羊的工具箱已启动！'); 