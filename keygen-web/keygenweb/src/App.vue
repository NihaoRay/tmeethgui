<template>
  <div class="container">
    <div class="card">
      <h2>获取专属激活码</h2>

      <div class="form-group">
        <label>请输入您的机器码</label>
        <input
            v-model="userInput"
            type="text"
            placeholder="例如：user_123"
        />
      </div>

      <button
          @click="requestActivationCode"
          :disabled="isLoading || !userInput"
          class="submit-btn"
      >
        <span v-if="isLoading">正在向 Python 请求...</span>
        <span v-else>生成激活码</span>
      </button>

      <!-- 结果展示区 -->
      <div v-if="resultCode" class="result-box">
        <p>生成成功！您的激活码是：</p>
        <div class="code-display">
          <span class="code">{{ resultCode }}</span>
          <button @click="copyCode" class="copy-btn">复制</button>
        </div>
      </div>

      <!-- 错误提示区 -->
      <div v-if="errorMessage" class="error-box">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// 定义响应式变量
const userInput = ref('')
const resultCode = ref('')
const isLoading = ref(false)
const errorMessage = ref('')

// 请求 Python 后端的函数
const requestActivationCode = async () => {
  isLoading.value = true
  errorMessage.value = ''
  resultCode.value = ''

  try {
    // 确保你的 Python FastAPI 后端运行在 8000 端口
    const response = await fetch('/api/generate_code', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_input: userInput.value })
    })

    if (!response.ok) throw new Error('网络请求失败')

    const resData = await response.json()
    resultCode.value = resData.data.activation_code

  } catch (error) {
    console.error("请求失败:", error)
    errorMessage.value = '请求失败，请检查 Python 后端是否已启动 (127.0.0.1:8000)'
  } finally {
    isLoading.value = false
  }
}

// 复制功能
// 复制功能（兼容局域网 HTTP 环境）
const copyCode = async () => {
  const textToCopy = resultCode.value;

  // 1. 优先尝试现代 Clipboard API (仅在 localhost 或 HTTPS 下有效)
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(textToCopy);
      alert('激活码已复制到剪贴板！');
      return; // 成功后直接返回
    } catch (err) {
      console.error('现代复制 API 失败:', err);
    }
  }

  // 2. 降级方案：使用传统的 textarea 方式 (支持 HTTP 局域网 IP 访问)
  try {
    // 创建一个隐藏的文本域
    const textArea = document.createElement("textarea");
    textArea.value = textToCopy;

    // 将其移出屏幕可视区域，避免页面闪烁
    textArea.style.position = "fixed";
    textArea.style.left = "-999999px";
    textArea.style.top = "-999999px";
    document.body.appendChild(textArea);

    // 选中文本
    textArea.focus();
    textArea.select();

    // 执行复制命令
    const successful = document.execCommand('copy');
    if (successful) {
      alert('激活码已复制到剪贴板！');
    } else {
      alert('复制失败，请长按手动复制');
    }

    // 清理 DOM
    textArea.remove();
  } catch (err) {
    console.error('传统复制方法失败:', err);
    alert('复制失败，请长按手动复制');
  }
}
</script>

<style scoped>
/* 基础样式，确保页面美观 */
.container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f9fafb;
  font-family: sans-serif;
}
.card {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}
h2 {
  text-align: center;
  color: #1f2937;
  margin-bottom: 1.5rem;
}
.form-group {
  margin-bottom: 1rem;
}
label {
  display: block;
  font-size: 0.875rem;
  color: #4b5563;
  margin-bottom: 0.5rem;
}
input {
  width: 100%;
  padding: 0.5rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  box-sizing: border-box;
  outline: none;
}
input:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2);
}
.submit-btn {
  width: 100%;
  background-color: #2563eb;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  margin-top: 0.5rem;
}
.submit-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
}
.result-box {
  margin-top: 1.5rem;
  padding: 1rem;
  background-color: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
}
.result-box p {
  margin: 0 0 0.5rem 0;
  color: #166534;
  font-size: 0.875rem;
}
.code-display {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 0.5rem;
  border: 1px solid #86efac;
  border-radius: 4px;
}
.code {
  font-family: monospace;
  font-weight: bold;
  font-size: 1.125rem;
}
.copy-btn {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
}
.error-box {
  margin-top: 1rem;
  padding: 0.75rem;
  background-color: #fff7ed;
  color: #c2410c;
  border: 1px solid #fed7aa;
  border-radius: 6px;
  font-size: 0.875rem;
}
</style>