import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export const useDownloadStore = defineStore('download', () => {
  const tasks = ref([])
  const queueStatus = ref({ queue_length: 0, tasks: [] })
  const bangumiQuota = ref({ remaining: 5, daily_limit: 5, cooldown_remaining_seconds: 0 })

  // 获取任务列表
  async function fetchTasks() {
    const res = await api.get('/api/download/tasks')
    if (res.data.code === 0) {
      tasks.value = res.data.data
    }
  }

  // 提交视频下载
  async function submitVideo(input) {
    const res = await api.post('/api/download/video', { input })
    if (res.data.code === 0) {
      await fetchTasks()
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 提交番剧下载
  async function submitBangumi(input) {
    const res = await api.post('/api/download/bangumi', { input })
    if (res.data.code === 0) {
      await fetchTasks()
      await fetchBangumiQuota()
      return res.data.data
    }
    throw new Error(res.data.message)
  }

  // 获取队列状态
  async function fetchQueueStatus() {
    const res = await api.get('/api/download/queue-status')
    if (res.data.code === 0) {
      queueStatus.value = res.data.data
    }
  }

  // 获取番剧配额
  async function fetchBangumiQuota() {
    const res = await api.get('/api/download/bangumi-quota')
    if (res.data.code === 0) {
      bangumiQuota.value = res.data.data
    }
  }

  // 更新单个任务信息（从 WebSocket 推送）
  function updateTask(taskData) {
    const idx = tasks.value.findIndex(t => t.id === taskData.task_id)
    if (idx !== -1) {
      const task = tasks.value[idx]
      if (taskData.progress !== undefined) task.progress = taskData.progress
      if (taskData.status !== undefined) task.status = taskData.status
      if (taskData.title !== undefined) task.title = taskData.title
      if (taskData.expires_at !== undefined) task.expires_at = taskData.expires_at
      if (taskData.file_size !== undefined) task.file_size = taskData.file_size
      if (taskData.error_message !== undefined) task.error_message = taskData.error_message
    }
  }

  // 更新队列状态（从 WebSocket 推送）
  function updateQueueStatus(data) {
    queueStatus.value = data
  }

  // 获取文件下载地址
  function getFileUrl(taskId) {
    return `/api/download/file/${taskId}`
  }

  return {
    tasks, queueStatus, bangumiQuota,
    fetchTasks, submitVideo, submitBangumi,
    fetchQueueStatus, fetchBangumiQuota,
    updateTask, updateQueueStatus, getFileUrl
  }
})
