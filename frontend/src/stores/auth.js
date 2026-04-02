import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../utils/api'

export const useAuthStore = defineStore('auth', () => {
  // 从 localStorage 恢复 token
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  // 登录
  async function login(username, password) {
    const res = await api.post('/api/auth/login', { username, password })
    if (res.data.code === 0) {
      token.value = res.data.data.access_token
      localStorage.setItem('token', token.value)
      return true
    }
    throw new Error(res.data.message)
  }

  // 注册
  async function register(username, password) {
    const res = await api.post('/api/auth/register', { username, password })
    if (res.data.code === 0) {
      return true
    }
    throw new Error(res.data.message)
  }

  // 获取当前用户信息
  async function fetchUser() {
    const res = await api.get('/api/auth/me')
    if (res.data.code === 0) {
      user.value = res.data.data
    }
  }

  // 退出登录
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, login, register, fetchUser, logout }
})
