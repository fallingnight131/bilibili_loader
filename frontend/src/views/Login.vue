<template>
  <div class="login-container">
    <div class="login-navbar">
      <div class="login-brand">
        <span class="logo">▶</span> B站视频下载平台
      </div>
      <el-button type="text" class="help-button" @click="openHelp">说明</el-button>
    </div>

    <div class="login-card">
      <h2 class="login-title">登录</h2>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="0"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
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
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        还没有账号？<router-link to="/register">立即注册</router-link>
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
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (e) {
    ElMessage.error(e.message || '登录失败')
  } finally {
    loading.value = false
  }
}

function openHelp() {
  window.open('https://fallingnight.com', '_blank')
}
</script>

<style scoped>
.login-container {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 72px 16px 24px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e8ed 100%);
}

.login-navbar {
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

.login-brand {
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

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.login-title {
  text-align: center;
  margin-bottom: 32px;
  color: #FB7299;
  font-size: 20px;
}

.login-footer {
  text-align: center;
  margin-top: 16px;
  color: #999;
  font-size: 14px;
}

.login-footer a {
  color: #FB7299;
  text-decoration: none;
}

.login-footer a:hover {
  text-decoration: underline;
}

@media (max-width: 600px) {
  .login-container {
    padding: 64px 12px 20px;
  }

  .login-navbar {
    padding: 0 12px;
  }

  .login-brand {
    font-size: 16px;
  }

  .login-card {
    width: 100%;
    max-width: 400px;
    padding: 28px 20px;
  }
}
</style>
