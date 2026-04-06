<template>
  <div class="register-container">
    <div class="register-navbar">
      <div class="register-brand">
        <span class="logo">▶</span> B站视频下载平台
      </div>
      <el-button type="text" class="help-button" @click="openHelp">说明</el-button>
    </div>

    <div class="register-card">
      <h2 class="register-title">注册</h2>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        @submit.prevent="handleRegister"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名（2-20字符）"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（6-20字符，全填1都行）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            style="width: 100%"
            native-type="submit"
          >
            注册
          </el-button>
        </el-form-item>
      </el-form>
      <div class="register-footer">
        已有账号？<router-link to="/login">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()
const formRef = ref()
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 20, message: '用户名长度需在2-20字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度需在6-20字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

async function handleRegister() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.register(form.username, form.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (e) {
    ElMessage.error(e.message || '注册失败')
  } finally {
    loading.value = false
  }
}

function openHelp() {
  window.open('https://fallingnight.com', '_blank')
}
</script>

<style scoped>
.register-container {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 72px 16px 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
}

.register-navbar {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 56px;
  padding: 0 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.register-brand {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 18px;
  font-weight: 600;
  color: #FB7299;
}

.logo {
  font-size: 20px;
}

.help-button {
  color: #FB7299;
}

.register-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.register-title {
  text-align: center;
  margin-bottom: 32px;
  color: #FB7299;
  font-size: 20px;
}

.register-footer {
  text-align: center;
  margin-top: 16px;
  color: #999;
  font-size: 14px;
}

.register-footer a {
  color: #FB7299;
  text-decoration: none;
}

.register-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 600px) {
  .register-container {
    padding: 64px 12px 20px;
  }

  .register-navbar {
    padding: 0 12px;
  }

  .register-brand {
    font-size: 16px;
  }

  .register-card {
    width: 100%;
    max-width: 400px;
    padding: 28px 20px;
  }
}
</style>
