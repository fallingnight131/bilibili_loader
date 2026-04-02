<template>
  <div v-if="downloadStore.queueStatus.queue_length > 0" class="queue-status">
    <div class="queue-animation">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
    <p class="queue-text">
      当前平台使用人数较多，您前方还有
      <strong>{{ downloadStore.queueStatus.queue_length }}</strong>
      位用户正在排队
    </p>
  </div>
</template>

<script setup>
import { useDownloadStore } from '../stores/download'

const downloadStore = useDownloadStore()
</script>

<style scoped>
.queue-status {
  margin-top: 16px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #fff5f7, #fff0f3);
  border: 1px solid #fde2e8;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.queue-text {
  color: #666;
  font-size: 14px;
}

.queue-text strong {
  color: #FB7299;
}

.queue-animation {
  display: flex;
  gap: 4px;
  align-items: center;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #FB7299;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

.dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes bounce {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
