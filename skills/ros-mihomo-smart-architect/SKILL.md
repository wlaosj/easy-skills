---
name: ros-mihomo-smart-architect
description: |
  在全新 RouterOS 7.x 软路由上自动化部署「CNIP 内核硬件直出 + Mihomo Smart (LightGBM) 容器 + 双轨分流」家庭/工作室级网络架构。
  当用户要求：
  - 在全新或重置的 RouterOS (CHR / x86 / ARM64) 上一键复刻 ROS + Mihomo Smart 分流架构；
  - 配置 RouterOS CNIP 大陆 IP 库、Mangle 路由标记、FastTrack-CNIP-Direct 卸载与 DNS 53 劫持；
  - 部署带 Model.bin 模型的 Mihomo Smart 容器、多机场协同策略组及防断网原子校验；
  - 可选在独立 Docker 宿主机部署 Smart 可视化看板（smart-dashboard）。
---

# RouterOS + Mihomo Smart 双层分流架构自动化部署规范

本 Skill 用于将一台已具备基础外网连通性的 **RouterOS 7.x** 软路由，全自动升级为「**L1 ROS 内核直出 + L2 Mihomo Smart AI 选路**」双层分流网关。

---

## 一、 前置准入清单（动手前向用户确认）

1. **RouterOS 基础状态**：
   - 版本 `>= 7.12`（推荐 `7.20+`），WAN 口已能正常上网（PPPoE 拨号或上级 DHCP）；
   - 已开启 SSH（22 端口），获取 `ROS_IP`、`ROS_USER`、`ROS_PASSWORD`；
   - 已安装官方 **`container`** 扩展包，且已开启容器权限（`/system/device-mode/update container=yes`）。
2. **用户代理资产**：
   - 至少 1 个机场订阅链接（支持多机场混跑协同，如 `第一服务`、`第二服务`、`第三服务`）；
   - 可选：自建 VPS 节点（推荐 `VLESS + xtls-rprx-vision + REALITY` 作为 AI 与核心业务稳态专线）。
3. **可选看板宿主机**：
   - 若需部署 Smart 实时可视化看板，需一台运行 Docker 的独立 Linux/LXC 宿主机（切勿在 ROS 内运行额外重型服务）。

---

## 二、 铁律与防断网安全底线

1. **先备后改**：任何改动前必须先执行 `/export file=backup_before_smart` 留存完整 ROS 配置备份。
2. **先容器、后劫持（防断网原子顺序）**：
   - [`templates/ros-init.rsc`](templates/ros-init.rsc) 中的 `LAN-Route-to-Mihomo`、`LAN-DNS-to-Mihomo` 与 `ROS-Output-to-Mihomo` 默认创建为 `disabled=yes`；
   - 必须先拉起 `mihomo` 容器并确认 `9090` API 与 `7893` 代理端口连通正常，**最后一步**才启用切流与 DNS 53 劫持。
3. **清理默认全局 FastTrack 陷阱**：全新 RouterOS 自带无条件 `defconf: fasttrack` 规则，若不禁用会导致海外流量绕过 Mangle 标记使透明代理完全失效！部署时必须检查并禁用原有全局 `fasttrack-connection`，仅保留带 `dst-address-list=CNIP` 条件的 `FastTrack-CNIP-Direct`。
4. **严禁空节点 Smart 组**：按用户实际接入的机场数量增删 `proxy-providers` 与对应的 `线路一 / 线路二 / 线路三` 策略组；任何正则匹配结果为 0 节点的 `type: smart` 策略组都会导致 Mihomo 启动报错。
5. **P-Unlimited / 定制授权保护**：若检测到 RouterOS 为特殊授权环境，**严禁**执行官方在线升级。
6. **NAT 规则收口铁律**：所有 `Mihomo-*` 端口映射（`9090 / 7890 / 7891 / 7893`）必须强制限定 `dst-address-type=local` 与 `in-interface=!<WAN口>`，防止误劫持局域网出站同端口流量或暴露至公网。
7. **CNIP 防空文件与 64KB 限制保护**：严禁在 ROS 脚本中用 `[/file/get ... contents]` 读取超过 64KB 的文本文件；必须使用 `.rsc` 格式配合 `size > 100000` 校验后 `/import` 导入。

---

## 三、 五阶段标准化部署流水线

### Phase 1：环境体检与备份
通过 SSH 登录 RouterOS，检查系统架构（`x86_64` / `arm64`）、剩余内存（建议 `>= 512 MiB` 空闲）、磁盘空间（建议 `>= 256 MiB` 空闲）、现有网卡与防火墙规则，并先做全量备份：
```routeros
/system/resource/print
/interface/print
/ip/firewall/filter/print where action=fasttrack-connection
/container/print
/export file=backup_before_smart
```

