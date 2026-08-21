#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
品牌热度数据采集器（第三方数据源）
- 搜索热度：Bing搜索结果数量（带重试和关键词兜底）
- 市场热度：Yahoo Finance 上市公司股价/交易量
- 输出：brand_metrics.json
"""

import requests
import re
import json
import time
import os
from datetime import datetime

# ========== 品牌定义 ==========
# search_kw: 主搜索关键词
# search_kw2: 备用关键词（主关键词失败时使用）
# stock: 上市股票代码（Yahoo Finance格式，未上市为None）

BRAND_CONFIG = {
    # ===== 安全芯片 =====
    "华大电子":   {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "华大电子", "search_kw2": "CID华大电子", "stock": None},
    "复旦微":     {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "复旦微电子", "search_kw2": "上海复旦微电子", "stock": "688385.SS"},
    "紫光同芯":   {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "紫光同芯", "search_kw2": "紫光同芯微电子", "stock": None},
    "晟元":       {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "晟元芯片", "search_kw2": "杭州晟元", "stock": None},
    "大唐微":     {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "大唐微电子", "search_kw2": "大唐微电子技术", "stock": None},
    "天津国芯":   {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "天津国芯", "search_kw2": "国芯科技", "stock": None},
    "宏思":       {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "宏思电子", "search_kw2": "北京宏思", "stock": None},
    "航芯":       {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "上海航芯", "search_kw2": "航芯芯片", "stock": None},
    "方正微":     {"sector": "安全芯片", "color": "#e74c3c", "search_kw": "方正微电子", "search_kw2": "方正微电子芯片", "stock": None},

    # ===== MCU =====
    "ST":         {"sector": "MCU", "color": "#3498db", "search_kw": "意法半导体", "search_kw2": "STMicroelectronics", "stock": "STM"},
    "瑞萨":       {"sector": "MCU", "color": "#3498db", "search_kw": "瑞萨电子", "search_kw2": "Renesas", "stock": "6723.T"},
    "NXP":        {"sector": "MCU", "color": "#3498db", "search_kw": "恩智浦半导体", "search_kw2": "NXP Semiconductors", "stock": "NXPI"},
    "英飞凌":     {"sector": "MCU", "color": "#3498db", "search_kw": "英飞凌", "search_kw2": "Infineon", "stock": "IFX.DE"},
    "新唐":       {"sector": "MCU", "color": "#3498db", "search_kw": "新唐科技", "search_kw2": "Nuvoton", "stock": "4919.TW"},
    "兆易创新":   {"sector": "MCU", "color": "#3498db", "search_kw": "兆易创新", "search_kw2": "GigaDevice", "stock": "603986.SS"},
    "华大半导体": {"sector": "MCU", "color": "#3498db", "search_kw": "华大半导体", "search_kw2": "华大半导体MCU", "stock": None},
    "汇顶科技":   {"sector": "MCU", "color": "#3498db", "search_kw": "汇顶科技", "search_kw2": "Goodix", "stock": "603160.SS"},
    "航顺":       {"sector": "MCU", "color": "#3498db", "search_kw": "航顺芯片", "search_kw2": "HK32航顺", "stock": None},
    "灵动":       {"sector": "MCU", "color": "#3498db", "search_kw": "灵动微电子", "search_kw2": "MindMotion", "stock": None},
    "ADI":        {"sector": "MCU", "color": "#3498db", "search_kw": "亚德诺半导体", "search_kw2": "Analog Devices", "stock": "ADI"},
    "TI":         {"sector": "MCU", "color": "#3498db", "search_kw": "德州仪器", "search_kw2": "Texas Instruments", "stock": "TXN"},
    "CYPRESS":    {"sector": "MCU", "color": "#3498db", "search_kw": "赛普拉斯半导体", "search_kw2": "Cypress Semiconductor", "stock": None},
    "Microchip":  {"sector": "MCU", "color": "#3498db", "search_kw": "微芯科技", "search_kw2": "Microchip Technology", "stock": "MCHP"},
    "芯旺":       {"sector": "MCU", "color": "#3498db", "search_kw": "芯旺微电子", "search_kw2": "Chipon", "stock": None},
    "MEGAWIN":    {"sector": "MCU", "color": "#3498db", "search_kw": "MEGAWIN", "search_kw2": "麦捷科技", "stock": None},
    "NAVOTA":     {"sector": "MCU", "color": "#3498db", "search_kw": "纳瓦塔NAVOTA", "search_kw2": "NAVOTA", "stock": None},
    "芯圣":       {"sector": "MCU", "color": "#3498db", "search_kw": "芯圣电子", "search_kw2": "HQChip", "stock": None},
    "赛元":       {"sector": "MCU", "color": "#3498db", "search_kw": "赛元微电子", "search_kw2": "SAKYO赛元", "stock": None},
    "苏州国芯":   {"sector": "MCU", "color": "#3498db", "search_kw": "苏州国芯", "search_kw2": "国芯科技MCU", "stock": None},
    "华芯微特":   {"sector": "MCU", "color": "#3498db", "search_kw": "华芯微特", "search_kw2": "华芯微特MCU", "stock": None},
    "小华半导体": {"sector": "MCU", "color": "#3498db", "search_kw": "小华半导体", "search_kw2": "小华半导体MCU", "stock": None},
    "先楫半导体": {"sector": "MCU", "color": "#3498db", "search_kw": "先楫半导体", "search_kw2": "HPM先楫", "stock": None},
    "雅特力":     {"sector": "MCU", "color": "#3498db", "search_kw": "雅特力半导体", "search_kw2": "Artery雅特力", "stock": None},
    "极海":       {"sector": "MCU", "color": "#3498db", "search_kw": "极海半导体", "search_kw2": "Geehy极海", "stock": None},
    "中颖":       {"sector": "MCU", "color": "#3498db", "search_kw": "中颖电子", "search_kw2": "中颖电子MCU", "stock": "300327.SZ"},

    # ===== 蓝牙 =====
    "NORDIC":     {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "Nordic半导体", "search_kw2": "Nordic Semiconductor", "stock": "NOD.OL"},
    "Dialog":     {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "Dialog半导体", "search_kw2": "Dialog Semiconductor", "stock": None},
    "泰凌微":     {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "泰凌微电子", "search_kw2": "Telink泰凌", "stock": "688591.SS"},
    "上海博通":   {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "上海博通", "search_kw2": "博通集成", "stock": None},
    "卓胜微":     {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "卓胜微", "search_kw2": "Maxscend卓胜微", "stock": "300782.SZ"},
    "易兆微":     {"sector": "蓝牙", "color": "#2ecc71", "search_kw": "易兆微", "search_kw2": "易兆微电子", "stock": None},

    # ===== BMS =====
    "芯海":       {"sector": "BMS", "color": "#f39c12", "search_kw": "芯海科技", "search_kw2": "芯海科技BMS", "stock": "688595.SS"},

    # ===== 自身品牌 =====
    "国民技术":   {"sector": "自身", "color": "#1a56c4", "search_kw": "国民技术", "search_kw2": "Nationz国民技术", "stock": "300077.SZ"},
}

# ========== 主题板块配置（机器人/AI，非品牌维度）==========
TOPIC_CONFIG = {
    "机器人芯片":  {"color": "#9b59b6", "search_kw": "机器人芯片", "search_kw2": "具身智能芯片"},
    "AI芯片":      {"color": "#1abc9c", "search_kw": "AI芯片", "search_kw2": "端侧AI芯片"},
}

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "brand_metrics.json")

# ========== MCU应用赛道配置（搜索品牌名+应用领域关键词）==========
MCU_APP_AREAS = [
    ("机器人", "#e74c3c"),       # 红 - 机器人/具身智能
    ("AI", "#9b59b6"),            # 紫 - 人工智能/端侧AI
    ("汽车电子", "#e67e22"),      # 橙 - 汽车电子/车规
    ("工业控制", "#2ecc71"),     # 绿 - 工业控制/工控
    ("消费电子", "#3498db"),      # 蓝 - 消费电子/家电
]

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
})


def fetch_bing_count(keyword, max_attempts=3):
    """从Bing获取搜索结果数量（仅从sb_count提取，多重试取最大值）"""
    url = 'https://www.bing.com/search'
    params = {'q': keyword, 'count': 10, 'setlang': 'zh-CN'}
    
    best_value = None
    for attempt in range(max_attempts):
        try:
            resp = session.get(url, params=params, timeout=12)
            if resp.status_code != 200:
                time.sleep(4)
                continue
            
            # 仅从 sb_count span 提取
            match = re.search(r'<span class="sb_count"[^>]*>([^<]+)</span>', resp.text)
            if match:
                text = match.group(1)
                nums = re.findall(r'[\d,]+', text)
                if nums:
                    val = int(nums[0].replace(',', ''))
                    # 取最大值（Bing有时返回页面内结果数而非总数）
                    if best_value is None or val > best_value:
                        best_value = val
                    # 如果值足够大（>500），认为是正确的，不需要重试
                    if val >= 500:
                        return val
        except:
            pass
        
        # 值太小或失败，等待后重试
        if attempt < max_attempts - 1:
            time.sleep(4)
    
    return best_value


def fetch_yahoo_stock(ticker):
    """从Yahoo Finance获取股票数据"""
    url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
    params = {'interval': '1d', 'range': '5d'}
    try:
        resp = session.get(url, params=params, timeout=10,
                          headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        if resp.status_code != 200:
            return None
        data = resp.json()
        result = data.get('chart', {}).get('result', [{}])[0]
        meta = result.get('meta', {})
        indicators = result.get('indicators', {}).get('quote', [{}])[0]
        
        volumes = [v for v in indicators.get('volume', []) if v is not None]
        closes = [c for c in indicators.get('close', []) if c is not None]
        
        latest_price = closes[-1] if closes else meta.get('regularMarketPrice')
        latest_vol = volumes[-1] if volumes else None
        avg_vol = sum(volumes) / len(volumes) if volumes else None
        currency = meta.get('currency', 'USD')
        
        # 5日涨跌幅
        if len(closes) >= 2:
            change_pct = ((closes[-1] - closes[0]) / closes[0]) * 100
        else:
            change_pct = 0
        
        # 交易额（量×价，用于跨市场比较）
        trade_value = None
        if latest_price and latest_vol:
            trade_value = round(latest_price * latest_vol, 0)
        
        return {
            'price': round(latest_price, 2) if latest_price else None,
            'volume': int(latest_vol) if latest_vol else None,
            'avg_volume': int(avg_vol) if avg_vol else None,
            'currency': currency,
            'change_pct': round(change_pct, 2),
            'trade_value': trade_value,
        }
    except:
        return None


_TENCENT_CCY = {'us': 'USD', 'sh': 'CNY', 'sz': 'CNY', 'hk': 'HKD'}


def _tencent_symbol(ticker):
    """Yahoo代码 -> 腾讯财经符号（仅覆盖美股/A股/港股；日股/德股/台股/挪威股返回None）"""
    t = ticker.upper()
    if t.endswith('.SS'):
        return 'sh' + t[:-3]
    if t.endswith('.SZ'):
        return 'sz' + t[:-3]
    if t.endswith('.HK'):
        return 'hk' + t[:-3]
    if t.endswith(('.T', '.TW', '.DE', '.OL')):
        return None
    return 'us' + t


def fetch_tencent_stock(ticker):
    """腾讯财经行情兜底（云端Yahoo不通时使用），覆盖美股/A股/港股。
    返回结构与 fetch_yahoo_stock 一致；涨跌为当日涨跌（非5日）。"""
    sym = _tencent_symbol(ticker)
    if not sym:
        return None
    try:
        resp = session.get(
            f"https://qt.gtimg.cn/q={sym}", timeout=10,
            headers={'User-Agent': 'Mozilla/5.0', 'Referer': 'https://gu.qq.com/'},
        )
        if resp.status_code != 200:
            return None
        txt = resp.text
        if '"' not in txt:
            return None
        parts = txt.split('"')[1].split('~')
        if len(parts) < 7:
            return None
        try:
            price = float(parts[3])
            prev_close = float(parts[4]) if parts[4] else None
            volume = int(parts[6]) if parts[6].isdigit() else None
        except (ValueError, IndexError):
            return None
        if price <= 0:
            return None
        currency = _TENCENT_CCY.get(sym[:2], 'USD')
        change_pct = round((price / prev_close - 1) * 100, 2) if prev_close else 0.0
        trade_value = round(price * volume, 0) if (price and volume) else None
        return {
            'price': price,
            'volume': volume,
            'avg_volume': None,
            'currency': currency,
            'change_pct': change_pct,
            'trade_value': trade_value,
        }
    except Exception:
        return None


def main():
    print("=" * 60)
    print("品牌热度数据采集（Bing + Yahoo Finance）")
    print("=" * 60)
    
    now = datetime.now()
    metrics = {
        "fetch_date": now.strftime("%Y-%m-%d"),
        "fetch_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "data_sources": ["Bing搜索结果数", "Yahoo Finance股价数据"],
        "brands": {},
    }

    total = len(BRAND_CONFIG)
    bing_success = 0
    bing_fallback = 0
    bing_fail = 0
    
    # === 第一阶段：Bing搜索结果数量 ===
    print(f"\n[1/4] 采集Bing搜索结果数量（{total}个品牌）...")
    
    for i, (brand_name, config) in enumerate(BRAND_CONFIG.items(), 1):
        kw1 = config["search_kw"]
        kw2 = config.get("search_kw2", kw1)
        print(f"  ({i}/{total}) {brand_name} [{kw1}]...", end=" ", flush=True)
        
        # 主关键词（内置3次重试，取最大值）
        count = fetch_bing_count(kw1)
        used_kw = kw1
        
        # 如果主关键词结果太小（<200），尝试备用关键词
        if count is None or count < 200:
            time.sleep(4)
            count2 = fetch_bing_count(kw2)
            if count2 is not None:
                if count is None or count2 > count:
                    count = count2
                    used_kw = kw2
        
        if count is not None and count > 0:
            if used_kw == kw1:
                bing_success += 1
            else:
                bing_fallback += 1
            tag = "✓" if used_kw == kw1 else "⚠️"
            print(f"{tag} {count:,}")
        else:
            bing_fail += 1
            count = 0
            print(f"❌ 失败，设为0")
        
        time.sleep(4)
        
        metrics["brands"][brand_name] = {
            "sector": config["sector"],
            "color": config["color"],
            "search_kw": used_kw,
            "bing_count": count,
            "stock_ticker": config["stock"],
            "stock_data": None,
        }

    # === 第二阶段：股票数据 ===
    # 读取上次成功采集的数据，作为云端 Yahoo 不通时的兜底
    prev_metrics = {}
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, encoding='utf-8') as f:
                prev_metrics = json.load(f)
        except Exception:
            prev_metrics = {}

    stock_brands = [(b, c) for b, c in BRAND_CONFIG.items() if c["stock"]]
    print(f"\n[2/4] 采集股价数据（{len(stock_brands)}家上市公司）...")
    stock_success = 0
    stock_fallback = 0

    for i, (brand_name, config) in enumerate(stock_brands, 1):
        ticker = config["stock"]
        print(f"  ({i}/{len(stock_brands)}) {brand_name} ({ticker})...", end=" ", flush=True)

        yh = fetch_yahoo_stock(ticker)
        if yh:
            stock_data, src = yh, "Yahoo"
        else:
            tn = fetch_tencent_stock(ticker)
            stock_data, src = (tn, "腾讯") if tn else (None, "")

        if stock_data:
            stock_success += 1
            cur = stock_data['currency']
            print(f"{stock_data['price']} {cur} | 成交量={stock_data['volume']:,} | 涨跌={stock_data['change_pct']}% [{src}]")
            metrics["brands"][brand_name]["stock_data"] = stock_data
        else:
            # 两源均失败：沿用上次成功数据，保证表格不空
            prev = prev_metrics.get("brands", {}).get(brand_name, {}).get("stock_data")
            if prev:
                stock_fallback += 1
                metrics["brands"][brand_name]["stock_data"] = prev
                print(f"⚠️ 两源失败，沿用上次({prev.get('price')} {prev.get('currency')})")
            else:
                print("❌ 获取失败且无历史")

        time.sleep(0.5)

    # === 第三阶段：主题板块热度（机器人/AI 关键词）===
    metrics["topics"] = {}
    print(f"\n[3/4] 采集主题板块热度（{len(TOPIC_CONFIG)}个主题）...")
    
    for topic_name, cfg in TOPIC_CONFIG.items():
        kw1 = cfg["search_kw"]
        kw2 = cfg.get("search_kw2", kw1)
        print(f"  {topic_name} [{kw1}]...", end=" ", flush=True)
        
        count = fetch_bing_count(kw1)
        used_kw = kw1
        
        if count is None or count < 200:
            time.sleep(4)
            count2 = fetch_bing_count(kw2)
            if count2 is not None and (count is None or count2 > count):
                count = count2
                used_kw = kw2
        
        if count and count > 0:
            tag = "✓" if used_kw == kw1 else "⚠️"
            print(f"{tag} {count:,}")
        else:
            count = 0
            print("❌ 失败，设为0")
        
        metrics["topics"][topic_name] = {
            "color": cfg["color"],
            "search_kw": used_kw,
            "bing_count": count,
        }
        
        time.sleep(4)

    # === 第四阶段：MCU应用赛道声量（TOP5品牌×5应用领域）===
    print(f"\n[4/4] 采集MCU应用赛道声量（TOP5品牌 × {len(MCU_APP_AREAS)}个应用领域）...")

    # 确定 TOP5：国民技术(自身) + 兆易创新(固定) + MCU板块按搜索量取前3
    self_name = "国民技术"
    focus_name = "兆易创新"
    mcu_brands = [(n, d) for n, d in metrics["brands"].items()
                  if d["sector"] == "MCU" and n != focus_name]
    mcu_brands.sort(key=lambda x: x[1]["bing_count"], reverse=True)
    top3_mcu = [n for n, _ in mcu_brands[:3]]
    top5_for_app = [self_name, focus_name] + top3_mcu

    metrics["mcu_applications"] = {}

    for bi, brand_name in enumerate(top5_for_app, 1):
        brand_kw = BRAND_CONFIG.get(brand_name, {}).get("search_kw", brand_name)
        print(f"  ({bi}/{len(top5_for_app)}) {brand_name}:", end=" ", flush=True)

        area_results = {}
        for area_name, area_color in MCU_APP_AREAS:
            search_term = f"{brand_kw} {area_name}"
            count = fetch_bing_count(search_term)
            if count is None:
                count = 0
            area_results[area_name] = count
            print(f"{area_name}={count:,}", end=" ", flush=True)
            time.sleep(4)

        # 找出声量最高的应用赛道
        top_area = max(area_results, key=area_results.get) if any(area_results.values()) else "—"
        top_count = area_results.get(top_area, 0)

        metrics["mcu_applications"][brand_name] = {
            "areas": area_results,
            "top_area": top_area,
            "top_count": top_count,
        }
        print(f"  => 最强: {top_area} ({top_count:,})")

    # === 保存 ===
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    
    # === 统计汇总 ===
    print("\n" + "=" * 60)
    print("采集完成！")
    print(f"  数据文件: {OUTPUT_FILE}")
    print(f"  Bing搜索(品牌): 成功{bing_success} + 备用{bing_fallback} + 失败{bing_fail} = {total}个品牌")
    print(f"  Bing搜索(主题): {len(TOPIC_CONFIG)}个主题板块")
    print(f"  股价数据: 成功{stock_success} + 沿用上次{stock_fallback} = {len(stock_brands)}家")

    # 主题板块热度
    print("\n主题板块热度:")
    for topic_name, tdata in metrics.get("topics", {}).items():
        print(f"  - {topic_name}: {tdata['bing_count']:>12,} (关键词: {tdata['search_kw']})")
    
    # 搜索热度TOP10
    print("\n搜索热度 TOP10:")
    sorted_brands = sorted(metrics["brands"].items(), key=lambda x: x[1]["bing_count"], reverse=True)
    for i, (name, data) in enumerate(sorted_brands[:10], 1):
        stock_str = ""
        if data["stock_data"]:
            sd = data["stock_data"]
            stock_str = f" | 股价: {sd['price']} {sd['currency']}"
        print(f"  {i:2d}. {name:15s} | 搜索: {data['bing_count']:>12,}{stock_str}")
    
    return metrics


if __name__ == "__main__":
    main()
