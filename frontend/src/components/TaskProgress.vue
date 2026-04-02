<template>
  <div class="task-card" :class="[`status-${task.status}`]">
    <div class="task-header">
      <div class="task-title">
        <el-tag size="small" :type="task.task_type === 'video' ? '' : 'warning'">
          {{ task.task_type === 'video' ? '视频' : '番剧' }}
        </el-tag>
        <span class="title-text">{{ task.title || task.target_id }}</span>
      </div>
      <span class="task-status" :class="statusClass">{{ statusText }}</span>
    </div>

    <!-- 进度条 -->
    <el-progress
      v-if="showProgress"
      :percentage="task.progress"
      :status="progressStatus"
      :stroke-width="8"
      style="margin-top: 12px;"
    />

    <!-- 已完成：下载按钮 + 倒计时 -->
    <div v-if="task.status === 'completed'" class="task-completed">
      <a :href="fileUrl" class="download-link">
        <el-button type="primary" size="small">下载文件</el-button>
      </a>
      <CountdownTimer
        v-if="task.expires_at"
        :expires-at="task.expires_at"
        @expired="onExpired"
      />
      <span v-if="task.file_size" class="file-size">
        {{ formatSize(task.file_size) }}
      </span>
    </div>

    <!-- 已失败：错误信息 -->
    <div v-if="task.status === 'failed'" class="task-error">
      {{ task.error_message || '下载失败' }}
    </div>

    <!-- 已过期 -->
    <div v-if="task.status === 'expired'" class="task-expired">
      文件已过期
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDownloadStore } from '../stores/download'
import CountdownTimer from './CountdownTimer.vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const downloadStore = useDownloadStore()

const fileUrl = computed(() => downloadStore.getFileUrl(props.task.id))

const statusMap = {
  pending: '等待中',
  queued: `排队中（第${props.task.queue_position || '?'}位）`,
  downloading: '下载中',
  merging: '合并中',
  completed: '已完成',
  failed: '已失败',
  expired: '已过期'
}

const statusText = computed(() => {
  if (props.task.status === 'queued') {
    return `排队中（第${props.task.queue_position || '?'}位）`
  }
  return statusMap[props.task.status] || props.task.status
})

const statusClass = computed(() => `status-text-${props.task.status}`)

const showProgress = computed(() =>
  ['downloading', 'merging', 'queued', 'pending'].includes(props.task.status)
)

const progressStatus = computed(() => {
  if (props.task.status === 'completed') return 'success'
  if (props.task.status === 'failed') return 'exception'
  return undefined
})

function formatSize(bytes) {
  if (!bytes) return ''
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB'
}

function onExpired() {
  // 倒计时结束，刷新任务列表
  downloadStore.fetchTasks()
}
</script>

<style scoped>
.task-card {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
}

.task-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-title {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.title-text {
  font-size: 14px;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-status {
  font-size: 12px;
  flex-shrink: 0;
  margin-left: 12px;
}

.status-text-pending,
.status-text-queued {
  color: #909399;
}

.status-text-downloading,
.status-text-merging {
  color: #FB7299;
}

.status-text-completed {
  color: #67C23A;
}

.status-text-failed {
  color: #F56C6C;
}

.status-text-expired {
  color: #C0C4CC;
}

.task-completed {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

.download-link {
  text-decoration: none;
}

.file-size {
  color: #999;
  font-size: 12px;
}

.task-error {
  margin-top: 8px;
  color: #F56C6C;
  font-size: 13px;
}

.task-expired {
  margin-top: 8px;
  color: #C0C4CC;
  font-size: 13px;
}

.status-expired {
  opacity: 0.6;
}
</style>
