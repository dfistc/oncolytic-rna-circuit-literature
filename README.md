# 溶瘤病毒 RNA 基因线路文献地图

这是一个独立静态网页，直接打开 `index.html` 即可使用；也可以双击 `打开网站.cmd`。

检索范围：2024-01-01 至 2026-07-15，聚焦 Cell、Nature、Science 正刊及系列子刊中与溶瘤病毒、RNA 调控、miRNA 靶序列、IRES、dsRNA 传感、saRNA 和可控递送相关的记录。

页面采用和现有文献库相近的浅绿背景、筛选栏、统计块和论文卡片结构，并额外增加了证据等级、线路模块、纳入理由和设计启示字段。默认排序为发表时间最新在前。

文件说明：

- `index.html`：可离线打开的完整网页，内嵌样式、交互脚本和文献卡片数据。
- `data/literature.csv`：文献基础表，方便核对 PMID、DOI、期刊和证据等级。
- `docs/检索说明.md`：检索范围、纳入标准和为什么分成核心/强相关/启发。
- `scripts/update_literature.py`：从 PubMed 检索 2024 年以来的新候选文献并更新 CSV。
- `scripts/render_site.py`：把 CSV 中新增的候选文献同步进网页。
- `.github/workflows/weekly-update.yml`：每周自动运行更新程序，有变化时自动提交。
- `.github/workflows/pages.yml`：推送到 GitHub 后自动发布 GitHub Pages。
- `打开网站.cmd`：Windows 下双击打开网页。

## 本地更新

```powershell
python scripts/update_literature.py
python scripts/render_site.py
```

自动新增的文献会标为“待核对”，方便后续人工补中文题名、线路模块和设计启示。
