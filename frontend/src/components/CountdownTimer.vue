<template>
  <span class="countdown" :class="{ warning: isWarning }">
    {{ display }}
  </span>
</template>

<script setup>
/**
 * props:
 *   expiresAt - ISO 时间字符串，文件过期时间
 * emits:
 *   expired - 倒计时结束时触发
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  expiresAt: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['expired'])

const remainingSeconds = ref(0)
let timer = null

function calcRemaining() {
  const expires = new Date(props.expiresAt).getTime()
  const now = Date.now()
  return Math.max(0, Math.floor((expires - now) / 1000))
}

function startTimer() {
  if (timer) clearInterval(timer)
  remainingSeconds.value = calcRemaining()

  if (remainingSeconds.value <= 0) {
    emit('expired')
    return
  }

  timer = setInterval(() => {
    remainingSeconds.value = calcRemaining()
    if (remainingSeconds.value <= 0) {
      clearInterval(timer)
      timer = null
      emit('expired')
    }
  }, 1000)
}

const display = computed(() => {
  const m = Math.floor(remainingSeconds.value / 60)
  const s = remainingSeconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

// 倒计时 < 2分钟 时变红
const isWarning = computed(() => remainingSeconds.value < 120)

onMounted(() => {
  startTimer()
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})

watch(() => props.expiresAt, () => {
  startTimer()
})
</script>

<style scoped>
.countdown {
  font-size: 13px;
  color: #67C23A;
  font-variant-numeric: tabular-nums;
}

.countdown.warning {
  color: #F56C6C;
  font-weight: 600;
}
</style>
