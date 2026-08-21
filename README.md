# 半导体芯片行业品牌热度仪表盘

国民技术市场品牌单元 · 竞品品牌动态监控仪表盘。

## 自动化说明

- **刷新频率**：每天 **8:00 / 13:00 / 20:00**（北京时间），由 GitHub Actions 定时触发。
- **数据源**：
  - 43 家竞品品牌 + 2 个主题板块的 **Bing 搜索结果数**（搜索热度）
  - 17 家上市公司的 **Yahoo Finance 股价数据**（美股 / A股 / 日股 / 德股 / 台股 / 挪威股）
- **数据持久化**：每次刷新后，`brand_metrics.json` 与 `daily/` 日报自动 commit 回本仓库，历史持续累积。
- **部署**：生成的 `dashboard/` 自动发布到 GitHub Pages，链接永久固定。

## 目录结构

| 路径 | 说明 |
|------|------|
| `fetch_brand_metrics.py` | 采集 Bing 搜索热度 + Yahoo 股价，输出 `brand_metrics.json` |
| `generate_dashboard.py` | 读取 `brand_metrics.json` + 最新日报，生成 `dashboard/index.html` |
| `generate_cover.py` | 生成微信分享卡片封面图 `dashboard/cover.png` |
| `daily/` | 竞品日报存档（`.md`） |
| `.github/workflows/refresh.yml` | 定时刷新工作流 |

## 字体

封面图使用 **思源黑体（Noto Sans CJK）**，SIL OFL 免商用授权，工作流内自动安装。

## 本地运行

```bash
pip install -r requirements.txt
python fetch_brand_metrics.py      # 采集（约 6-8 分钟）
python generate_dashboard.py       # 生成仪表盘
```
