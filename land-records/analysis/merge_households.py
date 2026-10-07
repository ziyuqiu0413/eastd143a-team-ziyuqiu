"""Merge per-household reading outputs into flat tables.

Inputs : data/households/<cluster>[_partN].json  (written by the reading tasks, schema in READING_GUIDE.md)
Outputs: data/households/all_docs.csv      one row per document
         data/households/all_parties.csv   one row per person mentioned in a document
         data/households/all_timeline.csv  one row per property-transfer / registration event
Tolerates small schema differences between tasks (e.g. timeline key names).
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HH = ROOT / "data" / "households"


def first(d, *keys):
    for k in keys:
        if d.get(k) not in (None, "", []):
            return d[k]
    return None


def text(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return "; ".join(text(x) for x in v)
    if isinstance(v, dict):
        return "; ".join(f"{k}={text(x)}" for k, x in v.items() if x not in (None, ""))
    return str(v)


def main():
    docs, parties, timeline, seen = [], [], [], set()
    for f in sorted(HH.glob("*.json")):
        if f.name in ("clusters.json",) or f.name.startswith("all_"):
            continue
        data = json.loads(f.read_text(encoding="utf-8"))
        cluster = data.get("cluster", f.stem)
        for d in data.get("docs", []):
            if d.get("pid") in seen:  # a document read twice (e.g. split parts) keeps its first reading
                continue
            seen.add(d.get("pid"))
            p, price = d.get("property") or {}, d.get("price") or {}
            docs.append({
                "cluster": cluster, "source_file": f.name, "pid": d.get("pid"), "nid": d.get("nid"),
                "page_count": d.get("page_count"), "doc_type": d.get("doc_type"),
                "date_original": text(d.get("date_original")), "date_gregorian": text(d.get("date_gregorian")),
                "date_vs_metadata": text(d.get("date_vs_metadata")),
                "property_kind": text(p.get("kind")), "toponym": text(p.get("toponym")),
                "location": text(p.get("location")), "size": text(p.get("size")),
                "tax_or_rent": text(p.get("tax_or_rent")), "parcel_ids": text(p.get("parcel_ids")),
                "title_origin": text(d.get("title_origin")),
                "price_amount": price.get("amount"), "price_unit": price.get("unit"),
                "price_currency": price.get("currency"), "price_text": text(price.get("original_text")),
                "clauses": text(d.get("clauses")), "legibility": d.get("legibility"),
                "confidence": d.get("confidence"), "notes": text(d.get("notes")),
            })
            for q in d.get("parties") or []:
                parties.append({
                    "cluster": cluster, "pid": d.get("pid"), "name": q.get("name"), "role": q.get("role"),
                    "relation_stated": text(q.get("relation_stated")), "evidence": text(q.get("evidence")),
                })
        tl = (data.get("synthesis") or {}).get("timeline") or []
        for e in tl if isinstance(tl, list) else []:
            timeline.append({
                "cluster": cluster, "source_file": f.name,
                "date": text(first(e, "date", "time")),
                "from": text(first(e, "from", "grantor")), "to": text(first(e, "to", "grantee")),
                "property": text(first(e, "parcel", "property", "object")),
                "mode": text(first(e, "mode", "method", "event", "type")),
                "price": text(e.get("price")), "relation": text(e.get("relation")),
                "evidence": text(first(e, "pid", "docs", "evidence", "source")),
            })

    for name, rows in (("all_docs.csv", docs), ("all_parties.csv", parties), ("all_timeline.csv", timeline)):
        if not rows:
            continue
        with open(HH / name, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    clusters = sorted({d["cluster"] for d in docs})
    print(f"clusters: {clusters}\ndocs: {len(docs)} | parties: {len(parties)} | timeline events: {len(timeline)}")


if __name__ == "__main__":
    main()