### Phase 2：部署 L1 RouterOS 底座（先建网桥、veth 与 CNIP，暂不切流）
参考模板 [`templates/ros-init.rsc`](templates/ros-init.rsc)，按用户实际 `LAN口`、`WAN口`、`LAN网段` 替换占位符后执行：
1. 检查并禁用 RouterOS 默认的全局 `fasttrack-connection`（保留或新增 `FastTrack-CNIP-Direct`）；
2. 创建 `veth-mihomo`（`172.17.0.2/24`，网关 `172.17.0.1`）与 `bridge-container`（`172.17.0.1/24`）；
3. 创建 `to-mihomo` 路由表与静态路由（`0.0.0.0/0 -> 172.17.0.2`、`198.18.0.0/16 -> 172.17.0.2`）；
4. 写入 `update-cnip` 脚本（使用 `cnip.rsc` + `size > 100000` 校验 + `/import`）并创建每周定时任务；立即导入一次 CNIP（若 ROS 切流前直连 GitHub 超时，由 Agent 本机下载 `cnip.rsc` 后 `scp` 上传至 ROS 并执行 `/import file-name=cnip.rsc`），确认 `[/ip/firewall/address-list/print count-only where list=CNIP]` `> 4000`；
5. 配置 `LAN_LOCAL`、`BYPASS_HOSTS`、`MY_INFRA_DIRECT`（自建 VPS IP 务必加入此列表防回环）及 PPPoE MSS Clamp；
6. 添加 Mangle、收口 NAT 与 DNS 53 劫持规则（其中切流与 DNS 劫持先保持 `disabled=yes`）。

### Phase 3：部署 L2 Mihomo Smart 容器与模型
1. **准备配置目录**：在 ROS 挂载目录（如 `/etc-mihomo`）放置基于 [`templates/mihomo-smart-config.yaml`](templates/mihomo-smart-config.yaml) 渲染的 `config.yaml`：
   - 填入用户的 `proxy-providers` 订阅链接（多机场时同步启用 `线路二 / 线路三` 并在 `默认代理`、`SelectPY` 等列表补充引用；单机场保持默认仅 `线路一`）；
   - 确认 `BaseProvider` 默认直连拉取订阅（避免首次启动代理尚未就绪时的鸡生蛋死锁；若订阅链接被墙再按需指定代理或由本机预下载）；
   - 设置强随机 `secret`（WebUI 密码）与 `authentication`；
   - 确认 Smart 策略组开启 `type: smart`、`uselightgbm: true`、`collectdata: true`、`strategy: sticky-sessions`。
2. **部署 Smart 内核与 `Model.bin`**：
   - 拉取或导入 Mihomo 容器镜像（优先支持 Smart 的镜像，或基于 `metacubex/mihomo:latest` 替换为 `vernesong/mihomo` Releases 中对应架构 `amd64-v3`/`amd64`/`arm64` 的 `alpha-smart` 二进制）；
   - 下载配套 `Model.bin` 放入 `/etc-mihomo/Model.bin`（容器内映射路径 `/root/.config/mihomo/Model.bin`）；
   - **权限注意**：通过 SFTP/SCP 上传二进制到 ROS 文件系统会丢失 `+x` 权限（变为 `0666`），替换容器内二进制后需通过 `/container/shell` 执行 `chmod 755 /mihomo`（或在打包 `.tar` 镜像前赋予 `0755`）；
   - 通过 `/container/add` 挂载 `/etc-mihomo:/root/.config/mihomo`，启动容器并等待 5~8 秒。
3. **容器就绪验证（未切全局流量前必须全部通过）**：
   - 检查 `/container/print` 状态为 `R`（Running）；
   - 验证 `http://<ROS_IP>:9090/version` 返回 Smart 版本，容器日志确认 `[Smart] Model file loaded successfully`；
   - 验证 `http://<ROS_IP>:9090/proxies` 中所有 Smart 策略组均成功加载到节点；
   - 用 `curl -x http://<ROS_IP>:7893 https://www.gstatic.com/generate_204` 验证返回 `HTTP 204`。

### Phase 4：安全切流与防火墙收口
确认 Phase 3 全部通过后，启用切流与 DNS 劫持：
```routeros
/ip/firewall/mangle/enable [find comment~"LAN-Route-to-Mihomo|ROS-Output-to-Mihomo"]
/ip/firewall/nat/enable [find comment~"LAN-DNS-to-Mihomo"]
```
并核对 IPv4/IPv6 WAN 入站丢弃规则（`Drop-WAN-Input` / `Drop-WAN-Forward`）无误。

### Phase 5：端到端验收与交付
向用户汇报以下实测结果（必须全部验证通过）：
1. **国内直连零损耗**：ROS `FastTrack-CNIP-Direct` 计数器增长，`CNIP` 条目数正常（`4000+`）；
2. **海外代理与 Smart 生效**：经 `7893` 端口访问 `gstatic/generate_204` 返回 `204`，`9090` API 正常返回 Smart 策略组且无报错；
3. **DNS 防污染**：局域网解析海外域名返回 `198.18.x.x` Fake-IP，解析国内域名直返真实国内 IP；
4. **Zashboard 面板**：输出管理地址 `http://<ROS_IP>:9090/ui/zashboard/` 与密钥，并提醒留存备份文件 `backup_before_smart.rsc`。
