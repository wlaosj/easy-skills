# 贡献指南 (Contributing)

欢迎为 **Easy Skills** 提交新的实战 Agent 技能或改进现有模板！

## 技能目录规范

每个技能放在 `skills/<skill-name>/` 独立目录下，至少包含：

```text
skills/<skill-name>/
├── SKILL.md          # 必须包含 YAML frontmatter (name, description) 与清晰的分阶段 SOP
├── templates/        # 可选：全量脱敏配置模板
└── scripts/          # 可选：辅助校验或部署脚本
```

## 隐私与安全红线（提交前必查）

严禁在任何文件或提交历史中包含以下真实信息，请统一使用 `{{PLACEHOLDER}}` 占位符：

- 真实公网 IP、自建 VPS IP、个人宽带出口 IP
- SSH 密码、API Secret、UUID、私钥/公钥、Token
- 机场订阅链接、私人业务域名、内网设备 MAC 地址
- macOS `.DS_Store` 等系统临时文件
