# mihomo-smart-dashboard

> **一句话让 AI 搭起 Mihomo Smart 可视化效果屏 —— 千站千面选路、多服务商混跑、AI 自动避坑，一眼看清。**

内置零第三方依赖的纯 Python bbolt 解析引擎（完整支持跨页 `overflow` 记录）与单页苹果白金 Bento 前端，**既支持 Docker 一键部署（常驻仅约 15 MiB 内存），也支持纯 Python 直接裸跑**。

---

## 实机效果预览

<div align="center">
  <img src="assets/preview.jpg" alt="Mihomo Smart 可视化效果屏预览" width="96%" />
</div>

<br />

### 核心特色
- **一秒看懂 Smart 价值**：首屏实时绘制「热门网站 → Smart AI 引擎 → 不同服务商最优专线 + 红色自动避坑拦截」动态流向图。
- **全自动多服务商识别**：无需手写配置，自动正则提取节点 `[前缀]` 并统计各服务商请求/流量混跑占比、自动配色与生成实战战报。
- **双数据源全平台兼容**：
  - **本地只读挂载**：直接读取 OpenWrt / Linux / Unraid / 群晖 / macOS 本机 `cache.db`；
  - **远程 SSH 拉取**：定时每 60 秒免密只读同步 RouterOS 软路由上的 `cache.db`，零侵入主路由。
- **极客抽屉随时深挖**：首页极简清爽，点击右上角「数据明细」可侧滑展开全量节点统计、原始连接明细与策略组评级。

---

## 一句话部署

无需手动配置 —— 复制以下内容、填入您的环境信息发给支持终端的 AI（Antigravity / Claude Code / Cursor / Codex / OpenClaw 通用）：

```text
请拉取 https://github.com/wlaosj/easy-skills 中的 skills/mihomo-smart-dashboard 技能，
按里面的 SKILL.md 把内置的 app/ 看板部署起来：

- 部署目标主机：本机（或 Docker 宿主机 IP：192.168.x.x）
- 数据源方式：本地挂载 /path/to/cache.db（或 SSH 拉取 RouterOS 192.168.x.x 的 etc-mihomo/cache.db）
- 访问端口：8899

完成后请验证 /api/data 和 /api/sync 接口正常，并把看板访问地址发给我。
```

---

## 目录内容

- [`SKILL.md`](SKILL.md) — AI 自动化部署与端到端验收手册
- [`app/bbolt_parser.py`](app/bbolt_parser.py) — 零依赖纯 Python bbolt 解析与 Smart 聚合引擎
- [`app/app.py`](app/app.py) — 支持 `local` / `ssh` 双数据源模式的轻量 HTTP 服务
- [`app/static/index.html`](app/static/index.html) — 单页苹果白金浅色 Bento 展示前端
- [`app/Dockerfile`](app/Dockerfile) & [`app/docker-compose.yml`](app/docker-compose.yml) — 容器编排模板

---

[← 返回 Easy Skills 总目录](../../README.md)
