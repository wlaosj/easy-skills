<div align="center">

<img src="assets/banner.svg" alt="Easy Skills Banner" width="100%" />

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-0066CC?style=flat-square)](LICENSE)
[![Agent Compatible](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-15803D?style=flat-square)](#一句话极速上手)
[![Production Verified](https://img.shields.io/badge/Status-Battle--Tested-EA580C?style=flat-square)](#技能目录)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-334155?style=flat-square)](CONTRIBUTING.md)

<p>
  <strong>把复杂折腾交给 AI，让一切变得 Easy。</strong><br />
  无需手动安装、无需东拼西凑教程 —— 直接把链接发给你的 AI，一键复刻真实环境验证过的完整方案。<br />
  <sub>Zero manual setup. Just hand a skill link to your AI agent and let it execute battle-tested workflows end to end.</sub>
</p>

<p>
  <a href="#技能目录">技能目录</a> ·
  <a href="#一句话极速上手">一句话上手</a> ·
  <a href="#为什么选-easy-skills">为什么选 Easy Skills</a> ·
  <a href="#仓库结构">仓库结构</a>
</p>

</div>

---

## 技能目录

点击技能名称进入独立主页，查看对应的**架构图、实测表现与专属唤醒词**：

| 技能名称 | 分类 | 一句话说明 | 详情 |
| :--- | :--- | :--- | :---: |
| [`ros-mihomo-smart-architect`](skills/ros-mihomo-smart-architect/) | 软路由 / 网络 | 全新 RouterOS 7.x 一键部署 CNIP 硬件直出 + Mihomo Smart (LightGBM) 多机场混跑与防断网校验 | [进入主页](skills/ros-mihomo-smart-architect/) |

> 仓库持续沉淀真实环境打磨出的高质量技能，欢迎点一颗 **Star** 关注后续更新。

---

## 一句话极速上手

无需手动克隆或配置本地目录 —— 只要你的 AI 助手支持终端或联网（**Antigravity / Claude Code / Cursor / Codex / OpenClaw** 等通用），直接复制下面这句话发给它即可：

```text
请拉取 https://github.com/wlaosj/easy-skills 仓库中的 <技能名称> 技能，
完整阅读对应目录下的 SKILL.md 与模板文件，严格按照里面的安全规范与校验步骤帮我执行。
```

> 如需长期常驻复用，补一句 **“顺便帮我安装到本地 skills 目录”**，AI 会自动帮你放好。

---

## 为什么选 Easy Skills

- **极致 Easy，零门槛**：不用折腾命令行与目录结构，一句话把整套专业手艺直接交给 AI。
- **真刀真枪，拒绝玩具**：每个 Skill 均提炼自 7×24 运行的真实环境，内置备份兜底与防踩坑门禁。
- **高内聚、全脱敏**：每个技能独立自包含，全库零私有 IP、密钥与个人域名，开箱放心用。

---

## 仓库结构

```text
easy-skills/
├── README.md                            # 总览与一句话上手指南
├── CONTRIBUTING.md                      # 贡献与隐私脱敏规范
├── LICENSE                              # MIT 开源许可证
├── assets/banner.svg                    # 顶部品牌横幅
└── skills/
    └── <skill-name>/                    # 每个技能独立自包含
        ├── README.md                    # 架构图、实测效果与专属提示词
        ├── SKILL.md                     # AI Agent 标准化执行手册
        ├── assets/                      # 专属图示素材
        └── templates/                   # 全量脱敏配置模板
```

---

<div align="center">
  <p>如果这里的技能帮您省下了反复折腾的时间，欢迎点一颗 <strong>Star</strong> 支持持续更新。</p>
  <sub>Made with care by <a href="https://github.com/wlaosj">wlaosj</a> · Part of the <strong>Easy</strong> Series · Licensed under <a href="LICENSE">MIT</a></sub>
</div>
