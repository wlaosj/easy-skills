---
name: ps4-local-host
description: |
  一键部署 PS4 局域网离线托管服务（nginx:alpine）+ 防误升网络硬隔离（通用路由器 / RouterOS / OpenWrt 三模式）+ NAS 游戏库高速分发。
  当用户要求：
  - 在 NAS / Docker 宿主机（Unraid、群晖、飞牛、PVE、Linux）搭建 PS4 局域网本地托管服务（免公网依赖、支持 .mjs 模块与 .pkg 目录索引）；
  - 为 PS4 配置防误连外网、防自动升级固件的局域网隔离方案（不限路由器型号，支持通用无网关模式、RouterOS 一键脚本与 OpenWrt）；
  - 将 NAS 上的 PS4 游戏目录只读挂载并通过局域网 HTTP 高速分发安装。
---

# PS4 局域网离线托管与防误升隔离部署规范

本 Skill 将真实 7×24 运行验证过的 **「防误升网络硬隔离 + 轻量 Nginx 离线托管 + NAS 游戏库高速分发」** 方案标准化。容器基于 `nginx:alpine`，常驻内存仅约 **5~10 MiB**，支持 Unraid、群晖、飞牛、PVE LXC 及任意 Linux Docker 宿主机。

> [!IMPORTANT]
> **合规与安全声明**：本 Skill 仅提供纯基础设施配置模板与网络隔离规范，**不包含也不分发任何受版权保护的游戏文件或第三方二进制程序**。静态托管页面与本地游戏文件均由用户自行准备或按需从官方开源上游获取。

---

## 一、 核心安全红线（执行前必读）

1. **先断外网，再联 PS4（绝对顺序，严禁颠倒）**：
   - 在网络隔离方案生效并验证完成前，**严禁**引导用户将 PS4 接入带有互联网出口的局域网，防止系统后台静默下载固件更新。
2. **双网卡同时覆盖**：
   - PS4 同时拥有 **Wi-Fi** 与 **有线 LAN** 两个 MAC 地址；若采用路由器侧隔离，务必把用户实际使用的接口（建议两个接口一并绑定）全部纳入拦截列表。
3. **存储只读挂载**：
   - Nginx 配置文件与 NAS 游戏库目录必须一律以 **只读（`:ro`）** 方式挂载进容器，杜绝误删或写入风险。
4. **必须显式声明 `.mjs` MIME 类型**：
   - `nginx:alpine` 默认配置在某些环境下可能未将 `.mjs` 映射为 `application/javascript`，会导致 PS4 浏览器加载 ES Module 白屏报错；必须使用内置的 [`templates/nginx.conf`](templates/nginx.conf)。

---

## 二、 第一阶段：环境信息采集（先问再做，严禁猜测）

动手前向用户确认以下 4 项信息（已有信息无需重复询问）：

1. **Docker 宿主机信息**：宿主机内网 IP（如 `192.168.1.10`）、系统类型（Unraid / 群晖 / 飞牛 / PVE / Linux）及计划开放端口（默认 `8090`）。
2. **宿主机本地目录**：
   - 静态托管文件目录 `{{PS4_WEB_DIR}}`（如 `/mnt/user/appdata/ps4-host/src` 或 `/opt/ps4-host/src`）；
   - （可选）PS4 本地游戏库目录 `{{PS4_GAMES_DIR}}`（如 `/mnt/user/ps4_games`）。
3. **主路由类型**（决定隔离模式）：
   - **模式 A（通用零门槛，推荐）**：任意家用路由器（小米 / 华硕 / TP-Link / 华为 / 光猫等）——无需改路由器规则；
   - **模式 B（RouterOS 7.x 全自动）**：支持通过 SSH 一键下发 DHCP 静态绑定 + 防火墙 `DROP` 规则；
   - **模式 C（OpenWrt 全自动）**：支持通过 SSH/UCI 一键下发防火墙禁网规则。
4. **PS4 网络信息**（仅模式 B/C 需要）：PS4 的 Wi-Fi / LAN MAC 地址及期望分配的固定内网 IP（如 `192.168.1.240` / `192.168.1.241`）。

---

## 三、 第二阶段：防误升网络硬隔离（三选一，必须先于 PS4 联网）

### 模式 A：通用零门槛方案（适用任何路由器，零依赖）
无需登录路由器或具备软路由，提供以下两种等效方式供用户任选其一（推荐方式 1）：

- **方式 1：PS4 本机“无有效网关”手动配网（最稳，物理断外网）**
  - 在 PS4「设定 → 网络 → 设定互联网连接 → 自定义 → IP 地址设定：手动」中填入：
    - **IP 地址**：同网段未占用的固定内网 IP（如 `192.168.x.240`，需避开 DHCP 冲突）
    - **子网掩码**：`255.255.255.0`
    - **默认网关**：填写一个**同网段不存在的内网 IP**（如 `192.168.x.254`，**严禁填真实路由器网关**）
    - **主 DNS / 次 DNS**：同上填写无效内网 IP（如 `192.168.x.254`）
  - **原理**：同网段访问 NAS（如 `http://{{HOST_IP}}:8090`）走二层交换直连，速度跑满且完全正常；所有发往公网的流量因缺少有效三层网关直接被丢弃，**物理上无法连接任何外部服务器**。
