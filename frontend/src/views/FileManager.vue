<template>
  <div class="file-manager">
    <!-- 顶部标题栏 -->
    <div class="page-header">
      <div class="header-left">
        <h2>📁 文件管理</h2>
        <p>管理排污许可国家标准文档</p>
      </div>
      <el-button type="primary" @click="triggerUpload" :loading="uploading">
        <span>⬆️ 上传文档</span>
      </el-button>
      <input ref="fileInput" type="file" accept=".pdf" style="display:none" @change="handleUpload" />
    </div>

    <!-- 搜索栏 -->
    <div class="search-bar">
      <el-input
        v-model="searchText"
        placeholder="搜索文件名..."
        prefix-icon="Search"
        clearable
        style="width: 300px"
      />
      <span class="file-count">共 {{ filteredFiles.length }} 个文件</span>
    </div>

    <!-- 文件列表 -->
    <div class="file-list">
      <el-empty v-if="filteredFiles.length === 0" description="暂无文件，请上传标准文档" />

      <div
        v-for="file in filteredFiles"
        :key="file.id"
        class="file-card"
      >
        <div class="file-icon">📄</div>
        <div class="file-info">
          <div class="file-name">{{ file.file_name }}</div>
          <div class="file-meta">
            <span>{{ formatSize(file.file_size) }}</span>
            <span class="divider">·</span>
            <span>{{ formatDate(file.upload_time) }}</span>
          </div>
        </div>
        <div class="file-actions">
          <el-button
            type="danger"
            size="small"
            plain
            @click="confirmDelete(file)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>
  </div>

  <!-- 删除确认弹窗 -->
  <el-dialog v-model="deleteDialogVisible" title="确认删除" width="400px">
    <p>确定要删除 <strong>{{ deleteTarget?.file_name }}</strong> 吗？</p>
    <p style="color: #999; font-size: 13px; margin-top: 8px">
      删除后将同步清除向量数据库中的相关数据，无法恢复。
    </p>
    <template #footer>
      <el-button @click="deleteDialogVisible = false">取消</el-button>
      <el-button type="danger" @click="handleDelete" :loading="deleting">确认删除</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fileApi } from '../api/index'

const files = ref([])
const searchText = ref('')
const uploading = ref(false)
const deleting = ref(false)
const fileInput = ref(null)
const deleteDialogVisible = ref(false)
const deleteTarget = ref(null)

// 过滤文件列表
const filteredFiles = computed(() =>
  files.value.filter(f =>
    f.file_name.toLowerCase().includes(searchText.value.toLowerCase())
  )
)

// 加载文件列表
const loadFiles = async () => {
  try {
    const res = await fileApi.list()
    files.value = res.data
  } catch {
    ElMessage.error('加载文件列表失败')
  }
}

// 触发文件选择
const triggerUpload = () => fileInput.value.click()

// 上传文件
const handleUpload = async (e) => {
  const file = e.target.files[0]
  if (!file) return
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', file)
    await fileApi.upload(formData)
    ElMessage.success('上传成功，正在处理文档...')
    await loadFiles()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '上传失败')
  } finally {
    uploading.value = false
    fileInput.value.value = ''
  }
}

// 确认删除
const confirmDelete = (file) => {
  deleteTarget.value = file
  deleteDialogVisible.value = true
}

// 执行删除
const handleDelete = async () => {
  deleting.value = true
  try {
    await fileApi.delete(deleteTarget.value.id)
    ElMessage.success('删除成功')
    deleteDialogVisible.value = false
    await loadFiles()
  } catch {
    ElMessage.error('删除失败')
  } finally {
    deleting.value = false
  }
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (!bytes) return '未知'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

// 格式化日期
const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(loadFiles)
</script>

<style scoped>
.file-manager {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 28px 32px;
  overflow: hidden;
}

.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  flex: 1;
}

.header-left h2 {
  font-size: 22px;
  color: #1B5E20;
  font-weight: 700;
}

.header-left p {
  font-size: 13px;
  color: #888;
  margin-top: 4px;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.file-count {
  color: #888;
  font-size: 13px;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-card {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: all 0.2s;
  border: 1px solid #E8F5E9;
}

.file-card:hover {
  box-shadow: 0 4px 16px rgba(46,125,50,0.12);
  border-color: #A5D6A7;
  transform: translateY(-1px);
}

.file-icon {
  font-size: 36px;
}

.file-info {
  flex: 1;
}

.file-name {
  font-size: 15px;
  font-weight: 600;
  color: #2E2E2E;
  margin-bottom: 4px;
}

.file-meta {
  font-size: 13px;
  color: #999;
  display: flex;
  gap: 6px;
}

.divider {
  color: #ddd;
}
</style>