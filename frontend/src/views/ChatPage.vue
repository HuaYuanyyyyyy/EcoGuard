<template>
  <div class="chat-page">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div class="header-left">
        <h2>💬 合规问答</h2>
        <p>输入污染物数据，AI 自动检索标准文档并判断合规性</p>
      </div>
    </div>

    <!-- 消息区域 -->
    <div class="message-area" ref="messageArea">
      <!-- 欢迎消息 -->
      <div class="welcome-msg" v-if="messages.length === 0">
        <div class="welcome-icon">🌿</div>
        <h3>你好，我是 EcoGuard 助手</h3>
        <p>请输入污染物数据，我将根据已上传的标准文档判断是否合规</p>
        <div class="example-box">
          <p class="example-title">输入示例：</p>
          <p class="example-content">
            灰尘 2.0mg/m3<br />
            二氧化硫 3.2mg/m3<br />
            二氧化氮 4.2mg/m3
          </p>
          <el-button size="small" text type="primary" @click="fillExample">
            点击使用示例
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div v-for="(msg, index) in messages" :key="index" class="message-wrapper">

        <!-- 用户消息 -->
        <div v-if="msg.role === 'user'" class="message user-message">
          <div class="msg-content">{{ msg.content }}</div>
          <div class="msg-avatar">👤</div>
        </div>

        <!-- AI消息 - 普通对话 -->
        <div v-else-if="msg.type === 'chat'" class="message ai-message">
          <div class="msg-avatar">🛡️</div>
          <div class="msg-content">{{ msg.content }}</div>
        </div>

        <!-- AI消息 - MHTML 加载中 -->
        <div v-else-if="msg.type === 'mhtml-loading'" class="message ai-message">
          <div class="msg-avatar">🛡️</div>
          <div class="mhtml-loading-box">
            <div class="mhtml-step" :class="{ active: msg.step >= 1, done: msg.step > 1 }">
              <span class="step-icon">{{ msg.step > 1 ? '✓' : '⟳' }}</span>
              <span>上传文件</span>
            </div>
            <div class="mhtml-step" :class="{ active: msg.step >= 2, done: msg.step > 2 }">
              <span class="step-icon">{{ msg.step > 2 ? '✓' : msg.step === 2 ? '⟳' : '○' }}</span>
              <span>解析污染物数据</span>
            </div>
            <div class="mhtml-step" :class="{ active: msg.step >= 3 }">
              <span class="step-icon">{{ msg.step === 3 ? '⟳' : '○' }}</span>
              <span>检索标准库并判断合规性</span>
            </div>
            <p class="mhtml-hint">{{ msg.statusText }}</p>
          </div>
        </div>

        <!-- AI消息 - 错误 -->
        <div v-else-if="msg.type === 'error'" class="message ai-message">
          <div class="msg-avatar">🛡️</div>
          <div class="error-box">
            <span class="error-icon">⚠️</span>
            <span>{{ msg.content }}</span>
          </div>
        </div>

        <div v-else-if="msg.type === 'compliance'" class="message ai-message compliance-msg">
          <div class="msg-avatar">🛡️</div>
          <div class="compliance-content">

            <!-- 结果表格 -->
            <div class="result-table-wrapper">
              <el-table :data="msg.results" border style="width: 100%">
                <el-table-column prop="name" label="污染物" width="120" />
                <el-table-column prop="measured_value" label="实测值" width="120" />
                <el-table-column prop="standard_value" label="标准值" width="120" />
                <el-table-column prop="source_file" label="文件依据" min-width="160">
                  <template #default="{ row }">
                    <span class="source-file">{{ row.source_files?.[0] || row.source_file }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="是否合规" width="100">
                  <template #default="{ row }">
                    <el-tag
                      v-if="row.is_compliant === true"
                      type="success"
                      size="small"
                    >✅ 合规</el-tag>
                    <el-tag
                      v-else-if="row.is_compliant === false"
                      type="danger"
                      size="small"
                    >❌ 超标</el-tag>
                    <el-tag
                      v-else
                      type="info"
                      size="small"
                    >⚠️ 未知</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="reason" label="判断依据" min-width="200" />
              </el-table>
            </div>

            <!-- 自然语言总结 -->
            <div class="summary-box">
              <span class="summary-icon">📊</span>
              <p>{{ msg.summary }}</p>
            </div>

          </div>
        </div>

      </div>

      <!-- 加载中 -->
      <div v-if="loading" class="message ai-message">
        <div class="msg-avatar">🛡️</div>
        <div class="msg-content loading-dots">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="输入污染物数据，每行一条，格式：污染物名称 实测值&#10;例：二氧化硫 3.2mg/m3"
        resize="none"
        @keydown.ctrl.enter="sendMessage"
      />
      <div class="input-footer">
        <div class="input-left">
          <input
            ref="mhtmlInput"
            type="file"
            accept=".mhtml"
            style="display: none"
            @change="uploadMhtml"
          />
          <el-button
            size="small"
            :loading="mhtmlLoading"
            :disabled="loading"
            @click="$refs.mhtmlInput.click()"
          >
            📎 上传 MHTML
          </el-button>
          <span class="input-tip">Ctrl + Enter 发送</span>
        </div>
        <el-button
          type="primary"
          @click="sendMessage"
          :loading="loading"
          :disabled="!inputText.trim()"
        >
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { chatApi } from '../api/index'

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const mhtmlLoading = ref(false)
const messageArea = ref(null)
const mhtmlInput = ref(null)

const fillExample = () => {
  inputText.value = '灰尘 2.0mg/m3\n二氧化硫 3.2mg/m3\n二氧化氮 4.2mg/m3'
}

const scrollToBottom = async () => {
  await nextTick()
  if (messageArea.value) {
    messageArea.value.scrollTop = messageArea.value.scrollHeight
  }
}

const uploadMhtml = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  event.target.value = ''

  mhtmlLoading.value = true

  messages.value.push({ role: 'user', content: `📎 ${file.name}` })
  // 加载中占位消息
  messages.value.push({
    role: 'ai',
    type: 'mhtml-loading',
    step: 1,
    statusText: '正在上传文件...'
  })
  const msgIndex = messages.value.length - 1
  await scrollToBottom()

  const setStep = (step, text) => {
    if (messages.value[msgIndex]?.type === 'mhtml-loading') {
      messages.value[msgIndex].step = step
      messages.value[msgIndex].statusText = text
    }
  }

  const showError = (text) => {
    messages.value[msgIndex] = { role: 'ai', type: 'error', content: text }
    mhtmlLoading.value = false
  }

  try {
    const formData = new FormData()
    formData.append('file', file)

    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await fetch(`${baseURL}/chat/check-mhtml`, {
      method: 'POST',
      body: formData,
    })

    // HTTP 层报错（400/500 等），读取 JSON 错误信息
    if (!response.ok) {
      let errMsg = `请求失败（${response.status}）`
      try {
        const errJson = await response.json()
        errMsg = errJson.detail || errJson.content || errMsg
      } catch {}
      showError(errMsg)
      return
    }

    setStep(2, '正在解析文件中的污染物数据...')
    await scrollToBottom()

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let gotFirstResult = false

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      for (const line of chunk.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))

          if (data.type === 'error') {
            showError(data.content)
            return
          }

          if (data.type === 'result_item') {
            if (!gotFirstResult) {
              gotFirstResult = true
              setStep(3, '正在逐项检测合规性...')
              // 切换为合规结果消息
              messages.value[msgIndex] = { role: 'ai', type: 'compliance', results: [], summary: '' }
            }
            messages.value[msgIndex].results.push(data.item)
          } else if (data.type === 'summary_chunk') {
            messages.value[msgIndex].summary += data.content
          } else if (data.type === 'done') {
            mhtmlLoading.value = false
          }
          await scrollToBottom()
        } catch {}
      }
    }

    // 若流结束但一条结果都没有（文件内容无法提取）
    if (!gotFirstResult) {
      showError('未从文件中提取到有效的污染物数据，请确认文件格式')
    }
  } catch (err) {
    showError('网络错误，请检查后端服务是否启动：' + (err.message || ''))
  } finally {
    mhtmlLoading.value = false
    await scrollToBottom()
  }
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  // 先占位
  messages.value.push({ role: 'ai', type: 'pending', content: '' })
  const msgIndex = messages.value.length - 1

  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    const response = await fetch(`${baseURL}/chat/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'result_item') {
              // 第一条结果来了，初始化消息
            if (messages.value[msgIndex].type === 'pending') {
               messages.value[msgIndex] = {
               role: 'ai',
               type: 'compliance',
               results: [],
               summary: ''
              }
            }
  // 每来一条追加一行
          messages.value[msgIndex].results.push(data.item)
          }
          else if (data.type === 'summary_chunk') {
            // 总结流式追加
            messages.value[msgIndex].summary += data.content
          } else if (data.type === 'chat_chunk') {
            // 普通对话流式追加
            if (messages.value[msgIndex].type === 'pending') {
              messages.value[msgIndex] = { role: 'ai', type: 'chat', content: '' }
            }
            messages.value[msgIndex].content += data.content
          } else if (data.type === 'done') {
            loading.value = false
          }
          await scrollToBottom()
        } catch {}
      }
    }
  } catch {
    ElMessage.error('请求失败，请检查后端服务是否启动')
    messages.value.splice(msgIndex, 1)
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 28px 32px 20px;
  overflow: hidden;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 22px;
  color: #1B5E20;
  font-weight: 700;
}

.page-header p {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

/* 消息区域 */
.message-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-right: 4px;
}

/* 欢迎消息 */
.welcome-msg {
  text-align: center;
  padding: 60px 20px;
  color: #888;
}

.welcome-icon {
  font-size: 56px;
  margin-bottom: 16px;
}

.welcome-msg h3 {
  font-size: 20px;
  color: #2E7D32;
  margin-bottom: 8px;
}

.welcome-msg p {
  font-size: 14px;
  margin-bottom: 24px;
}

.example-box {
  display: inline-block;
  background: white;
  border: 1px solid #C8E6C9;
  border-radius: 12px;
  padding: 16px 24px;
  text-align: left;
}

.example-title {
  font-size: 13px;
  color: #2E7D32;
  font-weight: 600;
  margin-bottom: 8px;
}

.example-content {
  font-size: 13px;
  color: #555;
  line-height: 2;
  font-family: monospace;
  margin-bottom: 8px;
}

/* 消息 */
.message {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.msg-avatar {
  font-size: 28px;
  min-width: 40px;
  text-align: center;
}

.msg-content {
  background: white;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  line-height: 1.7;
  color: #333;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  max-width: 70%;
  white-space: pre-wrap;
}

.user-message .msg-content {
  background: #2E7D32;
  color: white;
}

/* 合规检测结果 */
.compliance-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.result-table-wrapper {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.source-file {
  font-size: 12px;
  color: #2E7D32;
}

.summary-box {
  background: #E8F5E9;
  border-left: 4px solid #4CAF50;
  border-radius: 0 12px 12px 0;
  padding: 14px 18px;
  display: flex;
  gap: 10px;
  align-items: flex-start;
  font-size: 14px;
  color: #2E2E2E;
  line-height: 1.7;
}

.summary-icon {
  font-size: 20px;
  min-width: 24px;
}

/* 加载动画 */
.loading-dots {
  display: flex;
  gap: 6px;
  align-items: center;
  padding: 16px !important;
}

.loading-dots span {
  width: 8px;
  height: 8px;
  background: #4CAF50;
  border-radius: 50%;
  animation: dot-bounce 1.2s infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dot-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40% { transform: scale(1.2); opacity: 1; }
}

/* 输入区域 */
.input-area {
  margin-top: 16px;
  background: white;
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 -2px 20px rgba(0,0,0,0.06);
  border: 1px solid #E8F5E9;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.input-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* MHTML 加载步骤气泡 */
.mhtml-loading-box {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 260px;
}

.mhtml-step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #bbb;
  transition: color 0.3s;
}

.mhtml-step.active {
  color: #2E7D32;
  font-weight: 600;
}

.mhtml-step.done {
  color: #81C784;
}

.step-icon {
  font-size: 15px;
  width: 18px;
  text-align: center;
}

.mhtml-step.active .step-icon {
  animation: spin 1s linear infinite;
  display: inline-block;
}

.mhtml-step.done .step-icon {
  animation: none;
}

.mhtml-hint {
  font-size: 12px;
  color: #aaa;
  margin-top: 4px;
  margin-bottom: 0;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

/* 错误气泡 */
.error-box {
  background: #FFF3F3;
  border: 1px solid #FFCDD2;
  border-radius: 12px;
  padding: 12px 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: #C62828;
  max-width: 500px;
}

.error-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.input-tip {
  font-size: 12px;
  color: #bbb;
}
</style>