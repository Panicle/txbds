# 智能铁鞋服务端 - 部署指南

## 项目结构
```
.
├── web/                    # 前端静态文件（可部署到IGA Pages）
│   ├── index.html
│   ├── style.css
│   └── app.js
├── server.py               # TCP服务端（需部署到云服务器）
├── web_server.py           # Web服务端（需部署到云服务器）
└── ...其他后端文件
```

## 部署方案：前端 + 后端分离

### 第一步：部署前端到 IGA Pages

#### 方式1：使用 Skill 部署（推荐）
在 TRAE Builder 中输入：
```
将当前项目的 web 目录部署到 IGA Pages
```

#### 方式2：使用 CLI 部署
```bash
# 安装 IGA Pages CLI
npm install -g @iga-pages/cli

# 登录火山引擎账号
iga login

# 进入 web 目录
cd web

# 执行部署
iga pages deploy
```

### 第二步：部署后端到云服务器

#### 1. 准备云服务器
- 购买云服务器（阿里云/腾讯云/火山引擎等）
- 开放端口：8001（基准站）、8002（移动站）、8080（Web）

#### 2. 部署步骤
```bash
# 连接服务器
ssh root@your-server-ip

# 安装 Python 和依赖
apt update && apt install -y python3 python3-pip
pip3 install fastapi uvicorn

# 上传项目文件
scp -r ./* root@your-server-ip:/opt/smart-shoe/

# 启动服务
cd /opt/smart-shoe

# 启动 TCP 服务端（后台运行）
nohup python3 server.py > tcp.log 2>&1 &

# 启动 Web 服务端（后台运行）
nohup python3 web_server.py > web.log 2>&1 &

# 查看运行状态
ps aux | grep python3
```

### 第三步：配置前端连接后端

在 IGA Pages 控制台设置环境变量：
```
BACKEND_URL = http://your-server-ip:8080
```

或者修改前端配置：
```html
<script src="app.js" data-backend-url="http://your-server-ip:8080"></script>
```

## 配置说明

### 端口配置
| 端口 | 用途 |
|------|------|
| 8001 | 基准站TCP端口 |
| 8002 | 移动站TCP端口 |
| 8080 | Web服务端口 |

### 防火墙配置
```bash
# 开放端口
ufw allow 8001/tcp
ufw allow 8002/tcp
ufw allow 8080/tcp
ufw enable
```

## 验证部署

1. **前端验证**：访问 IGA Pages 返回的预览链接
2. **后端验证**：访问 http://your-server-ip:8080/api/coords
3. **设备连接验证**：使用测试客户端发送数据

## 本地开发测试

```bash
# 启动后端服务
python server.py        # 终端1
python web_server.py    # 终端2

# 发送测试数据
python test_client.py test

# 访问前端
http://localhost:8080
```

## 注意事项

1. **HTTPS配置**：生产环境建议配置HTTPS（使用Nginx反向代理）
2. **WebSocket跨域**：确保后端配置正确的CORS策略
3. **服务稳定性**：建议使用 systemd 管理服务进程
4. **数据备份**：定期备份 SQLite 数据库文件