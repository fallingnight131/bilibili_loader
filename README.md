# B站视频下载平台

一个基于 Flask + Vue 3 的 B站视频/番剧下载平台，支持实时进度推送、任务队列管理和文件自动清理。

## 技术栈

### 后端
- **Flask** - Web 框架
- **Flask-SQLAlchemy** - ORM（SQLite 数据库）
- **Flask-JWT-Extended** - JWT 认证
- **Flask-SocketIO** - WebSocket 实时通信
- **Eventlet** - 异步支持

### 前端
- **Vue 3** - 前端框架（Composition API）
- **Vue Router 4** - 路由管理
- **Pinia** - 状态管理
- **Element Plus** - UI 组件库
- **Axios** - HTTP 客户端
- **Socket.IO Client** - WebSocket 客户端
- **Vite** - 构建工具

## 功能特性

- 用户注册/登录（JWT 认证）
- B站普通视频下载（支持 BV 号和完整 URL）
- B站番剧下载（支持 EP 号和完整 URL，每日限额 5 次，2 分钟冷却）
- 单线程任务队列，防止服务器过载
- WebSocket 实时进度推送
- 文件下载完成后 10 分钟自动清理
- 响应式设计，支持移动端

## 安装与运行

### 前置依赖

- Python 3.8+
- Node.js 16+
- FFmpeg（用于音视频合并）

确保 FFmpeg 已安装并在 PATH 中：
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows（PowerShell）- 任选一种
winget install --id Gyan.FFmpeg -e
# 或
choco install ffmpeg
```

### 后端

```bash
cd backend

# 方式一：使用 conda（推荐）
conda create -n bili_loader python=3.10 -y
conda activate bili_loader

# 方式二：使用系统 Python（跳过上面两行 conda 命令）

# 配置环境变量
cp .env.example .env
# 然后编辑 .env 文件，填入以下必要配置：
#
# 1. BILI_SESSDATA 和 BILI_JCT（必填）：
#    在浏览器（建议chrome）登录b站
#    右键打开检查
#    在检查界面的上方菜单选择”应用“
#    在左侧菜单找到Cookie，点击Cookie目录下https://www.bilibili.com 对应的Cookie
#    找到 bili_jct 和 SESSDATA，将它们的值分别复制给 BILI_JCT 和 BILI_SESSDATA
#
# 2. SECRET_KEY 和 JWT_SECRET_KEY（建议修改）：
#    用于 JWT Token 签名，生产环境务必改为随机长字符串
#    可用命令生成：python -c "import secrets; print(secrets.token_hex(32))"

# 安装依赖
pip install -r requirements.txt

# 启动服务
python app.py
# 默认运行在 http://localhost:5001
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 默认运行在 http://localhost:5173
```

## 配置说明

### B站 Cookie 获取方法

1. 登录 [bilibili.com](https://www.bilibili.com)
2. 打开浏览器开发者工具（F12）
3. 切换到 Application/Storage → Cookies
4. 找到 `SESSDATA` 和 `bili_jct` 的值
5. 写入 `backend/.env` 中的 `BILI_SESSDATA` 与 `BILI_JCT`

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `BILI_SESSDATA` | B站登录 Cookie | 空 |
| `BILI_JCT` | B站 CSRF Token | 空 |
| `SECRET_KEY` | Flask 密钥 | 开发用默认值 |
| `JWT_SECRET_KEY` | JWT 签名密钥 | 开发用默认值 |

### 其他配置（config.py）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DOWNLOAD_QUALITY` | 下载清晰度 | 80（1080P） |
| `FILE_EXPIRE_MINUTES` | 文件保留时间（分钟） | 10 |
| `BANGUMI_DAILY_LIMIT` | 番剧每日下载限制 | 5 |
| `BANGUMI_COOLDOWN_SECONDS` | 番剧下载冷却时间（秒） | 120 |

## 使用说明

1. 注册账号并登录
2. 在"视频下载"标签页输入 BV 号或视频链接，点击下载
3. 在"番剧下载"标签页输入 EP 号或番剧链接，点击下载
4. 下载进度会实时显示在任务列表中
5. 下载完成后点击"下载文件"按钮保存到本地
6. 文件在完成后 10 分钟自动清理，请及时下载

## 项目结构

```
├── backend/
│   ├── app.py              # Flask 应用入口
│   ├── config.py            # 配置文件
│   ├── models.py            # 数据库模型
│   ├── auth.py              # 用户认证蓝图
│   ├── routes.py            # 下载 API 蓝图
│   ├── downloader.py        # B站下载核心逻辑
│   ├── task_queue.py        # 任务队列管理
│   ├── scheduler.py         # 过期文件清理
│   ├── websocket.py         # WebSocket 事件
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.js
│   │   ├── App.vue
│   │   ├── router/          # 路由配置
│   │   ├── stores/          # Pinia 状态管理
│   │   ├── views/           # 页面视图
│   │   ├── components/      # UI 组件
│   │   └── utils/           # 工具函数
│   ├── package.json
│   └── vite.config.js
└── README.md
```
