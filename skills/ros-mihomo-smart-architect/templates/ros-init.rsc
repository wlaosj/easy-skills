# RouterOS 7.x + Mihomo Smart 标准初始化脚本模板
# 占位符说明：
#   {{LAN_IF}}    -> LAN 物理口或网桥名 (如 bridge-lan)
#   {{WAN_IF}}    -> WAN 出口名 (如 pppoe-out1 或 ether1)
#   {{LAN_CIDR}}  -> 局域网网段 (如 192.168.31.0/24)

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

/system/script/add name=update-cnip source={
  /tool/fetch url="https://raw.githubusercontent.com/mayaxcn/china-ip-list/master/chnroute.txt" dst-path=cnip.txt
  :delay 2s
  :local content [/file/get cnip.txt contents]
  :if ([:len $content] > 100000) do={
    /ip/firewall/address-list/remove [find list=CNIP]
    :local pos 0
    :while ($pos < [:len $content]) do={
      :local nl [:find $content "\n" $pos]
      :if ([:typeof $nl] = "nil") do={ :set nl [:len $content] }
      :local line [:pick $content $pos $nl]
      :if ([:len $line] > 6) do={
        /ip/firewall/address-list/add list=CNIP address=$line
      }
      :set pos ($nl + 1)
    }
    :log info "CNIP updated successfully"
  } else={
    :log error "CNIP update aborted: file too small"
  }
}
/system/scheduler/add name=schedule-cnip-update start-time=04:30:00 interval=1w on-event="/system script run update-cnip"

# ==================== 3. FastTrack 国内卸载 & Mangle 分流 ====================
/ip/firewall/filter/add chain=forward action=fasttrack-connection connection-state=established,related dst-address-list=CNIP in-interface={{LAN_IF}} out-interface={{WAN_IF}} comment="FastTrack-CNIP-Direct"

/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=LAN_LOCAL comment="LAN-Direct"
/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=MY_INFRA_DIRECT comment="My-Infra-Direct"
/ip/firewall/mangle/add chain=prerouting action=accept dst-address-list=CNIP comment="China-IP-Direct"
# 注意：确认 Mihomo 容器正常启动并验证 7893 可用后，再启用下面这行切流规则
/ip/firewall/mangle/add chain=prerouting action=mark-routing new-routing-mark=to-mihomo passthrough=yes src-address={{LAN_CIDR}} dst-address-type=!local src-address-list=!BYPASS_HOSTS comment="LAN-Route-to-Mihomo"

# ==================== 4. 收口 NAT 与 DNS 53 劫持 ====================
/ip/firewall/nat/add chain=srcnat action=masquerade src-address=172.17.0.0/24
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=9090 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=9090 comment="Mihomo-WebUI"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7893 protocol=tcp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7893 comment="Mihomo-Mixed"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=7893 protocol=udp dst-address-type=local in-interface=!{{WAN_IF}} dst-port=7893 comment="Mihomo-Mixed-UDP"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=53 protocol=udp src-address={{LAN_CIDR}} src-address-list=!BYPASS_HOSTS dst-port=53 comment="LAN-DNS-to-Mihomo"
/ip/firewall/nat/add chain=dstnat action=dst-nat to-addresses=172.17.0.2 to-ports=53 protocol=tcp src-address={{LAN_CIDR}} src-address-list=!BYPASS_HOSTS dst-port=53 comment="LAN-DNS-to-Mihomo-TCP"
