<template>
  <div class="bangumi-download">
    <p class="desc">输入番剧 EP 号或完整链接，下载 B站番剧</p>
    <div class="input-row">
      <el-input
        v-model="input"
        placeholder="输入 EP 号（如 ep293024 或 293024）或番剧链接"
        size="large"
        clearable
        @keyup.enter="handleSubmit"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        :disabled="!quota.is_privileged && quota.remaining <= 0"
        @click="handleSubmit"
      >
        下载
      </el-button>
    </div>

    <!-- 配额信息 -->
    <div class="quota-info">
      <div class="quota-item" v-if="quota.is_privileged">
        <el-tag type="success" size="small">无限下载特权</el-tag>
      </div>
      <template v-if="!quota.is_privileged">
        <div class="quota-item">
          <span>今日剩余次数：</span>
          <el-tag :type="quota.remaining > 0 ? 'success' : 'danger'" size="small">
            {{ quota.remaining }} / {{ quota.daily_limit }}
          </el-tag>
        </div>
      </template>
    </div>

    <div class="tips">
      <p>支持格式：</p>
      <ul>
        <li>EP号：ep293024 或 293024</li>
        <li>链接：https://www.bilibili.com/bangumi/play/ep293024</li>
      </ul>
      <p class="limit-tip">{{ quota.is_privileged ? '您已拥有无限下载特权' : `每日限制 ${quota.daily_limit} 次` }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useDownloadStore } from '../stores/download'
import { ElMessage } from 'element-plus'

const downloadStore = useDownloadStore()
const input = ref('')
const loading = ref(false)

const quota = computed(() => downloadStore.bangumiQuota)

onMounted(async () => {
  await downloadStore.fetchBangumiQuota()
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
    await downloadStore.fetchBangumiQuota()
  } catch (e) {
    ElMessage.error(e.message || '提交失败')
    await downloadStore.fetchBangumiQuota()
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
