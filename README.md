<div align="center">

<img src="assets/banner.svg" alt="Easy Skills Banner" width="100%" />

<br />

[![License: MIT](https://img.shields.io/badge/License-MIT-0066CC?style=flat-square)](LICENSE)
[![Agent Compatible](https://img.shields.io/badge/Agents-Antigravity%20%7C%20Claude%20Code%20%7C%20Cursor%20%7C%20Codex-15803D?style=flat-square)](#极速上手)
[![Production Verified](https://img.shields.io/badge/Status-Battle--Tested-EA580C?style=flat-square)](#实测表现)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-334155?style=flat-square)](CONTRIBUTING.md)

<p>
  <strong>一台全新 RouterOS + 一句话 = 全自动双层智能分流网关。</strong><br />
  经过真实家庭实验室与工程环境打磨的 AI Agent 实战技能库 —— 把复杂折腾交给 AI，让架构部署变得 <strong>Easy</strong>。<br />
  <sub>Battle-tested AI Agent Skills that turn complex Homelab, RouterOS &amp; DevOps setups into effortless automated workflows.</sub>
</p>

<p>
  <a href="#技能目录">技能目录</a> ·
  <a href="#架构实景">架构实景</a> ·
  <a href="#实测表现">实测表现</a> ·
  <a href="#极速上手">极速上手</a> ·
  <a href="#设计理念">设计理念</a> ·
  <a href="#仓库结构">仓库结构</a>
</p>

</div>

---

## 技能目录

所有技能均遵循标准 `SKILL.md` 规范，内置防踩坑门禁、防断网原子校验流程与全量脱敏模板：

| 技能名称 | 领域分类 | 一句话解决什么痛点 | 适用环境 | 状态 |
| :--- | :--- | :--- | :--- | :---: |
| [`ros-mihomo-smart-architect`](skills/ros-mihomo-smart-architect/SKILL.md) | 软路由 / 网络架构 | 全新 RouterOS 7.x 一键自动部署 **CNIP 内核 FastTrack 硬件直出 + Mihomo Smart (LightGBM) 多机场混跑容器 + 防断网原子切流 + 收口 NAT** | RouterOS 7.12+ (x86 / CHR / ARM64) | **已发布** |

> 仓库持续沉淀真实环境验证过的新技能，欢迎点一颗 **Star** 关注后续更新。

---

## 架构实景

以首发旗舰技能 **`ros-mihomo-smart-architect`** 为例，AI 自动交付的「内核极速直出 + Smart AI 多线协同」双轨架构全景如下：

<div align="center">
  <img src="assets/ros-mihomo-smart-arch.jpg" alt="家庭智能双轨网络架构" width="94%" />
</div>

<br />

- **L1 内核级国内卸载**：RouterOS 每周自动更新大陆 `CNIP` 列表（带防空文件字节校验），命中流量在 Mangle 层直接放行并走 `FastTrack-CNIP-Direct` 硬件卸载，国内 4K 与大文件下载几乎 **0 CPU 占用**、不进代理容器。
- **L2 Smart AI 按站选路**：Mihomo Smart 内核加载 LightGBM 模型，为每个网站独立评估最优专线，自动把多家机场优势混跑叠加；遇到单站抽风时精准定向绕开，不误伤整条好节点。
- **双轨出口解耦**：AI 编程与核心业务可独立走自建稳态专线（零风控固定出口），日常大流量影音与海外站点交由多机场 Smart 池自动负载均衡。

---

## 实测表现

以下为该架构在真实家庭软路由环境（i3 低功耗 PVE + RouterOS CHR + 3 家机场混跑）下的脱敏实测基线：

| 累计护航请求 | 综合畅通率 | 多线协同峰值 | Mihomo 容器内存 |
| :---: | :---: | :---: | :---: |
| **450,000+ 次** | **98.2%** | **73.9 MB/s** | **~210 MiB** |

- 支持多家服务商流量自动混跑分担，告别传统 `url-test` 单线死磕、其余线路闲置吃灰。
- 单站级故障自动避坑，全屋日常免手动切节点。

---

## 极速上手

### 方式一：零安装，一句话直接甩给 AI（最推荐）

只要您的 AI 助手支持终端或联网（**Antigravity / Claude Code / Cursor / Codex / OpenClaw** 等通用），**无需手动下载或配置目录**，准备好一台已能上网并开启 SSH + `container` 权限的全新 RouterOS 7.x，直接复制下面这段话发给 AI：

```text
请拉取 https://github.com/wlaosj/easy-skills 仓库中的 ros-mihomo-smart-architect 技能，
严格按照里面的 SKILL.md 与 templates 模板，帮我在这台全新 RouterOS 上部署双层智能分流架构：

- RouterOS 地址：192.168.x.x（SSH 账号：admin，密码：xxxxxx）
- WAN 口名称：pppoe-out1，LAN 网段：192.168.x.0/24
- 机场订阅链接：https://你的订阅链接

要求：严格遵循先备份、先起容器验通 9090/7893、最后切 Mangle 与 DNS 的防断网顺序，完成后输出端到端验收结果。
```

### 方式二：安装到本地技能目录（一次安装，永久自动识别）

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

安装完成后重启或新开会话，直接告诉 AI“使用 `ros-mihomo-smart-architect` 帮我部署 RouterOS”即可自动触发。

</details>

---

## 设计理念

- **拒绝“玩具提示词”**：每一个 Skill 都源于真实 7×24 运行的生产/家庭环境，把踩过的真实大坑（CNIP 空文件清空列表、NAT 未收口误劫持外部同端口、抖音直连规则截胡定位规则、未验容器先切路由导致断网死锁）全部固化为强制检查门禁。
- **先备后改，安全兜底**：强制先做完整配置备份，再执行原子化校验与上线。
- **100% 脱敏开源**：全库不含任何私有 IP、密码、订阅链接与个人域名，所有参数通过占位符动态注入。

---

## 仓库结构

```text
easy-skills/
├── README.md                                     # 项目总览与极速上手指南
├── CONTRIBUTING.md                               # 技能编写规范与隐私脱敏红线
├── LICENSE                                       # MIT 开源许可证
├── assets/
│   ├── banner.svg                                # 顶部极简矢量横幅
│   └── ros-mihomo-smart-arch.jpg                 # 双轨分流架构示意图
└── skills/
    └── ros-mihomo-smart-architect/
        ├── SKILL.md                              # AI Agent 标准化执行手册
        └── templates/
            ├── mihomo-smart-config.yaml          # Mihomo Smart 脱敏配置模板
            └── ros-init.rsc                      # RouterOS 7.x 初始化脚本模板
```

---

<div align="center">
  <p>如果这套 Skill 帮您省下了反复排障的时间，欢迎点一颗 <strong>Star</strong> 支持项目持续更新。</p>
  <sub>Made with care by <a href="https://github.com/wlaosj">wlaosj</a> · Part of the <strong>Easy</strong> Series · Licensed under <a href="LICENSE">MIT</a></sub>
</div>
