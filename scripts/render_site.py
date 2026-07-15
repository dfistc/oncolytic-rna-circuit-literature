from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX_PATH = ROOT / "index.html"
CSV_PATH = ROOT / "data" / "literature.csv"


def load_csv_rows() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def extract_existing_papers(html: str) -> list[dict[str, object]]:
    match = re.search(r"const papers = (\[[\s\S]*?\]);\n\n    const allTier", html)
    if not match:
        raise RuntimeError("Cannot find papers block in index.html")

    block = match.group(1)
    try:
        parsed = json.loads(block)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass

    # The hand-authored first version used JavaScript object literals. Keep a
    # conservative extractor so rich Chinese annotations survive the first
    # render, then future renders use the JSON branch above.
    items: list[dict[str, object]] = []
    for item_match in re.finditer(r"\{\n([\s\S]*?)\n      \}(?=,?\n)", block):
        chunk = item_match.group(1)
        item: dict[str, object] = {}
        for field in ["pmid", "published", "journal", "tier", "motif", "title", "titleZh", "doi", "pubmedUrl", "doiUrl", "standard", "summaryZh"]:
            field_match = re.search(rf'{field}: "([\s\S]*?)"', chunk)
            if field_match:
                item[field] = field_match.group(1)
        year_match = re.search(r"year: (\d{4})", chunk)
        if year_match:
            item["year"] = int(year_match.group(1))
        terms_match = re.search(r"matchedTerms: \[([\s\S]*?)\]", chunk)
        if terms_match:
            item["matchedTerms"] = re.findall(r'"([^"]+)"', terms_match.group(1))
        if item.get("pmid"):
            items.append(item)
    return items


def default_item(row: dict[str, str]) -> dict[str, object]:
    pmid = row["pmid"]
    doi = row.get("doi", "")
    title = row.get("title", "")
    return {
        "pmid": pmid,
        "year": int(row.get("year") or 0),
        "published": row.get("published", ""),
        "journal": row.get("journal", ""),
        "tier": row.get("tier") or "待核对",
        "motif": "自动候选 / 待人工归类",
        "title": title,
        "titleZh": "中文题名待核对",
        "doi": doi,
        "pubmedUrl": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        "doiUrl": f"https://doi.org/{doi}" if doi else "",
        "matchedTerms": ["auto-update", "PubMed candidate"],
        "standard": "每周自动检索发现的候选记录，已通过标题/摘要关键词和期刊范围初筛，需人工确认是否严格属于溶瘤病毒 RNA 基因线路。",
        "summaryZh": "该条目由自动更新程序加入。建议打开 DOI 或 PubMed 原文，补充中文题名、线路模块、纳入理由和设计启示后再改为核心、强相关或启发。",
    }


def main() -> None:
    html = INDEX_PATH.read_text(encoding="utf-8")
    existing = {str(item["pmid"]): item for item in extract_existing_papers(html)}
    merged: list[dict[str, object]] = []

    for row in load_csv_rows():
        pmid = row["pmid"]
        item = existing.get(pmid, default_item(row))
        item["year"] = int(row.get("year") or item.get("year") or 0)
        item["published"] = row.get("published") or str(item.get("published", ""))
        item["journal"] = row.get("journal") or str(item.get("journal", ""))
        item["tier"] = row.get("tier") or str(item.get("tier", "待核对"))
        item["doi"] = row.get("doi") or str(item.get("doi", ""))
        item["title"] = row.get("title") or str(item.get("title", ""))
        merged.append(item)

    payload = json.dumps(merged, ensure_ascii=False, indent=6)
    new_html = re.sub(
        r"const papers = \[[\s\S]*?\];\n\n    const allTier",
        f"const papers = {payload};\n\n    const allTier",
        html,
        count=1,
    )
    INDEX_PATH.write_text(new_html, encoding="utf-8")
    print(f"Rendered {len(merged)} records into {INDEX_PATH}")


if __name__ == "__main__":
    main()
