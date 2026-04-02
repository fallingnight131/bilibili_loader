import { io } from 'socket.io-client'
import { useDownloadStore } from '../stores/download'

let socket = null

export function initSocket() {
  const token = localStorage.getItem('token')
  if (!token) return

  // 断开旧连接
  if (socket) {
    socket.disconnect()
  }

  socket = io('/', {
    auth: { token },
    transports: ['websocket', 'polling']
  })

  socket.on('connect', () => {
    console.log('WebSocket 已连接')
  })

  socket.on('disconnect', () => {
    console.log('WebSocket 已断开')
  })

  // 监听任务进度更新
  socket.on('task_progress', (data) => {
    const downloadStore = useDownloadStore()
    downloadStore.updateTask(data)
  })

  // 监听队列状态更新
  socket.on('queue_update', (data) => {
    const downloadStore = useDownloadStore()
    downloadStore.updateQueueStatus(data)
  })

  // 监听任务完成
  socket.on('task_completed', (data) => {
    const downloadStore = useDownloadStore()
    downloadStore.updateTask({
      task_id: data.task_id,
      status: 'completed',
      progress: 100,
      title: data.title,
      expires_at: data.expires_at,
      file_size: data.file_size
    })
  })

  // 监听任务失败
  socket.on('task_failed', (data) => {
    const downloadStore = useDownloadStore()
    downloadStore.updateTask({
      task_id: data.task_id,
      status: 'failed',
      error_message: data.error_message
    })
  })
}

export function disconnectSocket() {
  if (socket) {
    socket.disconnect()
    socket = null
  }
}
