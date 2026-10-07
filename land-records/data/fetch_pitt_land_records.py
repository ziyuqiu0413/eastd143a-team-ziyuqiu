"""Harvest metadata for the Pitt "Chinese Land Records" collection.

Source: https://digital.library.pitt.edu/collection/chinese-land-records
Uses the site's Drupal JSON (?_format=json) and IIIF manifests (/node/{nid}/manifest).
Outputs (next to this script):
  pitt_land_records_raw.json   full node JSON + canvas count per item
  pitt_land_records.csv        flattened, analysis-ready table
"""
import csv
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE = "https://digital.library.pitt.edu"
COLLECTION = "/collection/chinese-land-records"
OUT = Path(__file__).parent
S = requests.Session()
S.headers["User-Agent"] = f"python-requests/{requests.__version__} (Harvard DH hackathon)"


def get(url, **kw):
    for attempt in range(4):
        try:
            r = S.get(url, timeout=60, **kw)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed: {url}")


def member_paths():
    paths, page = [], 0
    while True:
        html = get(f"{BASE}{COLLECTION}", params={"items_per_page": 50, "page": f",{page}"}).text
        found = re.findall(r'href="(/islandora/object/pitt%3A[0-9A-Za-z_.-]+)"', html)
        new = [p for p in dict.fromkeys(found) if p not in paths]
        if not new:
            break
        paths += new
        page += 1
    return paths


def vals(node, field, key="value"):
    return [v.get(key) for v in node.get(field, []) if v.get(key) is not None]


term_cache = {}


def term_name(tid):
    if tid not in term_cache:
        try:
            term_cache[tid] = get(f"{BASE}/taxonomy/term/{tid}", params={"_format": "json"}).json()["name"][0]["value"]
        except Exception:
            term_cache[tid] = f"term:{tid}"
    return term_cache[tid]


def fetch_item(path):
    node = get(f"{BASE}{path}", params={"_format": "json"}).json()
    nid = node["nid"][0]["value"]
    try:
        manifest = get(f"{BASE}/node/{nid}/manifest").json()
        canvases = len(manifest.get("sequences", [{}])[0].get("canvases", []))
    except Exception:
        canvases = None
    return {"path": path, "nid": nid, "canvases": canvases, "node": node}


ROLE_RE = re.compile(r"^\s*([A-Za-z' ]+?)\s*:\s*(.+?)\s*$")
CJK_RE = re.compile(r"^(.*?)\s*\[(.*?)\]\s*$")


def parse_title(title):
    """'Seller: 許瓊栢 [XU Qiongbai] -- Buyer: ... -- Place: ... -- Government'"""
    out, tail = {}, []
    for part in re.split(r"\s*--\s*", title):
        m = ROLE_RE.match(part)
        if m:
            role = m.group(1).strip().lower().replace(" ", "_")
            out.setdefault(role, []).append(m.group(2))
        elif part.strip():
            tail.append(part.strip())
    out["_tail"] = tail
    return out


def split_cjk(s):
    m = CJK_RE.match(s or "")
    return (m.group(1).strip(), m.group(2).strip()) if m else (s, "")


def main():
    paths = member_paths()
    print("members found:", len(paths))
    with ThreadPoolExecutor(max_workers=4) as ex:
        items = list(ex.map(fetch_item, paths))
    (OUT / "pitt_land_records_raw.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")

    rows, roles_seen = [], set()
    for it in items:
        n = it["node"]
        title = (vals(n, "title") or [""])[0]
        parsed = parse_title(title)
        roles_seen.update(k for k in parsed if k != "_tail")
        place_zh, place_py = split_cjk((parsed.get("place") or [""])[0])
        row = {
            "pid": (vals(n, "field_pid") or [""])[0],
            "nid": it["nid"],
            "url": BASE + it["path"].replace("%3A", ":"),
            "title": title,
            "date_str": "; ".join(vals(n, "field_date_str")),
            "edtf_date": "; ".join(vals(n, "field_edtf_date")),
            "extent": "; ".join(vals(n, "field_extent")),
            "box_folder": "; ".join(vals(n, "field_source_location")),
            "pages_in_iiif": it["canvases"],
            "doc_kind": "; ".join(parsed["_tail"]),
            "place_zh": place_zh,
            "place_pinyin": place_py,
            "description": " | ".join(vals(n, "field_description")),
            "description_long": " | ".join(re.sub(r"<[^>]+>", " ", v) for v in vals(n, "field_description_long")),
            "note": " | ".join(re.sub(r"<[^>]+>", " ", v) for v in vals(n, "field_note")),
            "genre": "; ".join(term_name(t) for t in vals(n, "field_genre", "target_id")),
            "subjects": "; ".join(term_name(t) for t in vals(n, "field_subject", "target_id")),
            "geo_subjects": "; ".join(term_name(t) for t in vals(n, "field_geographic_subject", "target_id")),
            "member_of": "; ".join(str(t) for t in vals(n, "field_member_of", "target_id")),
        }
        for role in ("seller", "buyer", "owner", "lessor", "lessee", "mortgagor", "mortgagee", "grantor", "grantee"):
            if role in parsed:
                zh, py = zip(*(split_cjk(x) for x in parsed[role]))
                row[f"{role}_zh"], row[f"{role}_pinyin"] = "; ".join(zh), "; ".join(py)
        row["other_roles"] = "; ".join(
            f"{k}={'/'.join(v)}" for k, v in parsed.items()
            if k not in ("_tail", "place", "seller", "buyer", "owner", "lessor", "lessee", "mortgagor", "mortgagee", "grantor", "grantee")
        )
        rows.append(row)

    fields = list(dict.fromkeys(k for r in rows for k in r))
    with open(OUT / "pitt_land_records.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print("rows:", len(rows), "| roles in titles:", sorted(roles_seen))


if __name__ == "__main__":
    main()
