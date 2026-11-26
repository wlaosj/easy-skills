<div align="center">

<img src="assets/banner.svg" alt="Easy Skills Banner" width="100%" />

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-0066CC?style=flat-square)](LICENSE)
[![Agent Compatible](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-15803D?style=flat-square)](#极速上手)
[![Production Verified](https://img.shields.io/badge/Status-Battle--Tested-EA580C?style=flat-square)](#技能目录)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-334155?style=flat-square)](CONTRIBUTING.md)

<p>
  <strong>一套经过真实环境长期打磨的 AI Agent 实战技能合集。</strong><br />
  不再反复复制粘贴零散教程 —— 把标准化的 <code>SKILL.md</code> 与脱敏模板交给 AI，让复杂任务一键闭环。<br />
  <sub>A curated collection of production-tested AI Agent Skills — modular, sanitized, and ready for any modern coding or ops agent.</sub>
</p>

<p>
  <a href="#技能目录">技能目录</a> ·
  <a href="#极速上手">极速上手</a> ·
  <a href="#设计理念">设计理念</a> ·
  <a href="#仓库结构">仓库结构</a>
</p>

</div>

---

## 技能目录

每个技能均为独立自包含目录，点击技能名称即可查看完整的**架构图、实测效果与专属用法**：

| 技能名称 | 领域分类 | 核心能力简介 | 详情与模板 |
| :--- | :--- | :--- | :---: |
| [`ros-mihomo-smart-architect`](skills/ros-mihomo-smart-architect/) | 网络 / 软路由 | 全新 RouterOS 7.x 一键部署 CNIP 硬件直出 + Mihomo Smart (LightGBM) 多机场混跑与防断网原子校验 | [查看详情](skills/ros-mihomo-smart-architect/) |

> 仓库持续沉淀并开源经过真实环境验证的高质量技能，欢迎点一颗 **Star** 关注后续更新。

---

## 极速上手

### 方式一：零安装，一句话直接甩给 AI（最推荐）

只要您的 AI 助手支持终端或联网（**Antigravity / Claude Code / Cursor / Codex / OpenClaw** 等通用），无需手动克隆目录，直接发给 AI 即可按需拉取任意技能执行：

```text
请拉取 https://github.com/wlaosj/easy-skills 仓库中的 <技能名称> 技能，
完整阅读对应目录下的 SKILL.md 与模板文件，严格按照其中的安全规范与校验步骤帮我完成任务。
```

### 方式二：安装到本地技能目录（一次安装，永久自动触发）

<details>
<summary>点击展开 Antigravity / Claude Code / Cursor 一行安装命令</summary>

```bash
# Antigravity (Gemini)
git clone https://github.com/wlaosj/easy-skills.git /tmp/easy-skills \
  && mkdir -p ~/.gemini/config/skills \
  && cp -R /tmp/easy-skills/skills/* ~/.gemini/config/skills/ \
  && rm -rf /tmp/easy-skills

# Claude Code
git clone https://github.com/wlaosj/easy-skills.git /tmp/easy-skills \
  && mkdir -p ~/.claude/skills \
  && cp -R /tmp/easy-skills/skills/* ~/.claude/skills/ \
  && rm -rf /tmp/easy-skills

# Cursor
git clone https://github.com/wlaosj/easy-skills.git /tmp/easy-skills \
  && mkdir -p ~/.cursor/skills \
  && cp -R /tmp/easy-skills/skills/* ~/.cursor/skills/ \
  && rm -rf /tmp/easy-skills
```

安装完成后重启或新开会话，AI 会自动扫描 `SKILL.md` 描述并在对应场景下按需激活。

</details>

---

## 设计理念

- **拒绝“玩具提示词”**：每一个 Skill 都提炼自真实长期运行的工程或运维实践，把容易踩坑的边界条件固化为强制校验门禁。
- **高内聚、自包含**：每个子技能独立管理自己的 `README.md`（给人看）、`SKILL.md`（给 AI 看）、`templates/` 与 `assets/`，互不耦合。
- **先备后改，安全第一**：强调操作前留存快照、原子化变更与端到端闭环验收。
- **100% 脱敏开源**：全库零私有 IP、密钥、凭据与个人域名，全部通过显式占位符注入。

---

## 仓库结构

```text
easy-skills/
├── README.md                            # 技能合集总览与通用接入指南
├── CONTRIBUTING.md                      # 技能编写规范与隐私脱敏红线
├── LICENSE                              # MIT 开源许可证
├── assets/
│   └── banner.svg                       # 仓库顶部矢量横幅
└── skills/
    └── <skill-name>/                    # 每个技能独立自包含目录
        ├── README.md                    # 人类可读的架构说明、实测数据与唤醒示例
        ├── SKILL.md                     # AI Agent 标准执行规范
        ├── assets/                      # 可选：专属示意图与素材
        └── templates/                   # 可选：全量脱敏配置模板
```

---

<div align="center">
  <p>如果这里的实战技能帮您省下了反复折腾的时间，欢迎点一颗 <strong>Star</strong> 支持项目持续更新。</p>
  <sub>Made with care by <a href="https://github.com/wlaosj">wlaosj</a> · Part of the <strong>Easy</strong> Series · Licensed under <a href="LICENSE">MIT</a></sub>
</div>
