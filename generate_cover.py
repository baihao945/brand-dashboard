#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成微信分享卡片封面图（1080x1080 RGBA）"""
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard")
# 字体：Windows(微软雅黑) 与 Linux(Noto/思源黑体，免商用SIL OFL) 自适应
_FONT_CANDIDATES_REG = [
    "C:/Windows/Fonts/msyh.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]
_FONT_CANDIDATES_BLD = [
    "C:/Windows/Fonts/msyhbd.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
]


def _pick_font(cands):
    for p in cands:
        if os.path.exists(p):
            return p
    return cands[-1]  # 兜底：返回最后一项，缺失时 PIL 会给出明确报错


FONT_REG = _pick_font(_FONT_CANDIDATES_REG)
FONT_BLD = _pick_font(_FONT_CANDIDATES_BLD)


def gradient_bg(w, h, top_color, bottom_color):
    """生成渐变背景图"""
    bg = Image.new('RGB', (w, h), top_color)
    draw = ImageDraw.Draw(bg)
    for y in range(h):
        ratio = y / h
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return bg


def text_width(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]


def text_height(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


def draw_centered(draw, text, font, y, fill, w):
    tw = text_width(draw, text, font)
    draw.text(((w - tw) / 2, y), text, font=font, fill=fill)


def generate_cover():
    W = H = 1080

    # 1. 渐变背景（深海军蓝 → 中蓝）
    img = gradient_bg(W, H, (26, 42, 58), (45, 85, 140))
    # 转 RGBA 以支持透明度叠加
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img, 'RGBA')

    # 2. 顶部柔光（圆形渐变光晕）
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    cx, cy, max_r = 200, 200, 600
    for r in range(max_r, 0, -10):
        alpha = max(0, int(45 * (1 - r / max_r) ** 1.5))
        gdraw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(140, 180, 220, alpha))
    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img, 'RGBA')

    # 3. 字体加载
    f_brand = ImageFont.truetype(FONT_REG, 32)
    f_title = ImageFont.truetype(FONT_BLD, 108)
    f_sub = ImageFont.truetype(FONT_REG, 30)
    f_bignum = ImageFont.truetype(FONT_BLD, 78)
    f_label = ImageFont.truetype(FONT_REG, 26)
    f_hint = ImageFont.truetype(FONT_REG, 24)

    # 4. 顶部品牌标识
    x0 = 90
    y0 = 90
    draw.rounded_rectangle([x0, y0, x0 + 32, y0 + 32], radius=6, fill=(26, 86, 196, 255))
    draw.rounded_rectangle([x0 + 42, y0, x0 + 74, y0 + 32], radius=6, fill=(243, 156, 18, 255))
    draw.rounded_rectangle([x0 + 84, y0, x0 + 116, y0 + 32], radius=6, fill=(46, 204, 113, 255))
    draw.text((x0 + 140, y0 - 2), "国民技术 · 品牌动态监控", font=f_brand, fill=(168, 197, 232, 255))

    # 5. 主标题（两行）
    draw_centered(draw, "半导体芯片行业", f_title, 220, (255, 255, 255, 255), W)
    draw_centered(draw, "动态简报", f_title, 350, (255, 255, 255, 255), W)

    # 标题左侧装饰条
    draw.rectangle([90, 490, 130, 498], fill=(26, 86, 196, 255))

    # 6. 副标题
    today = datetime.now().strftime("%Y-%m-%d")
    sub = f"{today} · 每日 8:00 / 13:00 / 20:00 实时更新"
    draw_centered(draw, sub, f_sub, 530, (192, 212, 236, 255), W)

    # 7. 数据卡片（3列，玻璃拟态）
    stats = [("44", "家竞品品牌"), ("6", "大板块"), ("7", "大渠道")]
    card_y = 640
    card_w = 280
    card_h = 200
    gap = 26
    total_w = card_w * 3 + gap * 2
    start_x = (W - total_w) / 2

    for i, (num, label) in enumerate(stats):
        x = start_x + i * (card_w + gap)
        cx = x + card_w / 2

        # 卡片半透明深色背景
        draw.rounded_rectangle(
            [x, card_y, x + card_w, card_y + card_h],
            radius=18, fill=(20, 35, 55, 180), outline=(120, 160, 210, 100), width=2
        )
        # 顶部小色条
        draw.rounded_rectangle(
            [x + 30, card_y + 22, x + 60, card_y + 28],
            radius=3, fill=(26, 86, 196, 255)
        )
        # 大数字（白）
        tw = text_width(draw, num, f_bignum)
        draw.text((cx - tw / 2, card_y + 48), num, font=f_bignum, fill=(255, 255, 255, 255))
        # 标签（淡蓝）
        tw = text_width(draw, label, f_label)
        draw.text((cx - tw / 2, card_y + 148), label, font=f_label, fill=(168, 197, 232, 255))

    # 8. 底部装饰条（6色彩条）
    colors = ['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#9b59b6', '#1a56c4']
    bar_h = 6
    bar_y = H - 120
    for i, color in enumerate(colors):
        x_start = int(W * i / len(colors))
        x_end = int(W * (i + 1) / len(colors))
        rgb = tuple(int(color[1:][j:j+2], 16) for j in (0, 2, 4))
        draw.rectangle([x_start, bar_y, x_end, bar_y + bar_h], fill=rgb + (255,))

    # 9. 底部提示文字
    draw_centered(draw, "扫码或点击查看完整品牌动态数据", f_hint, H - 80, (122, 156, 198, 255), W)

    # 保存（转 RGB）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "cover.png")
    final = img.convert('RGB')
    final.save(out_path, "PNG", optimize=True)
    print(f"封面图已生成: {out_path}")
    print(f"尺寸: {W}x{H}")
    print(f"文件大小: {os.path.getsize(out_path) / 1024:.1f} KB")


if __name__ == "__main__":
    generate_cover()
