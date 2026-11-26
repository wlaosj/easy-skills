---
name: mihomo-smart-dashboard
description: |
  一键部署 Mihomo Smart (LightGBM) 节点评分与选路可视化看板（零第三方依赖纯 Python + 单页苹果白金 Bento 展示屏）。
  当用户要求：
  - 可视化展示 Mihomo Smart 内核 cache.db 中的千站千面选路、多服务商混跑占比、AI 自动避坑记录与主力专线战绩；
  - 在 Docker 宿主机（PVE LXC / NAS / OpenWrt / Linux）或本机 Python 上快速部署 smart-dashboard；
  - 对接本地 cache.db 只读挂载或通过 SSH 免密拉取 RouterOS 远程 cache.db。
---

# Mihomo Smart 可视化效果看板自动化部署规范

本 Skill 内置完整、零第三方依赖的 [`app/`](app/) 源码，直接只读解析 Mihomo Smart 内核的 bbolt 格式 `cache.db`（完整支持 `overflow` 跨页读取），渲染单页苹果白金浅色 Bento 效果展示屏，常驻内存仅约 **15 MiB**。

---

## 一、 自动识别两种数据源模式（动手前先判断用户环境）

| 模式 | 适用场景 | 核心环境变量 | 特点 |
| :--- | :--- | :--- | :--- |
| **模式 A：本地只读挂载 (`local`)** | Mihomo 运行在本机或同台 Linux / OpenWrt / Unraid / 群晖 / macOS | `SOURCE_MODE=local` + `LOCAL_DB_PATH=/data/cache.db` | **零 SSH 配置**，直接只读挂载 `cache.db`，最简单 |
| **模式 B：远程 SSH 拉取 (`ssh`)** | Mihomo 运行在独立 RouterOS 或另一台软路由，看板部署在独立 Docker 宿主机 | `SOURCE_MODE=ssh` + `ROS_HOST` + `ROS_DB_PATH` + `SSH_KEY_PATH` | 独立只读密钥定时每 60 秒 `scp` 拉取，不打扰主路由 |

---

## 二、 标准化部署流程

### Step 1：确认运行方式与路径
1. 询问或检测用户的目标机器是否安装 Docker（`docker --version` / `docker-compose` / `docker compose`）；
2. 定位 `cache.db` 位置：
   - **本地模式**：确认本地 `cache.db` 绝对路径（如 `/etc/mihomo/cache.db`、`/root/.config/mihomo/cache.db`）；
   - **远程 RouterOS 模式**：确认 RouterOS IP、SSH 端口、用户名与 `cache.db` 路径（通常为 `etc-mihomo/cache.db`）。

### Step 2：配置 SSH 免密（仅模式 B 需要）
1. 在看板宿主机为看板生成**独立专用**密钥（切勿复用 root 全局私钥）：
   ```bash
   mkdir -p /opt/smart-dashboard/ssh
   ssh-keygen -t ed25519 -N "" -f /opt/smart-dashboard/ssh/id_ed25519
   ```
2. 将公钥导入 RouterOS（`/user/ssh-keys/import public-key-file=... user=admin`）或远端主机 `~/.ssh/authorized_keys`，并用 `scp -i /opt/smart-dashboard/ssh/id_ed25519 ...` 实测单次免密拉取成功。

### Step 3：构建并启动服务
- **方式 1：Docker 部署（推荐）**
  将本目录 [`app/`](app/) 复制到宿主机（如 `/opt/smart-dashboard/`），按模式调整 `docker-compose.yml` 中的环境变量与挂载卷，构建并启动：
  ```bash
  cd /opt/smart-dashboard
  docker build -t smart-cache-dashboard:latest .
  # 兼容 docker compose v2 或 docker-compose v1
  (docker compose up -d --force-recreate smart-dashboard || docker-compose up -d --force-recreate smart-dashboard)
  ```
- **方式 2：无 Docker 纯 Python 裸跑（需 Python 3.9+，零 `pip` 依赖）**
  ```bash
  SOURCE_MODE=local LOCAL_DB_PATH=/path/to/cache.db PORT=8899 python3 app/app.py
  ```

### Step 4：端到端验收
必须执行以下 3 项验证通过后再向用户交付：
1. `GET http://<HOST>:8899/` 返回 `HTTP 200`；
2. `GET http://<HOST>:8899/api/data` 返回 JSON 且 `"ready": true`，确认 `overview.customized_sites > 0`；
3. `POST http://<HOST>:8899/api/sync` 返回 `HTTP 200` 且 `"sync_triggered_ok": true`。

交付时向用户提供浏览器访问地址 `http://<HOST>:8899` 及当前实测概览（畅通率、建模拟合站点数、服务商混跑占比）。
