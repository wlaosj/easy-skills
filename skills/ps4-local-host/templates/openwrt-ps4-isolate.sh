#!/bin/sh
# ==============================================================================
# OpenWrt — PS4 防误升网络硬隔离脚本模板 (脱敏)
# 说明：通过 UCI 为 PS4 绑定静态 IP 并禁止其从 lan 转发至 wan（保留局域网互访）
# 使用前请将所有 {{PLACEHOLDER}} 替换为实际参数
# ==============================================================================
set -e

# 1. DHCP 静态绑定（Wi-Fi 与 LAN 按需保留）
uci add dhcp host
uci set dhcp.@host[-1].name='ps4-wifi'
uci set dhcp.@host[-1].mac='{{PS4_WIFI_MAC}}'
uci set dhcp.@host[-1].ip='{{PS4_WIFI_IP}}'

uci add dhcp host
uci set dhcp.@host[-1].name='ps4-lan'
uci set dhcp.@host[-1].mac='{{PS4_LAN_MAC}}'
uci set dhcp.@host[-1].ip='{{PS4_LAN_IP}}'
uci commit dhcp

# 2. 防火墙禁止 PS4 访问 WAN（含 IPv4 / IPv6）
uci add firewall rule
uci set firewall.@rule[-1].name='Block-PS4-WAN'
uci set firewall.@rule[-1].src='lan'
uci set firewall.@rule[-1].dest='wan'
uci add_list firewall.@rule[-1].src_mac='{{PS4_WIFI_MAC}}'
uci add_list firewall.@rule[-1].src_mac='{{PS4_LAN_MAC}}'
uci set firewall.@rule[-1].proto='all'
uci set firewall.@rule[-1].target='DROP'
uci commit firewall

# 3. 重载服务生效
/etc/init.d/dnsmasq restart
/etc/init.d/firewall reload

echo "PS4 WAN isolation rules applied."
