# Vercel 部署指南

## 项目结构
```
.
├── api/                   # Vercel Serverless Functions
│   ├── index.py           # FastAPI入口
│   ├── coords.py          # 坐标API
│   ├── nfc.py             # NFC API
│   └── ws.py              # WebSocket支持
├── web/                   # 前端静态文件
│   ├── index.html
│   ├── style.css
│   └── app.js
├── vercel.json            # Vercel配置
├── requirements.txt       # Python依赖
└── storage.py             # 数据库模块
```

## 部署步骤

### 步骤1：安装 Vercel CLI
```bash
npm install -g vercel
```

### 步骤2：登录 Vercel
```bash
vercel login
```

### 步骤3：部署到 Vercel
```bash
# 开发预览
vercel

# 生产部署
vercel --prod
```

## 注意事项

### Vercel Serverless 限制
1. **不支持 TCP 服务端**：`server.py` 需要部署到云服务器
2. **WebSocket 支持**：需要使用 Edge Functions
3. **数据库**：SQLite 在 Serverless 环境中有限制，建议使用云数据库

### 推荐架构
```
┌─────────────────────────────────────────────┐
│              Vercel (前端 + API)            │
│  - web/* (静态托管)                          │
│  - api/* (Serverless Functions)             │
└─────────────────────────────────────────────┘
                        ↑
                        │ HTTP/WebSocket
                        ↓
┌─────────────────────────────────────────────┐
│           云服务器 (TCP服务端)                │
│  - server.py (监听8001/8002端口)            │
│  - 接收设备数据并转发到 Vercel API          │
└─────────────────────────────────────────────┘
```

### 环境变量配置
在 Vercel 控制台设置：
```
BACKEND_URL = http://your-server-ip:8080
DB_PATH = /tmp/smart_shoe.db
```

## 本地开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动本地开发服务器
vercel dev

# 访问
http://localhost:3000
```

## 完整部署方案

### 1. 部署前端 + API 到 Vercel
```bash
vercel --prod
```

### 2. 部署 TCP服务端到云服务器
```bash
ssh root@your-server-ip
cd /opt/smart-shoe
nohup python3 server.py > tcp.log 2>&1 &
```

### 3. 配置前端连接
修改 `web/app.js` 中的后端地址：
```javascript
const backendUrl = 'https://your-vercel-app.vercel.app';
```

## 测试

```bash
# 发送测试坐标
python test_client.py position 34.26 108.95

# 访问网页
https://your-vercel-app.vercel.app
```