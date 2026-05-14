<template>
  <div class="layout">
    <!-- 侧栏 -->
    <aside class="sidebar">
      <div class="sidebar-logo" @click="router.push('/')">
        <span>🛡️</span>
        <span class="logo-text">EcoGuard</span>
      </div>

      <div class="sidebar-menu">
        <div
          class="menu-item"
          :class="{ active: route.path === '/app/files' }"
          @click="router.push('/app/files')"
        >
          <span class="menu-icon">📁</span>
          <span>文件管理</span>
        </div>
        <div
          class="menu-item"
          :class="{ active: route.path === '/app/chat' }"
          @click="router.push('/app/chat')"
        >
          <span class="menu-icon">💬</span>
          <span>合规问答</span>
        </div>
      </div>

      <div class="sidebar-footer">
        <div class="system-info">
          <span class="dot"></span>
          <span>系统运行中</span>
        </div>
        <p>基于国家排污许可标准</p>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
const router = useRouter()
const route = useRoute()
</script>

<style scoped>
.layout {
  display: flex;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
}

/* 侧栏 */
.sidebar {
  width: 220px;
  min-width: 220px;
  background: linear-gradient(180deg, #1B5E20 0%, #2E7D32 100%);
  display: flex;
  flex-direction: column;
  padding: 24px 0;
  box-shadow: 4px 0 20px rgba(0,0,0,0.15);
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 24px 32px;
  cursor: pointer;
  font-size: 22px;
  color: white;
  font-weight: 700;
  letter-spacing: 2px;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  margin-bottom: 16px;
}

.sidebar-logo span:first-child {
  font-size: 28px;
}

.sidebar-menu {
  flex: 1;
  padding: 0 12px;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border-radius: 12px;
  cursor: pointer;
  color: rgba(255,255,255,0.7);
  font-size: 15px;
  transition: all 0.25s;
  margin-bottom: 4px;
}

.menu-item:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}

.menu-item.active {
  background: rgba(255,255,255,0.15);
  color: white;
  font-weight: 600;
  box-shadow: inset 3px 0 0 #A5D6A7;
}

.menu-icon {
  font-size: 20px;
}

/* 底部 */
.sidebar-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.system-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #A5D6A7;
  font-size: 13px;
  margin-bottom: 6px;
}

.dot {
  width: 8px;
  height: 8px;
  background: #69F0AE;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.sidebar-footer p {
  color: rgba(255,255,255,0.4);
  font-size: 11px;
}

/* 主内容 */
.main {
  flex: 1;
  background: #F1F8E9;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
</style>