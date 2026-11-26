import json
import os
import re
import struct
import time
from collections import defaultdict

# Strip Unicode emojis/flags from node display names to keep UI 100% emoji-free
_EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def clean_name(text: str) -> str:
    cleaned = _EMOJI_RE.sub("", text or "")
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return cleaned


_TARGET_META = {
    "GeoSite [youtube]": ("YouTube 视频", "影音", 100),
    "*.youtube.com": ("YouTube 网页端", "影音", 90),
    "*.googlevideo.com": ("YouTube 视频流", "影音", 90),
    "RuleSet [Streaming]": ("国际流媒体", "影音", 98),
    "GeoSite [google]": ("Google 核心服务", "搜索", 96),
    "*.google.com": ("Google 主站", "搜索", 88),
    "*.gstatic.com": ("Google 静态加速", "搜索", 70),
    "*.clients6.google.com": ("Google 静态加速", "搜索", 70),
    "RuleSet [Proxy]": ("海外综合网站", "通用", 95),
    "GeoSite [telegram]": ("Telegram 即时通讯", "通讯", 94),
    "*.telegram.org": ("Telegram 网页服务", "通讯", 85),
    "RuleSet [TelegramIP]": ("Telegram 媒体传输", "通讯", 92),
    "GeoSite [github]": ("GitHub 代码托管", "开发", 91),
    "GeoSite [tiktok]": ("TikTok 短视频", "影音", 89),
    "*.twitch.tv": ("Twitch 游戏直播", "影音", 86),
    "*.ttvnw.net": ("Twitch 游戏直播", "影音", 86),
    "DomainSuffix [play.googleapis.com]": ("Google Play 商店", "应用", 82),
    "DomainSuffix [storage.googleapis.com]": ("Google 云存储", "云服务", 80),
    "DomainSuffix [optimizationguide-pa.googleapis.com]": ("Chrome 智能组件", "服务", 75),
    "DomainSuffix [fonts.googleapis.com]": ("Google 字体服务", "网页", 72),
    "*.cloudflare-dns.com": ("Cloudflare 安全解析", "网络", 78),
    "1.1.1.1": ("Cloudflare 安全解析", "网络", 78),
    "*.dns.google": ("Google 公共解析", "网络", 76),
    "*.brew.sh": ("Homebrew 软件源", "开发", 74),
    "*.proxmox.com": ("Proxmox 虚拟化源", "运维", 73),
}

_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}(?:/\d{1,2})?$")


def humanize_target(target: str) -> tuple[str, str, int]:
    raw = (target or "").strip()
    if raw in _TARGET_META:
        return _TARGET_META[raw]

    no_proto = raw[4:].strip() if raw.startswith("udp|") else raw
    if no_proto in _TARGET_META:
        return _TARGET_META[no_proto]

    cleaned = no_proto
    category = "域名"
    for prefix, cat in (
        ("GeoSite [", "规则"),
        ("RuleSet [", "规则"),
        ("DomainSuffix [", "域名"),
        ("IPCIDR [", "网络"),
    ):
        if cleaned.startswith(prefix) and cleaned.endswith("]"):
            cleaned = cleaned[len(prefix) : -1].strip()
            category = cat
            break

    if cleaned.startswith("*."):
        cleaned = cleaned[2:]
    if _IPV4_RE.match(cleaned):
        category = "节点IP" if category == "域名" else category

    return (cleaned or raw, category, 40)


def _weight_to_score(raw_weight: float) -> int:
    if not raw_weight or raw_weight <= 0:
        return 0
    capped = min(float(raw_weight), 1.25)
    return min(99, max(35, round((capped / 1.25) * 99)))


