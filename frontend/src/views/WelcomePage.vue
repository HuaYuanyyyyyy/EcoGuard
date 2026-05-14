<template>
  <div class="welcome" :class="{ leaving: isLeaving }">
    <!-- 浮动粒子 -->
    <div class="particles">
      <div v-for="i in 15" :key="i" class="particle" :style="getParticleStyle(i)">🌿</div>
    </div>

    <!-- 主内容 -->
    <div class="content">
      <div class="logo">
        <span class="logo-icon">🛡️</span>
        <h1>EcoGuard</h1>
      </div>

      <h2>环保合规智能审查系统</h2>

      <p class="desc">
        基于排污许可国家标准文档的知识库增强索引存储<br />
        对用户提问污染物是否符合文档标准<br />
        使用 LLM 进行格式化输出
      </p>

      <div class="features">
        <div class="feature-item">
          <span class="feature-icon">📄</span>
          <span>标准文档管理</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">🔍</span>
          <span>智能检索分析</span>
        </div>
        <div class="feature-item">
          <span class="feature-icon">✅</span>
          <span>合规判断输出</span>
        </div>
      </div>

      <button class="start-btn" @click="startApp">
        快速开始
        <span class="arrow">↓</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLeaving = ref(false)

const startApp = () => {
  isLeaving.value = true
  setTimeout(() => {
    router.push('/app/chat')
  }, 600)
}

const getParticleStyle = (i) => {
  const size = Math.random() * 20 + 10
  const left = (i * 6.5) % 100
  const delay = (i * 0.4) % 4
  const duration = Math.random() * 6 + 8
  return {
    left: `${left}%`,
    fontSize: `${size}px`,
    animationDelay: `${delay}s`,
    animationDuration: `${duration}s`,
    opacity: Math.random() * 0.5 + 0.2
  }
}
</script>

<style scoped>
.welcome {
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #1B5E20 0%, #2E7D32 40%, #00695C 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  transition: transform 0.6s ease, opacity 0.6s ease;
}

.welcome.leaving {
  transform: translateY(-100%);
  opacity: 0;
}

/* 粒子 */
.particles {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.particle {
  position: absolute;
  bottom: -50px;
  animation: float linear infinite;
}

@keyframes float {
  0% { transform: translateY(0) rotate(0deg); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateY(-110vh) rotate(360deg); opacity: 0; }
}

/* 主内容 */
.content {
  text-align: center;
  color: white;
  z-index: 1;
  padding: 40px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
}

.logo-icon {
  font-size: 56px;
}

.logo h1 {
  font-size: 64px;
  font-weight: 800;
  letter-spacing: 4px;
  text-shadow: 0 4px 20px rgba(0,0,0,0.3);
}

h2 {
  font-size: 22px;
  font-weight: 400;
  color: #A5D6A7;
  margin-bottom: 24px;
  letter-spacing: 2px;
}

.desc {
  font-size: 15px;
  line-height: 2;
  color: rgba(255,255,255,0.75);
  margin-bottom: 40px;
}

.features {
  display: flex;
  justify-content: center;
  gap: 40px;
  margin-bottom: 48px;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #C8E6C9;
}

.feature-icon {
  font-size: 32px;
  background: rgba(255,255,255,0.1);
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  border: 1px solid rgba(255,255,255,0.2);
}

.start-btn {
  background: transparent;
  border: 2px solid white;
  color: white;
  font-size: 18px;
  padding: 14px 48px;
  border-radius: 50px;
  cursor: pointer;
  letter-spacing: 2px;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.start-btn:hover {
  background: white;
  color: #2E7D32;
  transform: translateY(-2px);
  box-shadow: 0 8px 30px rgba(0,0,0,0.2);
}

.arrow {
  animation: bounce 1.5s infinite;
  display: inline-block;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(6px); }
}
</style>