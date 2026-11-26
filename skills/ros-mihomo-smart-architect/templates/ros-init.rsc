# RouterOS 7.x + Mihomo Smart 标准初始化脚本模板
# 占位符说明：
#   {{LAN_IF}}    -> LAN 物理口或网桥名 (如 bridge-lan)
#   {{WAN_IF}}    -> WAN 出口名 (如 pppoe-out1 或 ether1)
#   {{LAN_CIDR}}  -> 局域网网段 (如 192.168.88.0/24)

# ==================== 1. 容器网络与路由表 ====================
/interface/veth/add name=veth-mihomo address=172.17.0.2/24 gateway=172.17.0.1
/interface/bridge/add name=bridge-container
/interface/bridge/port/add bridge=bridge-container interface=veth-mihomo
/ip/address/add address=172.17.0.1/24 interface=bridge-container

/routing/table/add name=to-mihomo fib
/ip/route/add dst-address=198.18.0.0/16 gateway=172.17.0.2 routing-table=main comment="Route-FakeIP-to-Mihomo"
/ip/route/add dst-address=0.0.0.0/0 gateway=172.17.0.2 routing-table=to-mihomo comment="Route-to-Mihomo"

# ==================== 2. 地址列表与 CNIP 自动更新 ====================
/ip/firewall/address-list/add list=LAN_LOCAL address=192.168.0.0/16
/ip/firewall/address-list/add list=LAN_LOCAL address=10.0.0.0/8
/ip/firewall/address-list/add list=LAN_LOCAL address=172.16.0.0/12
/ip/firewall/address-list/add list=LAN_LOCAL address=127.0.0.0/8
/ip/firewall/address-list/add list=LAN_LOCAL address=224.0.0.0/4
/ip/firewall/address-list/add list=OUT_TO_MIHOMO address=raw.githubusercontent.com comment="GitHub-Raw-Proxy"

# 采用 .rsc 导入 + 文件体积 >100KB 校验，彻底规避 ROS 64KB 变量上限与空文件清空列表风险
/system/script/add name=update-cnip source={
  :log info "CNIP: Starting China IP list update...";
  :do {
    /tool/fetch check-certificate=no url="https://raw.githubusercontent.com/DMF2022/ROS-cnip-script/master/cnip.rsc" dst-path="cnip.rsc";
    :delay 2s;
    :if ([:len [/file/find name="cnip.rsc"]] > 0 and [/file/get [find name="cnip.rsc"] size] > 100000) do={
      :log info "CNIP: Download verified (>100KB), importing address list...";
      /import file-name=cnip.rsc;
      /file/remove [find name="cnip.rsc"];
      :log info "CNIP: Update completed successfully.";
    } else={
      :log error "CNIP: Download failed or file size invalid, keeping existing CNIP list.";
    }
  } on-error={
    :log warning "CNIP: Update aborted due to network error.";
  }
}
/system/scheduler/add name=schedule-cnip-update start-time=04:30:00 interval=1w on-event="/system script run update-cnip"

# ==================== 3. FastTrack 国内卸载 & Mangle 分流 ====================
# 重要：若系统已有默认全局 defconf: fasttrack，请务必先禁用它，否则海外流量会绕过 Mangle！
/ip/firewall/filter/add chain=forward action=fasttrack-connection connection-state=established,related dst-address-list=CNIP in-interface={{LAN_IF}} out-interface={{WAN_IF}} comment="FastTrack-CNIP-Direct"

/ip/firewall/mangle/add chain=output action=mark-routing new-routing-mark=to-mihomo passthrough=yes dst-address-list=OUT_TO_MIHOMO disabled=yes comment="ROS-Output-to-Mihomo"
/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=LAN_LOCAL comment="LAN-Direct"
/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=MY_INFRA_DIRECT comment="My-Infra-Direct"
/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=CNIP comment="China-IP-Direct"
/ip/firewall/mangle/add chain=prerouting action=mark-routing new-routing-mark=to-mihomo passthrough=yes src-address={{LAN_CIDR}} dst-address-type=!local src-address-list=!BYPASS_HOSTS disabled=yes comment="LAN-Route-to-Mihomo"
/ip/firewall/mangle/add chain=forward action=change-mss new-mss=clamp-to-pmtu passthrough=yes tcp-flags=syn protocol=tcp out-interface={{WAN_IF}} comment="MSS-Clamp-IPv4-Out"
/ip/firewall/mangle/add chain=forward action=change-mss new-mss=clamp-to-pmtu passthrough=yes tcp-flags=syn protocol=tcp in-interface={{WAN_IF}} comment="MSS-Clamp-IPv4-In"

# ==================== 4. 收口 NAT 与 DNS 53 劫持 ====================
/ip/firewall/nat/add chain=srcnat action=masquerade src-address=172.17.0.0/24
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=9090 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=9090 comment="Mihomo-WebUI"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7890 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7890 comment="Mihomo-Proxy-TCP"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7891 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7891 comment="Mihomo-SOCKS5"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7893 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7893 comment="Mihomo-Mixed"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7893 protocol=udp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7893 comment="Mihomo-Mixed-UDP"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=53 protocol=udp src-address={{LAN_CIDR}} src-address-list=!BYPASS_HOSTS dst-port=53 disabled=yes comment="LAN-DNS-to-Mihomo"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=53 protocol=tcp src-address={{LAN_CIDR}} src-address-list=!BYPASS_HOSTS dst-port=53 disabled=yes comment="LAN-DNS-to-Mihomo-TCP"

# ==================== 5. Phase 4 安全切流命令（待 Mihomo 9090/7893 验收通过后执行） ====================
# /ip/firewall/mangle/enable [find comment~"LAN-Route-to-Mihomo|ROS-Output-to-Mihomo"]
# /ip/firewall/nat/enable [find comment~"LAN-DNS-to-Mihomo"]