def _parse_bbolt_entries(data: bytes):
    """Pure-Python read-only bbolt parser returning dict[bucket_path -> list[(key, val_bytes)]]."""
    if len(data) < 4096:
        raise ValueError("Database file too small or invalid")

    page_size = struct.unpack("<I", data[16 + 8 : 16 + 12])[0]
    if page_size not in (4096, 8192, 16384, 32768, 65536):
        page_size = 4096

    m0 = data[16 : 16 + 64]
    m1 = data[page_size + 16 : page_size + 16 + 64]
    tx0 = struct.unpack("<Q", m0[48:56])[0]
    tx1 = struct.unpack("<Q", m1[48:56])[0]
    meta = m0 if tx0 >= tx1 else m1
    root_pgid = struct.unpack("<Q", meta[16:24])[0]

    buckets = defaultdict(list)

    def walk_inline(page_bytes: bytes, bucket_name: str):
        if len(page_bytes) < 16:
            return
        flags, count = struct.unpack("<HH", page_bytes[8:12])
        if not (flags & 0x02):
            return
        for i in range(count):
            off = 16 + i * 16
            if off + 16 > len(page_bytes):
                break
            lf, pos, ks, vs = struct.unpack("<IIII", page_bytes[off : off + 16])
            kstart = off + pos
            k = page_bytes[kstart : kstart + ks].decode("utf-8", errors="replace")
            v = page_bytes[kstart + ks : kstart + ks + vs]
            if lf & 0x01:
                sub = struct.unpack("<Q", v[0:8])[0]
                sub_name = f"{bucket_name}/{k}" if bucket_name else k
                if sub != 0:
                    walk_page(sub, sub_name)
                elif len(v) > 16:
                    walk_inline(v[16:], sub_name)
            else:
                buckets[bucket_name].append((k, v))

    def walk_page(pgid: int, bucket_name: str):
        start = pgid * page_size
        if start + 16 > len(data):
            return
        flags, count, overflow = struct.unpack("<HHI", data[start + 8 : start + 16])
        end = start + (1 + overflow) * page_size
        if end > len(data):
            return
        p = data[start:end]
        if flags & 0x01:  # branch
            for i in range(count):
                off = 16 + i * 16
                if off + 16 > len(p):
                    break
                _, _, child_pgid = struct.unpack("<IIQ", p[off : off + 16])
                walk_page(child_pgid, bucket_name)
        elif flags & 0x02:  # leaf
            for i in range(count):
                off = 16 + i * 16
                if off + 16 > len(p):
                    break
                lf, pos, ks, vs = struct.unpack("<IIII", p[off : off + 16])
                kstart = off + pos
                k = p[kstart : kstart + ks].decode("utf-8", errors="replace")
                v = p[kstart + ks : kstart + ks + vs]
                if lf & 0x01:
                    sub = struct.unpack("<Q", v[0:8])[0]
                    sub_name = f"{bucket_name}/{k}" if bucket_name else k
                    if sub != 0:
                        walk_page(sub, sub_name)
                    elif len(v) > 16:
                        walk_inline(v[16:], sub_name)
                else:
                    buckets[bucket_name].append((k, v))

    walk_page(root_pgid, "")
    return buckets, max(tx0, tx1)


