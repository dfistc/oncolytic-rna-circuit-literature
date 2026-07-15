from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "literature.csv"

QUERY = (
    '(oncolytic[Title/Abstract] OR virotherapy[Title/Abstract] OR "oncolytic virus"[Title/Abstract] '
    'OR reovirus[Title/Abstract] OR "vesicular stomatitis virus"[Title/Abstract] OR HSV-1[Title/Abstract]) '
    'AND (RNA[Title/Abstract] OR microRNA[Title/Abstract] OR miRNA[Title/Abstract] OR IRES[Title/Abstract] '
    'OR dsRNA[Title/Abstract] OR "gene circuit"[Title/Abstract] OR circuit[Title/Abstract] OR saRNA[Title/Abstract]) '
    'AND ("2024"[Date - Publication] : "3000"[Date - Publication])'
)

CNS_JOURNAL_PATTERNS = [
    r"^Nature$",
    r"^Science",
    r"^Cell$",
    r"^Nature ",
    r"^Cell ",
    r"^Cancer Cell$",
    r"^Molecular Cell$",
    r"^Immunity$",
    r"^Med$",
    r"^Science ",
    r"^Science Advances$",
    r"^Science Translational Medicine$",
    r"^Scientific Reports$",
]

FIELDNAMES = ["pmid", "year", "published", "journal", "tier", "doi", "title"]


def request_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def request_xml(url: str) -> ET.Element:
    with urllib.request.urlopen(url, timeout=45) as response:
        return ET.fromstring(response.read())


def text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def journal_is_in_scope(journal: str) -> bool:
    return any(re.search(pattern, journal, flags=re.IGNORECASE) for pattern in CNS_JOURNAL_PATTERNS)


def load_existing() -> list[dict[str, str]]:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save_rows(rows: list[dict[str, str]]) -> None:
    rows = sorted(rows, key=lambda row: row.get("published", ""), reverse=True)
    with CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def search_pmids() -> list[str]:
    params = urllib.parse.urlencode({"db": "pubmed", "retmode": "json", "retmax": "250", "term": QUERY})
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}"
    data = request_json(url)
    return data["esearchresult"].get("idlist", [])


def fetch_records(pmids: list[str]) -> list[dict[str, str]]:
    if not pmids:
        return []
    params = urllib.parse.urlencode({"db": "pubmed", "retmode": "xml", "id": ",".join(pmids)})
    root = request_xml(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?{params}")
    records: list[dict[str, str]] = []

    for article_node in root.findall("PubmedArticle"):
        med = article_node.find("MedlineCitation")
        article = med.find("Article") if med is not None else None
        if med is None or article is None:
            continue

        pmid = text(med.find("PMID"))
        title = text(article.find("ArticleTitle"))
        journal = text(article.find("Journal/Title"))
        if not journal_is_in_scope(journal):
            continue

        pubdate = article.find("Journal/JournalIssue/PubDate")
        year = text(pubdate.find("Year") if pubdate is not None else None)
        month = text(pubdate.find("Month") if pubdate is not None else None)
        day = text(pubdate.find("Day") if pubdate is not None else None)
        if not year:
            medline_date = text(pubdate.find("MedlineDate") if pubdate is not None else None)
            year = medline_date[:4]
        published = "-".join(part for part in [year, month, day] if part)

        doi = ""
        for article_id in article_node.findall("PubmedData/ArticleIdList/ArticleId"):
            if article_id.attrib.get("IdType") == "doi":
                doi = text(article_id)
                break

        records.append(
            {
                "pmid": pmid,
                "year": year[:4],
                "published": published,
                "journal": journal,
                "tier": "待核对",
                "doi": doi,
                "title": title,
            }
        )

    return records


def main() -> None:
    rows = load_existing()
    existing_pmids = {row["pmid"] for row in rows}
    pmids = search_pmids()
    time.sleep(0.4)
    candidates = fetch_records(pmids)
    new_rows = [record for record in candidates if record["pmid"] not in existing_pmids]

    if new_rows:
        rows.extend(new_rows)
        save_rows(rows)
        print(f"Added {len(new_rows)} new candidate records.")
    else:
        print("No new candidate records found.")


if __name__ == "__main__":
    main()
