<template>
  <div class="video-download">
    <p class="desc">输入视频 BV 号或完整链接，下载 B站视频</p>
    <div class="input-row">
      <el-input
        v-model="input"
        placeholder="输入 BV 号（如 BV1c7wEzrEBm）或完整视频链接"
        size="large"
        clearable
        @keyup.enter="handleSubmit"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        @click="handleSubmit"
      >
        下载
      </el-button>
    </div>
    <div class="tips">
      <p>支持格式：</p>
      <ul>
        <li>BV号：BV1c7wEzrEBm</li>
        <li>链接：https://www.bilibili.com/video/BV1c7wEzrEBm</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDownloadStore } from '../stores/download'
import { ElMessage } from 'element-plus'

const downloadStore = useDownloadStore()
const input = ref('')
const loading = ref(false)

async function handleSubmit() {
  if (!input.value.trim()) {
    ElMessage.warning('请输入 BV 号或视频链接')
    return
  }

  loading.value = true
  try {
    const result = await downloadStore.submitVideo(input.value.trim())
    ElMessage.success(`任务已提交，队列位置: ${result.queue_position}`)
    input.value = ''
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.video-download {
  padding: 8px 0;
}

.desc {
  color: #666;
  font-size: 14px;
  margin-bottom: 16px;
}

.input-row {
  display: flex;
  gap: 12px;
}

.input-row .el-input {
  flex: 1;
}

.tips {
  margin-top: 16px;
  color: #999;
  font-size: 12px;
}

.tips ul {
  margin-top: 4px;
  padding-left: 20px;
}

.tips li {
  line-height: 1.8;
}
</style>