- **方式 2：家用路由器 App 禁网**
  - 在路由器管理后台/App 中找到 PS4 设备，开启「禁止联网 / 家长控制断网」并绑定静态 IP。

### 模式 B：RouterOS 7.x 全自动硬隔离
1. 读取模板 [`templates/ros-ps4-isolate.rsc`](templates/ros-ps4-isolate.rsc)，将 `{{PLACEHOLDER}}` 替换为用户的真实参数（DHCP Server 名称、PS4 MAC/IP、WAN 接口/列表名称）。
2. 通过 SSH 下发至 RouterOS，并确认：
   - 防火墙 `forward` 链的 `drop` 规则已插入到**最顶部（`place-before=0` 或早于 FastTrack 与常规放行规则）**，防止被 FastTrack 绕过；
   - 若局域网开启了 IPv6，提醒用户确认 PS4 侧未获取公网 IPv6 或同步在 `/ipv6/firewall/filter` 阻断对应设备。
3. 执行检查：`/ip/firewall/filter/print where comment~"PS4"` 与 `/ip/dhcp-server/lease/print where comment~"PS4"`，确认状态均未禁用（无 `X` 标记）。

### 模式 C：OpenWrt 全自动硬隔离
1. 读取模板 [`templates/openwrt-ps4-isolate.sh`](templates/openwrt-ps4-isolate.sh)，替换 `{{PS4_MAC}}` / `{{PS4_IP}}` 等占位符。
2. 通过 SSH 执行后运行 `uci commit firewall && /etc/init.d/firewall reload`，并校验规则在 `nft list ruleset` / `iptables` 中生效。

---

## 四、 第三阶段：部署 `ps4-host` Docker 容器

### Step 1：检查宿主机端口与目录
在 Docker 宿主机上执行：
```bash
# 确认目标端口未被占用（默认 8090）
ss -tlnp | grep ":{{HOST_PORT}} " || true
# 创建配置与托管目录
mkdir -p "{{PS4_CONFIG_DIR}}" "{{PS4_WEB_DIR}}"
```
> 若用户尚未在 `{{PS4_WEB_DIR}}` 放入静态页面文件，先引导用户自行放入（或按用户指定的官方开源项目版本现场拉取至该目录）；若用户需要 `/games/` 分发，确认 `{{PS4_GAMES_DIR}}` 目录存在。

### Step 2：落盘配置并拉起容器
1. 将 [`templates/nginx.conf`](templates/nginx.conf) 复制到 `{{PS4_CONFIG_DIR}}/nginx.conf`（无需改动，如需调整游戏目录路径仅修改挂载即可）。
2. 将 [`templates/docker-compose.yml`](templates/docker-compose.yml) 复制到 `{{PS4_CONFIG_DIR}}/docker-compose.yml`，替换全部 `{{PLACEHOLDER}}`（若用户暂不挂载游戏库，可注释掉 `/mnt/user/ps4_games` 对应挂载行）。
3. 启动容器（兼容 `docker compose` v2 与 `docker-compose` v1）：
```bash
cd "{{PS4_CONFIG_DIR}}"
(docker compose up -d --force-recreate || docker-compose up -d --force-recreate)
```

---

## 五、 第四阶段：端到端验收门禁（全部通过方可交付）

部署完成后，AI 必须执行以下 4 项真实拨测，**全部通过后再向用户汇报**：

1. **容器健康与日志检查**：
   ```bash
   docker ps --filter name=ps4-host --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
   docker logs --tail 20 ps4-host 2>&1
   ```
   确认状态为 `Up`，无 `emerg` / `error` 报错（`default.conf` 只读提示属于正常 `info`）。
2. **首页连通性拨测**：
   ```bash
   curl -sI -m 3 http://{{HOST_IP}}:{{HOST_PORT}}/ | head -n 5
   ```
   确认返回 `HTTP/1.1 200 OK`（若 `src` 目录尚未放入 `index.html`，应明确提示用户放入后再测）。
3. **`.mjs` MIME 类型校验（防白屏核心门禁）**：
   若 `{{PS4_WEB_DIR}}` 中存在 `.mjs` 文件，任选一个执行：
   ```bash
   curl -sI -m 3 http://{{HOST_IP}}:{{HOST_PORT}}/<sample>.mjs | grep -i "content-type"
   ```
   确认返回 `Content-Type: application/javascript`。
4. **`/games/` 目录索引校验**（如已挂载游戏库）：
   ```bash
   curl -sI -m 3 http://{{HOST_IP}}:{{HOST_PORT}}/games/ | head -n 5
   ```
   确认返回 `HTTP/1.1 200 OK`。

---

## 六、 交付给用户的 PS4 侧收尾检查单

验收通过后，向用户输出以下精简交付卡片：
- **本地托管访问地址**：`http://{{HOST_IP}}:{{HOST_PORT}}/`
- **局域网游戏库索引**：`http://{{HOST_IP}}:{{HOST_PORT}}/games/`（如已挂载）
- **PS4 本机双保险提醒**：
  1. 进入「设定 → 系统 → 自动下载」，取消勾选 **系统软件更新文件**；
  2. 打开 PS4 浏览器，先清空 Cookie 与网站数据，再访问 `http://{{HOST_IP}}:{{HOST_PORT}}/` 并收藏书签；
  3. 确认联网测试中“互联网连接”为失败或不可达、但浏览器能正常打开上述内网地址，即代表**防误升隔离 + 本地托管**双双生效。
