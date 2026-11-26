# ==============================================================================
# RouterOS 7.x — PS4 防误升网络硬隔离模板 (脱敏)
# 说明：
#   1. 先为 PS4 的 Wi-Fi 与 LAN 两个 MAC 分配固定内网 IP
#   2. 将固定 IP 加入地址列表 PS4_ISOLATED
#   3. 在 forward 链最前部插入 DROP 规则，彻底拦截全部出外网流量（不拦截局域网通信）
# 使用前请将所有 {{PLACEHOLDER}} 替换为实际环境参数
# ==============================================================================

# 1. 静态 DHCP 租约（按需保留 Wi-Fi / LAN 一条或两条）
/ip/dhcp-server/lease/add \
    address={{PS4_WIFI_IP}} \
    mac-address={{PS4_WIFI_MAC}} \
    server={{DHCP_SERVER_NAME}} \
    comment="PS4-WiFi-Isolated"

/ip/dhcp-server/lease/add \
    address={{PS4_LAN_IP}} \
    mac-address={{PS4_LAN_MAC}} \
    server={{DHCP_SERVER_NAME}} \
    comment="PS4-LAN-Isolated"

# 2. 隔离地址列表
/ip/firewall/address-list/add list=PS4_ISOLATED address={{PS4_WIFI_IP}} comment="PS4-WiFi"
/ip/firewall/address-list/add list=PS4_ISOLATED address={{PS4_LAN_IP}} comment="PS4-LAN"

# 3. 拦截 PS4 发往外网的全部转发流量（务必置于 FastTrack 与常规放行规则之前）
# 注意：若您的外网接口列表名称不是 WAN，请将 out-interface-list=WAN 替换为实际接口或列表名
/ip/firewall/filter/add \
    chain=forward \
    action=drop \
    src-address-list=PS4_ISOLATED \
    out-interface-list={{WAN_INTERFACE_LIST}} \
    place-before=0 \
    comment="PS4-Block-WAN-Update"

# 4. （可选）若局域网启用了 IPv6，建议同步按 MAC 或关闭对应网段 SLAAC，防止 IPv6 逃逸
# /ipv6/firewall/filter/add chain=forward action=drop src-mac-address={{PS4_WIFI_MAC}} out-interface-list={{WAN_INTERFACE_LIST}} place-before=0 comment="PS4-Block-WAN-IPv6-WiFi"
# /ipv6/firewall/filter/add chain=forward action=drop src-mac-address={{PS4_LAN_MAC}} out-interface-list={{WAN_INTERFACE_LIST}} place-before=0 comment="PS4-Block-WAN-IPv6-LAN"
