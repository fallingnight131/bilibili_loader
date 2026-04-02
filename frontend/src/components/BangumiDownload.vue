<template>
  <div class="bangumi-download">
    <p class="desc">输入番剧 EP 号或完整链接，下载 B站番剧</p>
    <div class="input-row">
      <el-input
        v-model="input"
        placeholder="输入 EP 号（如 ep259707 或 259707）或番剧链接"
        size="large"
        clearable
        @keyup.enter="handleSubmit"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        :disabled="quota.cooldown_remaining_seconds > 0 || quota.remaining <= 0"
        @click="handleSubmit"
      >
        下载
      </el-button>
    </div>

    <!-- 配额信息 -->
    <div class="quota-info">
      <div class="quota-item">
        <span>今日剩余次数：</span>
        <el-tag :type="quota.remaining > 0 ? 'success' : 'danger'" size="small">
          {{ quota.remaining }} / {{ quota.daily_limit }}
        </el-tag>
      </div>
      <div v-if="cooldownDisplay > 0" class="quota-item cooldown">
        <span>冷却中：</span>
        <el-tag type="warning" size="small">{{ cooldownDisplay }}s</el-tag>
      </div>
    </div>

    <div class="tips">
      <p>支持格式：</p>
      <ul>
        <li>EP号：ep259707 或 259707</li>
        <li>链接：https://www.bilibili.com/bangumi/play/ep259707</li>
      </ul>
      <p class="limit-tip">每日限制 {{ quota.daily_limit }} 次，每次间隔 2 分钟</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useDownloadStore } from '../stores/download'
import { ElMessage } from 'element-plus'

const downloadStore = useDownloadStore()
const input = ref('')
const loading = ref(false)
const cooldownDisplay = ref(0)
let cooldownTimer = null

const quota = computed(() => downloadStore.bangumiQuota)

// 冷却时间倒计时
function startCooldownTimer() {
  if (cooldownTimer) clearInterval(cooldownTimer)
  cooldownDisplay.value = quota.value.cooldown_remaining_seconds

  if (cooldownDisplay.value > 0) {
    cooldownTimer = setInterval(() => {
      cooldownDisplay.value--
      if (cooldownDisplay.value <= 0) {
        clearInterval(cooldownTimer)
        cooldownTimer = null
        downloadStore.fetchBangumiQuota()
      }
    }, 1000)
  }
}

watch(() => downloadStore.bangumiQuota.cooldown_remaining_seconds, () => {
  startCooldownTimer()
})

onMounted(async () => {
  await downloadStore.fetchBangumiQuota()
  startCooldownTimer()
})

onUnmounted(() => {
  if (cooldownTimer) clearInterval(cooldownTimer)
})

async function handleSubmit() {
  if (!input.value.trim()) {
    ElMessage.warning('请输入 EP 号或番剧链接')
    return
  }

  loading.value = true
  try {
    const result = await downloadStore.submitBangumi(input.value.trim())
    ElMessage.success(`任务已提交，队列位置: ${result.queue_position}`)
    input.value = ''
    // 刷新配额并重置冷却
    await downloadStore.fetchBangumiQuota()
    startCooldownTimer()
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
    // 如果是冷却错误，也刷新配额
    await downloadStore.fetchBangumiQuota()
    startCooldownTimer()
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.bangumi-download {
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

.quota-info {
  display: flex;
  gap: 24px;
  margin-top: 12px;
  align-items: center;
}

.quota-item {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.cooldown {
  color: #E6A23C;
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

.limit-tip {
  margin-top: 8px;
  color: #FB7299;
}
</style>
