# ros-mihomo-smart-architect

> **一台全新 RouterOS 7.x + 一句话 = 全自动「CNIP 硬件直出 + Mihomo Smart (LightGBM) 多机场混跑」双层智能分流网关。**

本技能将整套经过长期实战打磨的 RouterOS + Mihomo Smart 架构固化为标准化 AI Agent 操作手册（[`SKILL.md`](SKILL.md)）与全量脱敏模板（[`templates/`](templates/)），自动完成备份、部署、防断网原子切流与端到端验收。

---

## 架构全景

<div align="center">
  <img src="assets/ros-mihomo-smart-arch.jpg" alt="家庭智能双轨网络架构" width="96%" />
</div>

<br />

- **L1 内核级国内卸载（RouterOS）**：每周自动更新大陆 `CNIP` IP 库（内置防空文件字节校验），命中流量在 Mangle 层直接放行并走 `FastTrack-CNIP-Direct` 硬件加速，国内 4K 与大文件下载几乎 **0 CPU 占用**、不经过代理容器。
- **L2 Smart AI 按站选路（Mihomo Smart）**：内置 LightGBM 模型与 `sticky-sessions`，为每个网站独立评估最优专线并自动将多家机场混跑叠加；遇到单站抽风时精准定向避坑，不误伤整条好节点。
- **双轨出口解耦**：支持将 AI 编程与核心业务独立指派给自建稳态专线（固定低风控出口），其余高吞吐海外流量交由多机场 Smart 池协同分担。

---

## 真实环境脱敏实测基线

在 i3 低功耗 PVE + RouterOS CHR（4C4G）+ 3 家机场混跑环境下的真实运行表现：

| 累计护航请求 | 综合畅通率 | 多线协同峰值 | Mihomo 容器内存 |
| :---: | :---: | :---: | :---: |
| **450,000+ 次** | **98.2%** | **73.9 MB/s** | **~210 MiB** |

---

## 前置准备

只需一台刚装好的 **RouterOS 7.x**（推荐 `7.12+`）满足以下 3 个条件：
1. WAN 口已能上网（PPPoE 拨号或上级 DHCP），操作电脑可经局域网直连 ROS；
2. 已开启 SSH（22 端口），已安装官方 `container` 包并开启容器权限（`/system/device-mode/update container=yes`）；
3. 准备好您的机场订阅链接（以及可选的自建 VPS 节点信息）。

---

## 一句话唤醒 AI 部署

**零安装直接用**（适用于 Antigravity / Claude Code / Cursor / Codex / OpenClaw 等支持终端的 Agent），复制以下内容并填入您的信息发给 AI：

```text
请拉取 https://github.com/wlaosj/easy-skills 仓库中的 skills/ros-mihomo-smart-architect 技能，
严格按照里面的 SKILL.md 与 templates 模板，帮我在这台全新 RouterOS 上部署双层智能分流架构：

- RouterOS 地址：192.168.x.x（SSH 账号：admin，密码：xxxxxx）
- WAN 口名称：pppoe-out1，LAN 网段：192.168.x.0/24
- 机场订阅链接：https://你的订阅链接

要求：严格遵循先备份、先起容器验通 9090/7893、最后切 Mangle 与 DNS 的防断网顺序，完成后输出端到端验收结果。
```

---

## 包含文件

- [`SKILL.md`](SKILL.md) — AI Agent 五阶段标准化执行手册与防断网安全门禁
- [`templates/mihomo-smart-config.yaml`](templates/mihomo-smart-config.yaml) — 全量脱敏 Mihomo Smart 配置模板（LightGBM、Fake-IP、纯 UDP 国内 DNS + 海外 DoH、QUIC 拦截、`LocationDKS` 优先级修正）
- [`templates/ros-init.rsc`](templates/ros-init.rsc) — RouterOS 7.x 初始化脚本模板（容器网桥、`CNIP` 防空更新、`FastTrack-CNIP-Direct`、收口 NAT、DNS 53 劫持）

---

[← 返回 Easy Skills 技能目录](../../README.md)
