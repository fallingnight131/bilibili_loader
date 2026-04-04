<template>
  <div class="home-container">
    <!-- 顶部导航栏 -->
    <div class="navbar">
      <div class="navbar-brand">
        <span class="logo">▶</span> B站视频下载平台
      </div>
      <div class="navbar-right">
        <el-button type="text" @click="openHelp">说明</el-button>
        <el-button type="text" @click="showSettingsDialog = true">设置</el-button>
        <span class="username">{{ authStore.user?.username }}</span>
        <el-button type="text" @click="handleLogout">退出登录</el-button>
      </div>
    </div>

    <!-- 设置对话框 -->
    <el-dialog v-model="showSettingsDialog" title="B站凭据设置" width="480px">
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
      <p class="settings-tip">提交后将更新后端凭据，您将获得番剧下载次数无限的特权，直到凭据被其他用户更新。</p>
      <template #footer>
        <el-button @click="showSettingsDialog = false">取消</el-button>
        <el-button type="primary" :loading="settingsLoading" @click="handleUpdateCredentials">保存</el-button>
      </template>
    </el-dialog>

    <!-- 主体内容 -->
    <div class="main-content">
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
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
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

// 设置对话框
const showSettingsDialog = ref(false)
const settingsLoading = ref(false)
const settingsForm = ref({ sessdata: '', jct: '' })

onMounted(async () => {
  // 获取用户信息
  await authStore.fetchUser()
  // 拉取任务列表
  await downloadStore.fetchTasks()
  // 拉取队列状态
  await downloadStore.fetchQueueStatus()
  // 连接 WebSocket
  initSocket()
})

onUnmounted(() => {
  disconnectSocket()
})

function handleLogout() {
  authStore.logout()
  disconnectSocket()
  router.push('/login')
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

@media (max-width: 600px) {
  .main-content {
    padding: 0 12px;
    margin: 12px auto;
  }

  .download-tabs {
    padding: 16px;
  }
}

.settings-tip {
  font-size: 13px;
  color: #999;
  margin-top: 8px;
  line-height: 1.6;
}
</style>
