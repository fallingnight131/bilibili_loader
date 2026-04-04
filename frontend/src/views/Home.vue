<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <div class="navbar">
      <div class="navbar-brand">
        <span class="logo">▶</span> B站视频下载平台
      </div>
      <div class="navbar-right" v-if="!isMobile">
        <el-button type="text" @click="openHelp">说明</el-button>
        <el-button type="text" @click="showSettingsDialog = true" :disabled="!isLoggedIn">设置</el-button>
        <span class="username">{{ displayUsername }}</span>
        <el-button v-if="isLoggedIn" type="text" @click="handleLogout">退出登录</el-button>
        <el-button v-else type="text" @click="goLogin">登录</el-button>
      </div>

      <div class="navbar-right mobile-right" v-else>
        <span class="username">{{ displayUsername }}</span>
        <el-dropdown trigger="click">
          <el-button type="text">菜单</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="openHelp">说明</el-dropdown-item>
              <el-dropdown-item :disabled="!isLoggedIn" @click="showSettingsDialog = true">设置</el-dropdown-item>
              <el-dropdown-item v-if="!isLoggedIn" @click="goLogin">登录</el-dropdown-item>
              <el-dropdown-item v-else @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 设置对话框 -->
    <el-dialog
      v-model="showSettingsDialog"
      title="B站凭据设置"
      :width="settingsDialogWidth"
      :top="settingsDialogTop"
      class="settings-dialog"
    >
      <el-form label-position="top">
        <el-form-item label="BILI_SESSDATA">
          <el-input
            v-model="settingsForm.sessdata"
            placeholder="请输入 BILI_SESSDATA"
            type="textarea"
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="BILI_JCT">
          <el-input
            v-model="settingsForm.jct"
            placeholder="请输入 BILI_JCT"
          />
        </el-form-item>
      </el-form>
      <p class="settings-tip">提交后系统将校验 cookie 有效性（需要大会员账号），校验通过后加入 cookie 池，在您提交的 cookie 的有效期内，您将获得番剧下载次数无限的特权。cookie 的获取方式请在说明中查看。</p>
      <template #footer>
        <div class="settings-actions">
          <el-button @click="showSettingsDialog = false">取消</el-button>
          <el-button type="primary" :loading="settingsLoading" @click="handleUpdateCredentials">保存</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 主体内容 -->
    <div class="main-content">
      <div v-if="!isLoggedIn" class="guest-panel">
        <h2>欢迎使用 B站视频下载平台</h2>
        <p>当前状态：未登录。登录后可提交下载任务、查看队列与进度。</p>
        <el-button type="primary" size="large" @click="goLogin">去登录</el-button>
      </div>

      <template v-else>
        <!-- 下载功能区 -->
        <el-tabs v-model="activeTab" class="download-tabs">
          <el-tab-pane label="视频下载" name="video">
            <VideoDownload />
          </el-tab-pane>
          <el-tab-pane label="番剧下载" name="bangumi">
            <BangumiDownload />
          </el-tab-pane>
        </el-tabs>

        <!-- 队列状态 -->
        <QueueStatus />

        <!-- 任务列表 -->
        <div class="task-list-section">
          <h3 class="section-title">下载任务</h3>
          <div v-if="downloadStore.tasks.length === 0" class="empty-tip">
            暂无下载任务
          </div>
          <div v-else class="task-list">
            <TaskProgress
              v-for="task in downloadStore.tasks"
              :key="task.id"
              :task="task"
            />
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useDownloadStore } from '../stores/download'
import { initSocket, disconnectSocket } from '../utils/socket'
import { ElMessage } from 'element-plus'
import api from '../utils/api'
import VideoDownload from '../components/VideoDownload.vue'
import BangumiDownload from '../components/BangumiDownload.vue'
import TaskProgress from '../components/TaskProgress.vue'
import QueueStatus from '../components/QueueStatus.vue'

const router = useRouter()
const authStore = useAuthStore()
const downloadStore = useDownloadStore()
const activeTab = ref('video')
const isMobile = ref(window.innerWidth <= 768)

const isLoggedIn = computed(() => !!authStore.token)
const displayUsername = computed(() => authStore.user?.username || '未登录')

// 设置对话框
const showSettingsDialog = ref(false)
const settingsLoading = ref(false)
const settingsForm = ref({ sessdata: '', jct: '' })
const settingsDialogWidth = computed(() => (isMobile.value ? 'calc(100vw - 24px)' : '480px'))
const settingsDialogTop = computed(() => (isMobile.value ? '6vh' : '15vh'))

onMounted(async () => {
  window.addEventListener('resize', handleResize)
  if (authStore.token) {
    await authStore.fetchUser()
    await downloadStore.fetchTasks()
    await downloadStore.fetchQueueStatus()
    initSocket()
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  disconnectSocket()
})

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}

function goLogin() {
  router.push('/login')
}

function handleLogout() {
  authStore.logout()
  disconnectSocket()
  router.push('/')
}

function openHelp() {
  window.open('https://fallingnight.com', '_blank')
}

async function handleUpdateCredentials() {
  const { sessdata, jct } = settingsForm.value
  if (!sessdata.trim() || !jct.trim()) {
    ElMessage.warning('SESSDATA 和 JCT 不能为空')
    return
  }
  settingsLoading.value = true
  try {
    const res = await api.post('/api/download/settings/bili-credentials', {
      sessdata: sessdata.trim(),
      jct: jct.trim()
    })
    if (res.data.code === 0) {
      ElMessage.success(res.data.message)
      showSettingsDialog.value = false
      settingsForm.value = { sessdata: '', jct: '' }
      // 刷新配额状态
      await downloadStore.fetchBangumiQuota()
    } else {
      ElMessage.error(res.data.message)
    }
  } catch (e) {
    ElMessage.error(e.message || '更新失败')
  } finally {
    settingsLoading.value = false
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: #f5f5f5;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.navbar-brand {
  font-size: 18px;
  font-weight: 600;
  color: #FB7299;
}

.logo {
  font-size: 20px;
}

.navbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.username {
  color: #666;
  font-size: 14px;
}

.main-content {
  max-width: 800px;
  margin: 24px auto;
  padding: 0 16px;
}

.guest-panel {
  background: #fff;
  border-radius: 12px;
  padding: 28px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  text-align: center;
}

.guest-panel h2 {
  margin: 0 0 12px;
  color: #333;
}

.guest-panel p {
  color: #666;
  margin: 0 0 18px;
}

.download-tabs {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.task-list-section {
  margin-top: 24px;
}

.section-title {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
}

.empty-tip {
  text-align: center;
  color: #999;
  padding: 40px 0;
  font-size: 14px;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.settings-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 600px) {
  .navbar {
    padding: 0 12px;
  }

  .navbar-brand {
    font-size: 16px;
  }

  .mobile-right {
    gap: 8px;
  }

  .username {
    font-size: 13px;
  }

  .main-content {
    padding: 0 12px;
    margin: 12px auto;
  }

  .download-tabs {
    padding: 16px;
  }

  .settings-actions {
    flex-direction: column-reverse;
  }

  .settings-actions .el-button {
    width: 100%;
    margin-left: 0;
  }
}

.settings-tip {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
  line-height: 1.6;
}
</style>