def parse_cache_db(db_path: str) -> dict:
    """Parse Mihomo Smart cache.db into comprehensive visualization-ready JSON."""
    now_ts = int(time.time())
    file_size = os.path.getsize(db_path)
    mtime = int(os.path.getmtime(db_path))

    with open(db_path, "rb") as f:
        raw = f.read()

    buckets, txid = _parse_bbolt_entries(raw)

    # 1. Selected proxy choices
    selected = {}
    for k, v in buckets.get("selected", []):
        val = clean_name(v.decode("utf-8", errors="replace"))
        if val:
            selected[clean_name(k)] = val

    # 2. Subscription info
    subscriptions = []
    for k, v in buckets.get("subscriptioninfo", []):
        raw_str = v.decode("utf-8", errors="replace")
        kv = {}
        for part in raw_str.split(";"):
            part = part.strip()
            if "=" in part:
                pk, pv = part.split("=", 1)
                kv[pk.strip().lower()] = pv.strip()
        up = int(kv.get("upload") or 0)
        down = int(kv.get("download") or 0)
        total = int(kv.get("total") or 0)
        expire = int(kv.get("expire") or 0)
        used = up + down
        pct = round((used / total) * 100, 2) if total > 0 else 0.0
        sub_name = clean_name(k)
        subscriptions.append(
            {
                "name": sub_name,
                "is_legacy": sub_name.endswith("_链式"),
                "upload_gb": round(up / (1024**3), 2),
                "download_gb": round(down / (1024**3), 2),
                "used_gb": round(used / (1024**3), 2),
                "total_gb": round(total / (1024**3), 2),
                "remaining_gb": round(max(total - used, 0) / (1024**3), 2),
                "percent": min(pct, 100.0),
                "expire": expire,
            }
        )
    subscriptions.sort(key=lambda x: x["name"])

    # 3. Smart stats bucket
    rankings = []
    prefetch_list = []
    stats_detail = []
    node_states = []
    failures = []
    groups_set = set()

    # Aggregation per (group, node)
    agg = {}

    for k, v in buckets.get("smart_stats", []):
        try:
            obj = json.loads(v.decode("utf-8", errors="replace"))
        except Exception:
            continue

        parts = k.split("/")
        if len(parts) < 4 or parts[0] != "smart":
            continue

        kind = parts[1]
        group = clean_name(parts[3])
        if group:
            groups_set.add(group)

        if kind == "ranking":
            items = []
            for item in obj.get("result") or []:
                items.append(
                    {
                        "node": clean_name(item.get("Name", "")),
                        "rank": item.get("Rank", ""),
                        "weight": item.get("Weight", 0),
                    }
                )
            rankings.append(
                {
                    "group": group,
                    "last_updated": obj.get("last_updated", 0),
                    "items": items,
                }
            )

        elif kind == "prefetch" and len(parts) >= 5:
            target = "/".join(parts[4:])
            tcp_obj = obj.get("tcp") or {}
            udp_obj = obj.get("udp") or {}
            tcp_nodes = tcp_obj.get("nodes") or []
            tcp_weights = tcp_obj.get("weights") or []
            udp_nodes = udp_obj.get("nodes") or []
            udp_weights = udp_obj.get("weights") or []

            tcp_pairs = [
                {"node": clean_name(n), "weight": round(float(w), 4)}
                for n, w in zip(tcp_nodes, tcp_weights)
            ]
            udp_pairs = [
                {"node": clean_name(n), "weight": round(float(w), 4)}
                for n, w in zip(udp_nodes, udp_weights)
            ]
            if tcp_pairs or udp_pairs:
                prefetch_list.append(
                    {
                        "group": group,
                        "target": target,
                        "tcp": tcp_pairs,
                        "udp": udp_pairs,
                    }
                )

        elif kind == "stats" and len(parts) >= 6:
            node = clean_name(parts[-1])
            target = "/".join(parts[4:-1])
            success = int(obj.get("success") or 0)
            failure = int(obj.get("failure") or 0)
            connect_time = float(obj.get("connect_time") or 0)
            latency = float(obj.get("latency") or 0)
            last_used = int(obj.get("last_used") or 0)
            weights = obj.get("weights") or {}
            w_tcp = round(float(weights.get("tcp") or 0), 4)
            w_udp = round(float(weights.get("udp") or 0), 4)
            up_mb = round(float(obj.get("upload_total") or 0), 3)
            down_mb = round(float(obj.get("download_total") or 0), 3)
            max_up = round(float(obj.get("max_upload_rate") or 0), 2)
            max_down = round(float(obj.get("max_download_rate") or 0), 2)
            duration = round(float(obj.get("connection_duration") or 0), 2)
            total_req = success + failure
            sr = round((success / total_req) * 100, 1) if total_req > 0 else 0.0

            stats_detail.append(
                {
                    "group": group,
                    "target": target,
                    "node": node,
                    "success": success,
                    "failure": failure,
                    "success_rate": sr,
                    "connect_time": round(connect_time, 1),
                    "latency": round(latency, 1),
                    "weight_tcp": w_tcp,
                    "weight_udp": w_udp,
                    "upload_mb": up_mb,
                    "download_mb": down_mb,
                    "max_upload_rate": max_up,
                    "max_download_rate": max_down,
                    "duration": duration,
                    "last_used": last_used,
                }
            )

            akey = (group, node)
            if akey not in agg:
                agg[akey] = {
                    "group": group,
                    "node": node,
                    "success": 0,
                    "failure": 0,
                    "targets": set(),
                    "connect_sum": 0.0,
                    "connect_cnt": 0,
                    "latency_sum": 0.0,
                    "latency_cnt": 0,
                    "tcp_weights": [],
                    "udp_weights": [],
                    "upload_mb": 0.0,
                    "download_mb": 0.0,
                    "max_download_rate": 0.0,
                    "max_upload_rate": 0.0,
                    "last_used": 0,
                    "blocked_until": 0,
                    "threshold_grade": 0,
                }
            a = agg[akey]
            a["success"] += success
            a["failure"] += failure
            a["targets"].add(target)
            if connect_time > 0:
                a["connect_sum"] += connect_time
                a["connect_cnt"] += 1
            if 0 < latency < 10000:
                a["latency_sum"] += latency
                a["latency_cnt"] += 1
            if w_tcp > 0:
                a["tcp_weights"].append(w_tcp)
            if w_udp > 0:
                a["udp_weights"].append(w_udp)
            a["upload_mb"] += up_mb
            a["download_mb"] += down_mb
            if max_down > a["max_download_rate"]:
                a["max_download_rate"] = max_down
            if max_up > a["max_upload_rate"]:
                a["max_upload_rate"] = max_up
            if last_used > a["last_used"]:
                a["last_used"] = last_used

        elif kind == "node" and len(parts) >= 5:
            node = clean_name(obj.get("name") or "/".join(parts[4:]))
            blocked_until = int(obj.get("blocked_until") or 0)
            grade = int(obj.get("threshold_grade") or 0)
            last_checked = int(obj.get("last_checked") or 0)
            is_blocked = blocked_until > now_ts
            node_states.append(
                {
                    "group": group,
                    "node": node,
                    "last_checked": last_checked,
                    "blocked_until": blocked_until,
                    "is_blocked": is_blocked,
                    "cooldown_sec": max(blocked_until - now_ts, 0),
                    "threshold_grade": grade,
                }
            )

        elif kind == "failures" and len(parts) >= 5:
            target = "/".join(parts[4:])
            blocked_nodes = []
            fail_counts = []
            codes = obj.get("codes") or {}
            for code_key, code_val in codes.items():
                if not isinstance(code_val, dict):
                    continue
                for n_name, until_ts in (code_val.get("nodes") or {}).items():
                    until_i = int(until_ts or 0)
                    blocked_nodes.append(
                        {
                            "node": clean_name(n_name),
                            "code": str(code_key),
                            "until": until_i,
                            "active": until_i > now_ts,
                            "remaining_sec": max(until_i - now_ts, 0),
                        }
                    )
                for n_name, cnt in (code_val.get("fail_counts") or {}).items():
                    fail_counts.append(
                        {
                            "node": clean_name(n_name),
                            "code": str(code_key),
                            "count": int(cnt or 0),
                        }
                    )
            f_label, f_cat, _ = humanize_target(target)
            active_list = [b for b in blocked_nodes if b["active"]]
            failures.append(
                {
                    "group": group,
                    "target": target,
                    "label": f_label,
                    "category": f_cat,
                    "blocked": bool(obj.get("blocked", False)),
                    "last_failure": int(obj.get("last_failure") or 0),
                    "last_check": int(obj.get("last_check") or 0),
                    "active_count": len(active_list),
                    "max_remaining_sec": max((b["remaining_sec"] for b in active_list), default=0),
                    "blocked_nodes": blocked_nodes,
                    "fail_counts": fail_counts,
                }
            )

    # Merge node_states into agg
    state_map = {(s["group"], s["node"]): s for s in node_states}
    node_aggregates = []
    total_success = 0
    total_failure = 0
    total_download_mb = 0.0
    total_upload_mb = 0.0

    for akey, a in agg.items():
        st = state_map.get(akey)
        blocked_until = st["blocked_until"] if st else 0
        grade = st["threshold_grade"] if st else 0
        req_tot = a["success"] + a["failure"]
        sr = round((a["success"] / req_tot) * 100, 1) if req_tot > 0 else 0.0
        avg_conn = round(a["connect_sum"] / a["connect_cnt"], 1) if a["connect_cnt"] else 0.0
        avg_lat = round(a["latency_sum"] / a["latency_cnt"], 1) if a["latency_cnt"] else 0.0
        avg_tcp_w = round(sum(a["tcp_weights"]) / len(a["tcp_weights"]), 4) if a["tcp_weights"] else 0.0
        avg_udp_w = round(sum(a["udp_weights"]) / len(a["udp_weights"]), 4) if a["udp_weights"] else 0.0

        total_success += a["success"]
        total_failure += a["failure"]
        total_download_mb += a["download_mb"]
        total_upload_mb += a["upload_mb"]

        node_aggregates.append(
            {
                "group": a["group"],
                "node": a["node"],
                "success": a["success"],
                "failure": a["failure"],
                "total_requests": req_tot,
                "success_rate": sr,
                "target_count": len(a["targets"]),
                "avg_connect_ms": avg_conn,
                "avg_latency_ms": avg_lat,
                "avg_tcp_weight": avg_tcp_w,
                "avg_udp_weight": avg_udp_w,
                "score_100": _weight_to_score(max(avg_tcp_w, avg_udp_w)),
                "download_mb": round(a["download_mb"], 2),
                "upload_mb": round(a["upload_mb"], 2),
                "max_download_rate": round(a["max_download_rate"], 2),
                "peak_mbs": round(a["max_download_rate"] / 1024, 1),
                "max_upload_rate": round(a["max_upload_rate"], 2),
                "last_used": a["last_used"],
                "is_blocked": blocked_until > now_ts,
                "blocked_until": blocked_until,
                "threshold_grade": grade,
            }
        )

    node_aggregates.sort(key=lambda x: (x["avg_tcp_weight"], x["success"]), reverse=True)
    stats_detail.sort(key=lambda x: x["last_used"], reverse=True)
    prefetch_list.sort(key=lambda x: (x["group"], x["target"]))
    failures.sort(
        key=lambda x: (x["active_count"] > 0, x["active_count"], x["blocked"], x["last_failure"]),
        reverse=True,
    )
    node_states.sort(key=lambda x: (x["is_blocked"], x["threshold_grade"], x["last_checked"]), reverse=True)
    rankings.sort(key=lambda x: x["group"])

    # Build beginner-friendly site_showcase merging prefetch + stats_detail + active failures
    active_block_map = {(f["group"], f["target"]): f["active_count"] for f in failures}
    showcase_sites = {}

    def _ensure_site(grp: str, tgt: str):
        skey = (grp, tgt)
        if skey not in showcase_sites:
            lbl, cat, prio = humanize_target(tgt)
            showcase_sites[skey] = {
                "group": grp,
                "target": tgt,
                "label": lbl,
                "category": cat,
                "priority": prio,
                "total_success": 0,
                "total_failure": 0,
                "total_download_mb": 0.0,
                "active_blocked_count": active_block_map.get(skey, 0),
                "cand_map": {},
            }
        return showcase_sites[skey]

    def _ensure_cand(site_entry: dict, node_name: str):
        cmap = site_entry["cand_map"]
        if node_name not in cmap:
            cmap[node_name] = {
                "node": node_name,
                "prefetch_tcp": 0.0,
                "prefetch_udp": 0.0,
                "stat_w_tcp": 0.0,
                "stat_w_udp": 0.0,
                "success": 0,
                "failure": 0,
                "download_mb": 0.0,
                "max_download_rate": 0.0,
            }
        return cmap[node_name]

    for p in prefetch_list:
        s_entry = _ensure_site(p["group"], p["target"])
        for pair in p["tcp"]:
            if not pair["node"]:
                continue
            c = _ensure_cand(s_entry, pair["node"])
            if pair["weight"] > c["prefetch_tcp"]:
                c["prefetch_tcp"] = pair["weight"]
        for pair in p["udp"]:
            if not pair["node"]:
                continue
            c = _ensure_cand(s_entry, pair["node"])
            if pair["weight"] > c["prefetch_udp"]:
                c["prefetch_udp"] = pair["weight"]

    for st in stats_detail:
        if not st["node"]:
            continue
        s_entry = _ensure_site(st["group"], st["target"])
        s_entry["total_success"] += st["success"]
        s_entry["total_failure"] += st["failure"]
        s_entry["total_download_mb"] += st["download_mb"]
        c = _ensure_cand(s_entry, st["node"])
        c["success"] += st["success"]
        c["failure"] += st["failure"]
        c["download_mb"] += st["download_mb"]
        if st["max_download_rate"] > c["max_download_rate"]:
            c["max_download_rate"] = st["max_download_rate"]
        if st["weight_tcp"] > c["stat_w_tcp"]:
            c["stat_w_tcp"] = st["weight_tcp"]
        if st["weight_udp"] > c["stat_w_udp"]:
            c["stat_w_udp"] = st["weight_udp"]

    # Helper for ecosystem-level active blocked node union (e.g. GeoSite [youtube] -> *.googlevideo.com + *.youtube.com)
    eco_related = {
        "GeoSite [youtube]": ("*.youtube.com", "*.googlevideo.com", "GeoSite [youtube]"),
        "GeoSite [google]": ("*.google.com", "*.googleapis.com", "*.gstatic.com", "GeoSite [google]"),
        "GeoSite [telegram]": ("*.telegram.org", "GeoSite [telegram]"),
        "RuleSet [TelegramIP]": ("91.108.56.127", "RuleSet [TelegramIP]"),
    }
    fail_active_nodes_map = {}
    for f in failures:
        fset = {b["node"] for b in f["blocked_nodes"] if b["active"]}
        if fset:
            fail_active_nodes_map[(f["group"], f["target"])] = fset

    def _effective_avoid_count(grp: str, tgt: str) -> int:
        if tgt in eco_related:
            union_nodes = set()
            for rel_t in eco_related[tgt]:
                union_nodes |= fail_active_nodes_map.get((grp, rel_t), set())
            return len(union_nodes)
        return len(fail_active_nodes_map.get((grp, tgt), set()))

    _PROV_PREFIX_RE = re.compile(r"^\s*[\[【（(]([^\]】）)]{1,16})[\]】）)]")

    def _detect_provider(node_name: str) -> str:
        m = _PROV_PREFIX_RE.match(node_name or "")
        if m:
            tag = m.group(1).strip()
            if tag:
                return tag
        return "其他"

    site_showcase = []
    for s_entry in showcase_sites.values():
        cands = []
        for c in s_entry["cand_map"].values():
            w_tcp = round(max(c["prefetch_tcp"], c["stat_w_tcp"]), 4)
            w_udp = round(max(c["prefetch_udp"], c["stat_w_udp"]), 4)
            raw_w = round(max(w_tcp, w_udp), 4)
            tot_c = c["success"] + c["failure"]
            c_sr = round((c["success"] / tot_c) * 100, 1) if tot_c > 0 else 0.0
            cands.append(
                {
                    "node": c["node"],
                    "provider": _detect_provider(c["node"]),
                    "raw_weight": raw_w,
                    "weight_tcp": w_tcp,
                    "weight_udp": w_udp,
                    "score_100": _weight_to_score(raw_w),
                    "success": c["success"],
                    "failure": c["failure"],
                    "success_rate": c_sr,
                    "download_mb": round(c["download_mb"], 2),
                    "max_download_rate": round(c["max_download_rate"], 2),
                }
            )
        cands.sort(key=lambda x: (x["raw_weight"], x["success"]), reverse=True)
        if not cands:
            continue
        site_tot = s_entry["total_success"] + s_entry["total_failure"]
        site_sr = round((s_entry["total_success"] / site_tot) * 100, 1) if site_tot > 0 else 100.0
        eff_avoid = _effective_avoid_count(s_entry["group"], s_entry["target"])
        site_showcase.append(
            {
                "group": s_entry["group"],
                "target": s_entry["target"],
                "label": s_entry["label"],
                "category": s_entry["category"],
                "priority": s_entry["priority"],
                "total_success": s_entry["total_success"],
                "total_failure": s_entry["total_failure"],
                "success_rate": site_sr,
                "total_download_mb": round(s_entry["total_download_mb"], 2),
                "active_blocked_count": s_entry["active_blocked_count"],
                "effective_blocked_count": max(s_entry["active_blocked_count"], eff_avoid),
                "candidate_count": len(cands),
                "candidates": cands[:6],
            }
        )

    site_showcase.sort(
        key=lambda x: (
            x["priority"] >= 80,
            x["total_success"] + x["total_download_mb"] * 5,
            x["priority"],
            len(x["candidates"]),
        ),
        reverse=True,
    )

    # Provider collaboration breakdown (3 airports working together)
    prov_agg = {}
    for a in node_aggregates:
        ptag = _detect_provider(a["node"])
        if ptag not in prov_agg:
            prov_agg[ptag] = {
                "tag": ptag,
                "name": f"{ptag}专线" if ptag != "其他" else "其他专线",
                "requests": 0,
                "success": 0,
                "failure": 0,
                "download_mb": 0.0,
                "active_nodes": 0,
                "peak_mbs": 0.0,
            }
        pa = prov_agg[ptag]
        pa["requests"] += a["total_requests"]
        pa["success"] += a["success"]
        pa["failure"] += a["failure"]
        pa["download_mb"] += a["download_mb"]
        pa["active_nodes"] += 1
        if a["peak_mbs"] > pa["peak_mbs"]:
            pa["peak_mbs"] = a["peak_mbs"]

    total_prov_reqs = sum(p["requests"] for p in prov_agg.values()) or 1
    total_prov_dl = sum(p["download_mb"] for p in prov_agg.values()) or 1.0
    provider_mix = []
    for pa in prov_agg.values():
        tot_p = pa["success"] + pa["failure"]
        provider_mix.append(
            {
                "tag": pa["tag"],
                "name": pa["name"],
                "requests": pa["requests"],
                "req_pct": round((pa["requests"] / total_prov_reqs) * 100, 1),
                "download_mb": round(pa["download_mb"], 2),
                "dl_pct": round((pa["download_mb"] / total_prov_dl) * 100, 1),
                "active_nodes": pa["active_nodes"],
                "peak_mbs": round(pa["peak_mbs"], 1),
                "success_rate": round((pa["success"] / tot_p) * 100, 1) if tot_p > 0 else 100.0,
            }
        )
    provider_mix.sort(key=lambda x: x["requests"], reverse=True)

    # Curated deduplicated flow routes (5 distinct recognizable sites for visual routing map)
    flow_routes = []
    seen_labels = set()
    for item in site_showcase:
        lbl = item["label"]
        if lbl in seen_labels or not item["candidates"]:
            continue
        seen_labels.add(lbl)
        top1 = item["candidates"][0]
        flow_routes.append(
            {
                "label": lbl,
                "category": item["category"],
                "group": item["group"],
                "total_success": item["total_success"],
                "total_download_mb": item["total_download_mb"],
                "success_rate": item["success_rate"],
                "effective_blocked_count": item["effective_blocked_count"],
                "candidate_count": item["candidate_count"],
                "top_node": top1["node"],
                "top_provider": top1["provider"],
                "top_score": top1["score_100"],
            }
        )
        if len(flow_routes) >= 5:
            break

    total_reqs = total_success + total_failure
    overall_sr = round((total_success / total_reqs) * 100, 2) if total_reqs > 0 else 100.0
    active_blocked_nodes = sum(1 for s in node_states if s["is_blocked"])
    degraded_nodes = sum(1 for s in node_states if s["threshold_grade"] > 1)
    active_site_blocks = sum(f["active_count"] for f in failures)
    active_failure_targets = sum(1 for f in failures if f["active_count"] > 0)
    peak_download_mbs = round(
        max((a["max_download_rate"] for a in node_aggregates), default=0.0) / 1024,
        1,
    )

    # Plain-language factual insights generated from live cache.db
    insights = []
    if flow_routes:
        fr0 = flow_routes[0]
        dl_txt = f"{fr0['total_download_mb'] / 1024:.1f} GB" if fr0["total_download_mb"] >= 1024 else f"{fr0['total_download_mb']:.0f} MB"
        avoid_txt = f"，并自动绕开 {fr0['effective_blocked_count']} 条卡顿线路" if fr0["effective_blocked_count"] > 0 else ""
        insights.append(
            {
                "tone": "blue",
                "tag": "主力提速",
                "text": f"看 {fr0['label']} 累计加速 {dl_txt}，AI 从 {fr0['candidate_count']} 条线中优选 {fr0['top_node']}{avoid_txt}",
            }
        )
    standout_nodes = [a for a in node_aggregates if a["success"] >= 1000]
    if standout_nodes:
        best_n = max(standout_nodes, key=lambda x: (x["success_rate"], x["peak_mbs"], x["success"]))
        insights.append(
            {
                "tone": "green",
                "tag": "零卡标杆",
                "text": f"{best_n['node']} 承担 {best_n['success']:,} 次访问达成 {best_n['success_rate']:.1f}% 畅通率，实测峰值 {best_n['peak_mbs']} MB/s",
            }
        )
    if len(provider_mix) >= 2:
        mix_desc = "、".join(f"{p['tag']} {p['req_pct']:.0f}%" for p in provider_mix[:3])
        insights.append(
            {
                "tone": "amber",
                "tag": "多线混跑",
                "text": f"多机场智能协同分流（请求占比 {mix_desc}），告别传统测速只死磕单一线路",
            }
        )
    if active_site_blocks > 0:
        insights.append(
            {
                "tone": "red",
                "tag": "自动避坑",
                "text": f"实时拦截 {active_site_blocks} 处站点-节点异常组合，正在守护 {active_failure_targets} 个常用网站免手动切节点",
            }
        )

    return {
        "meta": {
            "generated_at": now_ts,
            "db_size_kb": round(file_size / 1024, 1),
            "db_mtime": mtime,
            "bbolt_txid": txid,
        },
        "overview": {
            "group_count": len(groups_set),
            "groups": sorted(groups_set),
            "node_count": len(node_aggregates),
            "tracked_node_states": len(node_states),
            "stats_records": len(stats_detail),
            "prefetch_records": len(prefetch_list),
            "customized_sites": len(site_showcase),
            "failure_records": len(failures),
            "total_success": total_success,
            "total_failure": total_failure,
            "overall_success_rate": overall_sr,
            "total_download_mb": round(total_download_mb, 2),
            "total_upload_mb": round(total_upload_mb, 2),
            "peak_download_mbs": peak_download_mbs,
            "active_blocked_nodes": active_blocked_nodes,
            "degraded_nodes": degraded_nodes,
            "active_site_blocks": active_site_blocks,
            "active_failure_targets": active_failure_targets,
        },
        "provider_mix": provider_mix,
        "flow_routes": flow_routes,
        "insights": insights,
        "subscriptions": subscriptions,
        "selected": selected,
        "rankings": rankings,
        "node_aggregates": node_aggregates,
        "site_showcase": site_showcase,
        "prefetch": prefetch_list,
        "node_states": node_states,
        "failures": failures,
        "stats_detail": stats_detail,
    }
