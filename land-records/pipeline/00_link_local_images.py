"""Link the course-provided image export to the harvested metadata.

Images: students_documents_export/images/<barcode>_<NNN>.jpg   (barcode = pid without "pitt:", NNN = 1-based page)
Inputs: data/pitt_land_records.csv (left untouched)
Outputs:
  data/pitt_land_records_linked.csv  the records table plus n_local_images, local_images (";"-joined relative paths)
  data/pitt_land_records_pages.csv   one row per image with record metadata, page number, pixel size
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
IMG_DIR = ROOT / "students_documents_export" / "images"
RECORDS = ROOT / "data" / "pitt_land_records.csv"
LINKED = ROOT / "data" / "pitt_land_records_linked.csv"
PAGES = ROOT / "data" / "pitt_land_records_pages.csv"
NAME = re.compile(r"^(?P<barcode>[0-9A-Za-z-]+)_(?P<page>\d{3})\.jpg$", re.I)


def main():
    pages = defaultdict(list)
    unmatched_names = []
    for f in sorted(IMG_DIR.iterdir()):
        m = NAME.match(f.name)
        if m:
            pages[m["barcode"]].append((int(m["page"]), f))
        else:
            unmatched_names.append(f.name)

    with open(RECORDS, encoding="utf-8-sig", newline="") as fh:
        records = list(csv.DictReader(fh))
    fields = [k for k in records[0] if k not in ("n_local_images", "local_images")]
    fields[fields.index("pages_in_iiif") + 1:fields.index("pages_in_iiif") + 1] = ["n_local_images", "local_images"]

    page_rows, mismatched = [], []
    by_barcode = {}
    for r in records:
        barcode = r["pid"].removeprefix("pitt:")
        by_barcode[barcode] = r
        imgs = sorted(pages.get(barcode, []))
        r["n_local_images"] = len(imgs)
        r["local_images"] = ";".join(f.relative_to(ROOT).as_posix() for _, f in imgs)
        if r["pages_in_iiif"] and int(r["pages_in_iiif"]) != len(imgs):
            mismatched.append((r["pid"], r["pages_in_iiif"], len(imgs)))
        for n, f in imgs:
            with Image.open(f) as im:
                w, h = im.size
            page_rows.append({
                "pid": r["pid"], "barcode": barcode, "nid": r["nid"], "page": n,
                "image_path": f.relative_to(ROOT).as_posix(), "width": w, "height": h,
                "title": r["title"], "edtf_date": r["edtf_date"], "place_zh": r["place_zh"],
                "doc_kind": r["doc_kind"], "box_folder": r["box_folder"], "url": r["url"],
            })

    with open(LINKED, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(records)
    with open(PAGES, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(page_rows[0]))
        w.writeheader()
        w.writerows(page_rows)

    orphans = sorted(set(pages) - set(by_barcode))
    no_images = [r["pid"] for r in records if not r["n_local_images"]]
    print(f"records: {len(records)} | with images: {len(records) - len(no_images)} | images linked: {len(page_rows)}")
    print("records without images:", no_images)
    print("image barcodes without a record:", orphans)
    print("page-count mismatches vs IIIF:", mismatched)
    print("unparsed file names:", unmatched_names)


if __name__ == "__main__":
    main()
