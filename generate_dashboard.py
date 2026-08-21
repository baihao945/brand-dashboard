#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
竞品动态日报 H5 仪表盘生成器（第三方数据版）
- 搜索热度：Bing搜索结果数量（brand_metrics.json）
- 市场热度：Yahoo Finance上市公司股价/交易量
- 日报正文：最新一天日报内容
"""

import os
import re
import json
import glob
from datetime import datetime

# ========== 品牌定义（用于日报正文解析）==========
BRANDS = {
    "安全芯片": {"color": "#e74c3c", "brands": [
        ("华大电子", ["华大电子"]), ("复旦微", ["复旦微", "复旦微电"]),
        ("紫光同芯", ["紫光同芯", "同芯微"]), ("晟元", ["晟元"]),
        ("大唐微", ["大唐微"]), ("天津国芯", ["天津国芯"]),
        ("宏思", ["宏思"]), ("航芯", ["航芯"]), ("方正微", ["方正微"]),
    ]},
    "MCU": {"color": "#3498db", "brands": [
        ("ST", ["ST", "意法半导体", "STM32"]), ("瑞萨", ["瑞萨", "Renesas"]),
        ("NXP", ["NXP", "恩智浦"]), ("英飞凌", ["英飞凌", "Infineon"]),
        ("新唐", ["新唐", "新唐科技", "NuvoTon"]), ("兆易创新", ["兆易创新", "GigaDevice", "GD32"]),
        ("华大半导体", ["华大半导体"]), ("汇顶科技", ["汇顶", "Goodix"]),
        ("航顺", ["航顺", "HK32"]), ("灵动", ["灵动", "MindMotion"]),
        ("ADI", ["ADI", "亚德诺"]), ("TI", ["TI", "德州仪器"]),
        ("CYPRESS", ["CYPRESS", "赛普拉斯"]), ("Microchip", ["Microchip", "微芯"]),
        ("芯旺", ["芯旺", "Chipon"]), ("MEGAWIN", ["MEGAWIN"]),
        ("NAVOTA", ["NAVOTA"]), ("芯圣", ["芯圣"]), ("赛元", ["赛元"]),
        ("苏州国芯", ["苏州国芯"]), ("华芯微特", ["华芯微特"]),
        ("小华半导体", ["小华半导体"]), ("先楫半导体", ["先楫", "HPM5"]),
        ("雅特力", ["雅特力", "Artery"]), ("极海", ["极海", "Geehy", "APM32"]),
        ("中颖", ["中颖", "中颖电子"]),
    ]},
    "蓝牙": {"color": "#2ecc71", "brands": [
        ("NORDIC", ["NORDIC", "Nordic", "nRF54"]), ("Dialog", ["Dialog"]),
        ("泰凌微", ["泰凌微", "Telink"]), ("上海博通", ["上海博通"]),
        ("卓胜微", ["卓胜微", "Maxscend"]), ("易兆微", ["易兆微"]),
    ]},
    "BMS": {"color": "#f39c12", "brands": [
        ("芯海", ["芯海", "芯海科技", "SINOWEALTH"]),
    ]},
}

SELF_BRAND = {"name": "国民技术", "color": "#1a56c4"}

DAILY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daily")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")
METRICS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand_metrics.json")

# 仪表盘在线部署地址（用于微信分享卡片 og:image 绝对URL）
# 优先读环境变量（自动化部署后写入 dashboard_url.txt）；缺省保留旧链接
DASHBOARD_BASE_URL = os.environ.get(
    "DASHBOARD_BASE_URL",
    "https://2965c6ac28b64b09b167544a3b815f24.sh4.agentos-app.net",
)


def format_count(n):
    """格式化搜索结果数量"""
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}亿"
    elif n >= 10_000:
        return f"{n / 10_000:.1f}万"
    else:
        return f"{n:,}"


def format_volume(n):
    """格式化成交量"""
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}亿"
    elif n >= 10_000:
        return f"{n / 10_000:.1f}万"
    else:
        return f"{n:,}"


def format_price(price, currency):
    """格式化股价"""
    symbols = {"CNY": "¥", "USD": "$", "JPY": "¥", "EUR": "€", "TWD": "NT$", "NOK": "kr "}
    symbol = symbols.get(currency, "")
    return f"{symbol}{price:.2f}"


def load_brand_metrics():
    """加载第三方品牌热度数据"""
    if not os.path.exists(METRICS_FILE):
        print("  ⚠️ brand_metrics.json 不存在，请先运行 fetch_brand_metrics.py")
        return None
    with open(METRICS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_date_from_filename(filepath):
    basename = os.path.basename(filepath)
    match = re.search(r"(\d{4}-\d{2}-\d{2})", basename)
    return match.group(1) if match else None


def md_to_html(md_text):
    """将日报Markdown转换为带样式的HTML片段"""
    lines = md_text.split('\n')
    html_parts = []
    in_ol = False
    in_ul = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_ol: html_parts.append('</ol>'); in_ol = False
            if in_ul: html_parts.append('</ul>'); in_ul = False
            continue

        if stripped.startswith('# ') and not stripped.startswith('## '):
            html_parts.append(f'<div class="report-title">{stripped[2:].strip()}</div>')
            continue

        if stripped == '---':
            if in_ol: html_parts.append('</ol>'); in_ol = False
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append('<hr style="border:none;border-top:1px solid #e8e8e8;margin:12px 0;">')
            continue

        if stripped.startswith('## '):
            if in_ol: html_parts.append('</ol>'); in_ol = False
            if in_ul: html_parts.append('</ul>'); in_ul = False
            html_parts.append(f'<div class="report-section-title">{stripped[3:].strip()}</div>')
            continue

        ol_match = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if ol_match:
            if not in_ol:
                if in_ul: html_parts.append('</ul>'); in_ul = False
                html_parts.append('<ol class="report-ol">'); in_ol = True
            html_parts.append(f'<li>{format_inline(ol_match.group(2))}</li>')
            continue

        if stripped.startswith('- '):
            if not in_ul:
                if in_ol: html_parts.append('</ol>'); in_ol = False
                html_parts.append('<ul class="report-ul">'); in_ul = True
            html_parts.append(f'<li>{format_inline(stripped[2:].strip())}</li>')
            continue

        if stripped.startswith('*') and stripped.endswith('*') and not stripped.startswith('**'):
            html_parts.append(f'<div class="report-source">{stripped[1:-1]}</div>')
            continue

        if in_ol: html_parts.append('</ol>'); in_ol = False
        if in_ul: html_parts.append('</ul>'); in_ul = False
        html_parts.append(f'<p class="report-p">{format_inline(stripped)}</p>')

    if in_ol: html_parts.append('</ol>')
    if in_ul: html_parts.append('</ul>')
    return '\n'.join(html_parts)


def format_inline(text):
    return re.sub(r'\*\*(.+?)\*\*', r'<span class="brand">\1</span>', text)


def parse_latest_report():
    """解析最新日报（仅内容，不统计声量）"""
    md_files = sorted(glob.glob(os.path.join(DAILY_DIR, "*.md")))
    if not md_files:
        return None

    filepath = md_files[-1]
    date = extract_date_from_filename(filepath)
    if not date:
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    active_match = re.search(r"有动态(\d+)家", content)
    active_count = int(active_match.group(1)) if active_match else 0

    return {
        "date": date,
        "active_count": active_count,
        "report_html": md_to_html(content),
    }


def generate_stock_table(metrics):
    """生成上市公司行情表格HTML"""
    stock_brands = []
    for name, data in metrics["brands"].items():
        if data.get("stock_data"):
            stock_brands.append((name, data))

    # 国民技术排第一
    stock_brands.sort(key=lambda x: (x[0] != "国民技术", x[0]))

    rows = []
    for name, data in stock_brands:
        sd = data["stock_data"]
        is_self = name == "国民技术"
        change = sd["change_pct"]
        change_class = "up" if change > 0 else ("down" if change < 0 else "flat")
        change_str = f"+{change:.2f}%" if change > 0 else f"{change:.2f}%"
        name_display = f"★ {name}" if is_self else name
        row_class = ' class="self-row"' if is_self else ""
        
        rows.append(f"""<tr{row_class}>
            <td class="stock-name">{name_display}</td>
            <td>{format_price(sd['price'], sd['currency'])}</td>
            <td>{format_volume(sd['volume'])}</td>
            <td class="{change_class}">{change_str}</td>
        </tr>""")

    return f"""<div class="chart-section">
        <div class="chart-section-title"><span class="dot" style="background:#f39c12;"></span>上市公司行情（{len(stock_brands)}家 · 5日涨跌）</div>
        <div class="stock-table-wrap">
        <table class="stock-table">
            <thead><tr><th>品牌</th><th>股价</th><th>成交量</th><th>5日涨跌</th></tr></thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        </div>
    </div>"""


def generate_html(latest, metrics):
    """生成 H5 页面"""

    self_name = SELF_BRAND["name"]
    self_color = SELF_BRAND["color"]

    # === 搜索热度排行 ===
    brand_search = {}
    sector_search = {"安全芯片": 0, "MCU": 0, "蓝牙": 0, "BMS": 0}

    for name, data in metrics["brands"].items():
        count = data.get("bing_count", 0)
        brand_search[name] = {"count": count, "color": data.get("color", "#999"), "sector": data.get("sector", "")}
        if data.get("sector") in sector_search:
            sector_search[data["sector"]] += count

    # 国民技术 + 兆易创新固定，其余全部供应商按搜索热度取 TOP5（共7个）
    mcu_apps = metrics.get("mcu_applications", {})

    def get_app_areas_detail(name):
        """获取品牌所有应用赛道的声量明细（仅MCU品牌有）"""
        app = mcu_apps.get(name, {})
        return app.get("areas", {})

    self_data = brand_search.get(self_name, {"count": 0, "color": self_color, "sector": "MCU"})
    focus_name = "兆易创新"
    focus_data = brand_search.get(focus_name, {"count": 0, "color": "#9b59b6", "sector": "MCU"})
    focus_data["color"] = "#9b59b6"
    # 全部供应商（排除自身和兆易创新），跨所有板块
    others = [(n, d) for n, d in brand_search.items() if n not in (self_name, focus_name)]
    others.sort(key=lambda x: x[1]["count"], reverse=True)
    top5 = others[:5]

    combined = []
    combined.append({"name": self_name, "count": self_data["count"], "color": self_color, "sector": "MCU"})
    combined.append({"name": focus_name, "count": focus_data["count"], "color": focus_data["color"], "sector": "MCU"})
    for n, d in top5:
        combined.append({"name": n, "count": d["count"], "color": d["color"], "sector": d["sector"]})

    def fmt_label(item):
        return f"{item['name']} · {item['sector']}"

    top5_labels = [fmt_label(it) for it in combined]
    top5_values = [it["count"] for it in combined]
    top5_colors = [it["color"] for it in combined]
    top5_formatted = [format_count(it["count"]) for it in combined]
    top5_sectors = [it["sector"] for it in combined]
    top5_names = [it["name"] for it in combined]
    top5_areas_detail = [get_app_areas_detail(it["name"]) for it in combined]

    # === 板块占比（4个产品板块 + 2个主题板块：机器人/AI）===
    sector_labels = list(sector_search.keys())
    sector_values = list(sector_search.values())
    sector_colors = [BRANDS[s]["color"] for s in sector_labels if s in BRANDS]

    # 加入主题板块（机器人芯片/AI芯片），用关键词Bing搜索结果数
    topics_data = metrics.get("topics", {})
    topic_order = ["机器人芯片", "AI芯片"]
    for topic_name in topic_order:
        if topic_name in topics_data:
            sector_labels.append(topic_name)
            sector_values.append(topics_data[topic_name].get("bing_count", 0))
            sector_colors.append(topics_data[topic_name].get("color", "#999"))

    # === 上市统计 ===
    stock_count = sum(1 for d in metrics["brands"].values() if d.get("stock_data"))

    # === 股票表格 ===
    stock_table_html = generate_stock_table(metrics)

    data = {
        "date": latest["date"],
        "active_count": latest["active_count"],
        "stock_count": stock_count,
        "self_brand": self_name,
        "self_color": self_color,
        "top5_labels": top5_labels,
        "top5_values": top5_values,
        "top5_colors": top5_colors,
        "top5_formatted": top5_formatted,
        "top5_sectors": top5_sectors,
        "top5_names": top5_names,
        "top5_areas_detail": top5_areas_detail,
        "sector_labels": sector_labels,
        "sector_values": sector_values,
        "sector_colors": sector_colors,
        "sector_formatted": [format_count(v) for v in sector_values],
        "report_html": latest["report_html"],
        "metrics_date": metrics.get("fetch_date", ""),
        "metrics_time": metrics.get("fetch_time", ""),
    }

    data_json = json.dumps(data, ensure_ascii=False)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>半导体芯片行业动态简报</title>

<!-- 微信分享卡片 / Open Graph -->
<meta property="og:title" content="半导体芯片行业动态简报">
<meta property="og:description" content="国民技术品牌动态监控 · 44家竞品 · 6大板块 · 7大渠道 · 每日8/13/20点实时更新">
<meta property="og:type" content="website">
<meta property="og:url" content="{DASHBOARD_BASE_URL}/">
<meta property="og:image" content="{DASHBOARD_BASE_URL}/cover.png">
<meta property="og:image:width" content="1080">
<meta property="og:image:height" content="1080">
<meta property="og:image:type" content="image/png">
<meta name="description" content="国民技术品牌动态监控 · 44家竞品 · 6大板块 · 7大渠道 · 每日8/13/20点实时更新">
<meta itemprop="name" content="半导体芯片行业动态简报">
<meta itemprop="description" content="国民技术品牌动态监控 · 44家竞品 · 6大板块 · 7大渠道 · 每日8/13/20点实时更新">
<meta itemprop="image" content="{DASHBOARD_BASE_URL}/cover.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="半导体芯片行业动态简报">
<meta name="twitter:description" content="国民技术品牌动态监控 · 44家竞品 · 6大板块 · 7大渠道">
<meta name="twitter:image" content="{DASHBOARD_BASE_URL}/cover.png">

<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html {{ -webkit-text-size-adjust: 100%; }}
body {{
    font-family: -apple-system, "Microsoft YaHei", "Segoe UI", sans-serif;
    background: #f0f2f5;
    color: #333;
    -webkit-font-smoothing: antialiased;
    padding-bottom: 40px;
}}
.container {{ width: 100%; max-width: 600px; margin: 0 auto; padding: 0 12px; }}

/* ===== 顶部头部 ===== */
.header {{
    background: linear-gradient(135deg, #1a2a3a 0%, #2d4a6b 100%);
    color: #fff;
    padding: 20px 20px 16px;
    text-align: center;
    position: relative;
    overflow: hidden;
}}
.header::after {{
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #e74c3c, #f39c12, #3498db, #2ecc71);
}}
.header h1 {{ font-size: 18px; font-weight: 700; margin-bottom: 4px; }}
.header .subtitle {{ font-size: 12px; opacity: 0.75; }}
.update-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 20px;
    padding: 2px 8px;
    font-size: 10px;
    margin-top: 6px;
}}

/* ===== 统计卡片 ===== */
.stats-row {{ display: flex; gap: 8px; padding-top: 10px; }}
.stat-card {{
    flex: 1;
    background: #fff;
    border-radius: 8px;
    padding: 8px 6px;
    text-align: center;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
.stat-card .num {{ font-size: 18px; font-weight: 700; color: #1a56c4; line-height: 1.2; }}
.stat-card .label {{ font-size: 10px; color: #999; margin-top: 2px; }}

/* ===== 图表区域 ===== */
.charts-toggle {{ padding-top: 8px; text-align: center; }}
.charts-toggle-btn {{
    display: inline-block;
    background: #fff;
    color: #1a56c4;
    border: 1px solid #d0d8e8;
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}}
.charts-toggle-btn:hover {{ background: #f0f4f8; }}
.charts-wrap {{ padding-top: 8px; display: none; }}
.charts-wrap.show {{ display: block; }}
.chart-section {{
    background: #fff;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
.chart-section-title {{
    font-size: 12px;
    font-weight: 600;
    color: #1a2a3a;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 4px;
}}
.chart-section-title .dot {{
    width: 3px;
    height: 12px;
    border-radius: 1px;
    background: #1a56c4;
}}
.chart-container {{ position: relative; width: 100%; }}
.chart-container.bar {{ height: 240px; }}
.chart-container.donut {{ height: 160px; }}
.legend {{
    display: flex;
    flex-wrap: wrap;
    gap: 4px 12px;
    justify-content: center;
    margin-top: 4px;
}}
.legend-item {{ display: flex; align-items: center; gap: 3px; font-size: 10px; color: #888; }}
.legend-dot {{ width: 8px; height: 8px; border-radius: 2px; }}

/* ===== 股票表格 ===== */
.stock-table-wrap {{ overflow-x: auto; }}
.stock-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
}}
.stock-table th {{
    text-align: left;
    padding: 6px 8px;
    color: #999;
    font-weight: 500;
    border-bottom: 1px solid #eee;
    white-space: nowrap;
}}
.stock-table td {{
    padding: 5px 8px;
    border-bottom: 1px solid #f5f5f5;
    white-space: nowrap;
}}
.stock-table .stock-name {{ font-weight: 600; color: #333; }}
.stock-table .up {{ color: #e74c3c; font-weight: 600; }}
.stock-table .down {{ color: #2ecc71; font-weight: 600; }}
.stock-table .flat {{ color: #999; }}
.stock-table .self-row {{
    background: #f0f4ff;
}}
.stock-table .self-row .stock-name {{ color: #1a56c4; }}

/* ===== 日报正文 ===== */
.report-wrap {{ padding-top: 8px; }}
.report-card {{
    background: #fff;
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    overflow: hidden;
}}
.report-title {{
    font-size: 16px;
    font-weight: 700;
    color: #1a2a3a;
    text-align: center;
    padding-bottom: 10px;
    border-bottom: 2px solid #1a2a3a;
    margin-bottom: 12px;
}}
.report-section-title {{
    font-size: 13px;
    font-weight: 700;
    color: #1a2a3a;
    background: #f0f4f8;
    border-left: 3px solid #1a56c4;
    padding: 6px 10px;
    margin: 12px 0 6px 0;
    border-radius: 0 4px 4px 0;
}}
.report-ol {{ margin: 0; padding-left: 18px; font-size: 12.5px; line-height: 1.75; color: #444; }}
.report-ul {{ margin: 0; padding-left: 16px; font-size: 12.5px; line-height: 1.75; color: #444; list-style: none; }}
.report-ul li {{ position: relative; padding-left: 10px; margin-bottom: 3px; }}
.report-ul li::before {{
    content: '';
    position: absolute;
    left: 0; top: 8px;
    width: 4px; height: 4px;
    border-radius: 50%;
    background: #c0c8d8;
}}
.report-ol li {{ margin-bottom: 3px; }}
.report-ul li .brand, .report-ol li .brand {{ font-weight: 700; color: #1a56c4; }}
.report-source {{
    font-size: 10px;
    color: #999;
    margin-top: 12px;
    padding-top: 8px;
    border-top: 1px solid #f0f0f0;
    line-height: 1.5;
}}
.report-p {{ font-size: 12.5px; line-height: 1.75; color: #444; margin: 4px 0; }}

/* ===== 底部 ===== */
.footer {{
    text-align: center;
    padding: 16px 12px;
    font-size: 10px;
    color: #bbb;
    line-height: 1.6;
}}

/* ===== 小屏手机 ===== */
@media (max-width: 380px) {{
    .stat-card .num {{ font-size: 16px; }}
    .header h1 {{ font-size: 16px; }}
    .report-section-title {{ font-size: 12px; }}
    .report-ol, .report-ul {{ font-size: 12px; }}
    .stock-table {{ font-size: 10px; }}
    .stock-table th, .stock-table td {{ padding: 4px 6px; }}
}}

/* ===== 平板竖屏 / 小笔记本 (768px+) ===== */
@media (min-width: 768px) {{
    .container {{ max-width: 740px; padding: 0 16px; }}
    .header {{ padding: 28px 20px 20px; }}
    .header h1 {{ font-size: 22px; }}
    .header .subtitle {{ font-size: 13px; }}
    .stat-card .num {{ font-size: 22px; }}
    .stat-card .label {{ font-size: 11px; }}
    .stat-card {{ padding: 12px 8px; }}
    .charts-toggle-btn {{ font-size: 13px; padding: 6px 18px; }}
    .chart-section {{ padding: 14px 16px; }}
    .chart-section-title {{ font-size: 14px; }}
    .chart-container.bar {{ height: 280px; }}
    .chart-container.donut {{ height: 200px; }}
    .legend-item {{ font-size: 12px; }}
    .stock-table {{ font-size: 13px; }}
    .stock-table th, .stock-table td {{ padding: 8px 12px; }}
    .report-card {{ padding: 24px 28px; }}
    .report-title {{ font-size: 20px; padding-bottom: 14px; margin-bottom: 16px; }}
    .report-section-title {{ font-size: 15px; padding: 8px 12px; margin: 16px 0 8px 0; }}
    .report-ol, .report-ul {{ font-size: 14px; line-height: 1.85; }}
    .report-p {{ font-size: 14px; line-height: 1.85; }}
    .report-source {{ font-size: 12px; }}
    .footer {{ font-size: 11px; }}
    .charts-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
    .charts-grid .chart-section {{ margin-bottom: 0; }}
}}

/* ===== PC桌面 (1024px+) ===== */
@media (min-width: 1024px) {{
    .container {{ max-width: 960px; padding: 0 20px; }}
    .header {{ padding: 32px 20px 24px; }}
    .header h1 {{ font-size: 26px; }}
    .header .subtitle {{ font-size: 14px; }}
    .update-badge {{ font-size: 11px; padding: 3px 10px; }}
    .stat-card .num {{ font-size: 26px; }}
    .stat-card .label {{ font-size: 12px; }}
    .stat-card {{ padding: 14px 10px; }}
    .stats-row {{ gap: 12px; }}
    .chart-section {{ padding: 16px 20px; }}
    .chart-section-title {{ font-size: 15px; }}
    .chart-container.bar {{ height: 320px; }}
    .chart-container.donut {{ height: 220px; }}
    .report-card {{ padding: 28px 36px; }}
    .report-title {{ font-size: 22px; }}
    .report-section-title {{ font-size: 16px; }}
    .report-ol, .report-ul {{ font-size: 15px; line-height: 1.9; }}
    .report-p {{ font-size: 15px; line-height: 1.9; }}
    .footer {{ font-size: 12px; padding: 20px 12px; }}
    .charts-grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 12px; }}
    .charts-grid-full {{ grid-column: 1 / -1; }}
}}

/* ===== 大屏桌面 (1440px+) ===== */
@media (min-width: 1440px) {{
    .container {{ max-width: 1100px; }}
    .header h1 {{ font-size: 28px; }}
}}
</style>
</head>
<body>

<div class="header">
    <h1>半导体芯片行业动态简报</h1>
    <div class="subtitle">44家竞品品牌 · 4大产品板块 + 机器人/AI主题 · 7大渠道全网监测</div>
    <div class="update-badge">数据更新于 {now_str} · 日报 {latest["date"]}</div>
</div>

<div class="container">
<div class="stats-row">
    <div class="stat-card">
        <div class="num">44</div>
        <div class="label">监控品牌</div>
    </div>
    <div class="stat-card">
        <div class="num">{latest["active_count"]}</div>
        <div class="label">有动态品牌</div>
    </div>
    <div class="stat-card">
        <div class="num">{stock_count}</div>
        <div class="label">上市追踪</div>
    </div>
</div>
</div>

<div class="container">
<div class="charts-toggle">
    <div class="charts-toggle-btn" id="chartsToggle" onclick="toggleCharts()">
        📊 品牌热度数据 ▸
    </div>
    <div style="font-size:10px;color:#aaa;margin-top:4px;">
        数据来源：Bing搜索结果数 + Yahoo Finance股价
    </div>
</div>

<div class="charts-wrap" id="chartsWrap">
    <div class="charts-grid">
    <div class="chart-section">
        <div class="chart-section-title"><span class="dot" style="background:{self_color};"></span>品牌搜索热度 TOP7</div>
        <div class="chart-container bar">
            <canvas id="barChart"></canvas>
        </div>
    </div>
    <div class="chart-section">
        <div class="chart-section-title"><span class="dot"></span>六大板块搜索热度占比</div>
        <div class="chart-container donut">
            <canvas id="donutChart"></canvas>
        </div>
        <div class="legend" id="donutLegend"></div>
    </div>
    </div>
    {stock_table_html}
</div>
</div>

<div class="container">
<div class="report-wrap">
    <div class="report-card" id="reportContent"></div>
</div>
</div>

<div class="footer">
    搜索热度数据：Bing搜索结果数量（{data["metrics_date"]}采集，4个产品板块按品牌汇总 + 机器人/AI主题按关键词）<br>
    股价数据：Yahoo Finance API（5日区间）<br>
    日报内容：WebSearch + 微信公众号 + 财经平台 + 半导体媒体 + 社交媒体 + 供应链 + 专利数据库<br>
    监控范围：安全芯片9家 · MCU 26家 · 蓝牙6家 · BMS 3家
</div>

<script>
const D = {data_json};

document.getElementById('reportContent').innerHTML = D.report_html;

let chartsVisible = false;
let barChart = null, donutChart = null;

function toggleCharts() {{
    chartsVisible = !chartsVisible;
    const wrap = document.getElementById('chartsWrap');
    const btn = document.getElementById('chartsToggle');
    if (chartsVisible) {{
        wrap.classList.add('show');
        btn.innerHTML = '📊 品牌热度数据 ▾';
        if (!barChart) initCharts();
    }} else {{
        wrap.classList.remove('show');
        btn.innerHTML = '📊 品牌热度数据 ▸';
    }}
}}

function fmtNum(n) {{
    if (n >= 100000000) return (n/100000000).toFixed(1) + '亿';
    if (n >= 10000) return (n/10000).toFixed(1) + '万';
    return n.toLocaleString();
}}

function initCharts() {{
    barChart = new Chart(document.getElementById('barChart'), {{
        type: 'bar',
        data: {{
            labels: D.top5_labels,
            datasets: [{{
                data: D.top5_values,
                backgroundColor: D.top5_colors,
                borderWidth: 0,
                borderRadius: 2,
                barPercentage: 0.85,
                categoryPercentage: 0.85,
                minBarLength: 2,
            }}]
        }},
        options: {{
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            layout: {{ padding: {{ left: 0, right: 50, top: 4, bottom: 4 }} }},
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        title: (items) => {{
                            const i = items[0].dataIndex;
                            return D.top5_names[i] + '（' + D.top5_sectors[i] + '）';
                        }},
                        label: (ctx) => {{
                            const i = ctx.dataIndex;
                            const detail = D.top5_areas_detail[i];
                            const lines = ['搜索结果约 ' + ctx.parsed.x.toLocaleString() + ' 个'];
                            if (detail && Object.keys(detail).length) {{
                                const areaNames = Object.keys(detail).sort((a, b) => detail[b] - detail[a]);
                                areaNames.forEach(function(area) {{
                                    lines.push(area + ': ' + detail[area].toLocaleString());
                                }});
                            }}
                            return lines;
                        }}
                    }}
                }}
            }},
            scales: {{
                x: {{
                    beginAtZero: true,
                    grid: {{ color: '#f0f0f0', drawTicks: false }},
                    ticks: {{
                        font: {{ size: 10 }},
                        color: '#999',
                        callback: function(v) {{ return fmtNum(v); }}
                    }},
                    border: {{ display: false }}
                }},
                y: {{
                    grid: {{ display: false, drawBorder: false }},
                    ticks: {{
                        font: {{ size: 11, weight: '600' }},
                        color: (ctx) => {{
                            const label = ctx.tick && ctx.tick.label;
                            // 国民技术品牌蓝、兆易创新紫色，其他灰色
                            const i = ctx.tick && ctx.tick.index;
                            const name = D.top5_names[i] || '';
                            if (name === D.self_brand) return D.self_color;
                            if (name === '兆易创新') return '#9b59b6';
                            return '#555';
                        }},
                        callback: function(value) {{
                            const label = this.getLabelForValue(value);
                            return label.length > 14 ? label.substring(0, 14) : label;
                        }}
                    }},
                    border: {{ display: false }}
                }}
            }}
        }}
    }});

    donutChart = new Chart(document.getElementById('donutChart'), {{
        type: 'doughnut',
        data: {{
            labels: D.sector_labels,
            datasets: [{{
                data: D.sector_values,
                backgroundColor: D.sector_colors,
                borderWidth: 0,
                spacing: 2,
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            cutout: '62%',
            animation: false,
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: (ctx) => {{
                            const total = ctx.dataset.data.reduce((a,b)=>a+b, 0);
                            const pct = ((ctx.parsed / total) * 100).toFixed(1);
                            return ctx.label + ': ' + fmtNum(ctx.parsed) + ' (' + pct + '%)';
                        }}
                    }}
                }}
            }}
        }}
    }});

    const legendEl = document.getElementById('donutLegend');
    D.sector_labels.forEach((label, i) => {{
        const item = document.createElement('div');
        item.className = 'legend-item';
        item.innerHTML = '<span class="legend-dot" style="background:' + D.sector_colors[i] + '"></span>' + label + ' (' + fmtNum(D.sector_values[i]) + ')';
        legendEl.appendChild(item);
    }});
}}
</script>

</body>
</html>"""

    return html


def main():
    print("正在生成动态简报H5页面（第三方数据版）...")

    # 先生成微信分享卡片封面图
    try:
        from generate_cover import generate_cover as gen_cover
        gen_cover()
        print()
    except Exception as e:
        print(f"  ⚠️ 封面图生成失败: {e}，继续生成HTML\n")

    # 加载日报
    latest = parse_latest_report()
    if not latest:
        print("  未找到日报数据")
        return

    # 加载品牌热度数据
    metrics = load_brand_metrics()
    if not metrics:
        print("  未找到品牌热度数据，退出")
        return

    stock_count = sum(1 for d in metrics["brands"].values() if d.get("stock_data"))
    print(f"  最新日报: {latest['date']}, 有动态{latest['active_count']}家")
    print(f"  热度数据: {metrics['fetch_date']}采集, 上市追踪{stock_count}家")

    html = generate_html(latest, metrics)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n  H5页面已生成: {output_path}")


if __name__ == "__main__":
    main()
