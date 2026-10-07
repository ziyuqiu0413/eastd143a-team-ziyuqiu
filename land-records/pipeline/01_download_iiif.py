"""Download IIIF page images for selected Pitt land-record nodes.

Usage:
  python pipeline/01_download_iiif.py --clusters data/households/clusters.json [--width 1600]
  python pipeline/01_download_iiif.py --nids 83869 83874 ...

Writes data/images/<pid>/<pid>-NNNN.jpg and data/images/index.json
(index keeps each page's IIIF service URL so zoomed crops can be requested later:
 {service}/pct:x,y,w,h/1600,/0/default.jpg).
"""
import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

BASE = "https://digital.library.pitt.edu"
ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "data" / "images"
S = requests.Session()
S.headers["User-Agent"] = f"python-requests/{requests.__version__} (Harvard DH hackathon)"


def get(url, timeout=60):
    for attempt in range(5):
        try:
            r = S.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"failed after retries: {url}")


def pages_for(nid):
    m = get(f"{BASE}/node/{nid}/manifest").json()
    pid = None
    pages = []
    for i, c in enumerate(m["sequences"][0]["canvases"], 1):
        svc = c["images"][0]["resource"]["service"]["@id"]
        label = c.get("label", "")
        pid = pid or label.rsplit("-", 1)[0]
        pages.append({"n": i, "label": label, "service": svc, "width": c["width"], "height": c["height"]})
    return {"nid": nid, "pid": pid, "title": m.get("label"), "pages": pages}


def download(doc, width):
    out = IMG_DIR / doc["pid"].replace(":", "_")
    out.mkdir(parents=True, exist_ok=True)
    for p in doc["pages"]:
        f = out / f"{doc['pid'].replace(':', '_')}-{p['n']:04d}.jpg"
        if not f.exists():
            f.write_bytes(get(f"{p['service']}/full/{width},/0/default.jpg", timeout=180).content)
        p["file"] = str(f.relative_to(ROOT)).replace("\\", "/")
    return doc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clusters")
    ap.add_argument("--nids", nargs="*", type=int, default=[])
    ap.add_argument("--width", type=int, default=1600)
    a = ap.parse_args()
    nids = list(a.nids)
    if a.clusters:
        for g in json.loads(Path(a.clusters).read_text(encoding="utf-8")).values():
            nids += [d["nid"] for d in g["docs"]]
    nids = list(dict.fromkeys(nids))

    with ThreadPoolExecutor(max_workers=4) as ex:
        docs = list(ex.map(pages_for, nids))
        docs = list(ex.map(lambda d: download(d, a.width), docs))

    idx_path = IMG_DIR / "index.json"
    index = json.loads(idx_path.read_text(encoding="utf-8")) if idx_path.exists() else {}
    index.update({str(d["nid"]): d for d in docs})
    idx_path.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"docs: {len(docs)} | images: {sum(len(d['pages']) for d in docs)}")


if __name__ == "__main__":
    main()
