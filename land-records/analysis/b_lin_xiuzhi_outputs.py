"""Build reader-facing outputs for household B (林修枝, 林森縣, 1947).

Inputs : data/households/B_linsen_lin_xiuzhi.json, students_documents_export/images/<barcode>_001.jpg
Outputs: data/households/B_linsen_lin_xiuzhi_ocr.md      9 transcriptions ordered by licence number
         data/households/B_linsen_lin_xiuzhi_parcels.csv  one row per parcel
         data/households/B_linsen_lin_xiuzhi_parcels.jpg  contact sheet of the 9 hand-drawn parcel sketches
"""
import csv
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
HH = ROOT / "data" / "households"
IMAGES = ROOT / "students_documents_export" / "images"
FONT = "C:/Windows/Fonts/msyh.ttc"

CN = {"零": 0, "壹": 1, "貳": 2, "叁": 3, "參": 3, "肆": 4, "伍": 5, "陸": 6, "柒": 7, "捌": 8, "玖": 9}


def mu(s):
    """'壹畝玖分伍厘' -> 1.95"""
    m = re.search(r"(.)畝(.)分(.)厘", s or "")
    return round(CN[m[1]] + CN[m[2]] / 10 + CN[m[3]] / 100, 2) if m else None


def yuan(s):
    """'壹元貳角柒分' -> 1.27"""
    m = re.search(r"(.)元(.)角(.)分", s or "")
    return round(CN[m[1]] + CN[m[2]] / 10 + CN[m[3]] / 100, 2) if m else None


def main():
    data = json.loads((HH / "B_linsen_lin_xiuzhi.json").read_text(encoding="utf-8"))
    rows = []
    for d in data["docs"]:
        p = d.get("property") or {}
        ids = p.get("parcel_ids") or ""
        lic = re.search(r"執照號西字第0*(\d+)號", ids)
        lot = re.search(r"第(\d+)段第(\d+)(\[\?\])?號", ids)
        grade = re.search(r"(\S+?)地?〕?(\S)等〔?(\S)則", d.get("transcription", ""))
        rows.append({
            "licence_no": int(lic[1]) if lic else None,
            "nid": d["nid"], "pid": d["pid"],
            "toponym": p.get("toponym"),
            "section": int(lot[1]) if lot else None,
            "lot_no": (lot[2] + (lot[3] or "")) if lot else None,
            "land_class": next((k for k in ("農地", "基地", "蕩地", "田") if k in (p.get("kind") or "")), p.get("kind")),
            "area_text": p.get("size"), "area_mu": mu(p.get("size")),
            "tax_text": p.get("tax_or_rent"), "tax_yuan": yuan(p.get("tax_or_rent")),
            "confidence": d.get("confidence"),
            "transcription": d.get("transcription", ""),
        })
    rows.sort(key=lambda r: r["licence_no"] or 0)

    with open(HH / "B_linsen_lin_xiuzhi_parcels.csv", "w", newline="", encoding="utf-8-sig") as f:
        cols = [k for k in rows[0] if k != "transcription"]
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    lines = ["# 林修枝土地管業執照 OCR 全文（9 件，民國36年4月）", "",
             "按執照號排序。〔〕內為手寫或戳記填寫，其餘為印刷；□ 為不能識讀，[?] 為沒有把握。原件豎排、由右向左讀，這裡每列一行。", ""]
    for r in rows:
        lines += [f"## 西字第{r['licence_no']:06d}號 · {r['toponym']} · {r['area_text']}",
                  f"`{r['pid']}` · nid {r['nid']} · 識讀信心 {r['confidence']}", "", "```text", r["transcription"].strip(), "```", ""]
    (HH / "B_linsen_lin_xiuzhi_ocr.md").write_text("\n".join(lines), encoding="utf-8")

    # contact sheet of parcel sketches (drawing box only; sketches are NOT to a common scale)
    tw, th, cap = 420, 360, 96
    font, small = ImageFont.truetype(FONT, 24), ImageFont.truetype(FONT, 19)
    slots = rows[:]
    slots.insert(next(i for i, r in enumerate(rows) if r["licence_no"] > 5592), None)
    sheet = Image.new("RGB", (tw * 5, (th + cap) * 2 + 60), "white")
    dr = ImageDraw.Draw(sheet)
    dr.text((14, 12), "林修枝名下九坵地的「圖略」（1947，福建省林森縣；各圖比例不同，僅示形狀）", fill="black", font=font)
    for i, r in enumerate(slots):
        x, y = (i % 5) * tw, 60 + (i // 5) * (th + cap)
        if r is None:
            dr.rectangle([x + 10, y + 10, x + tw - 10, y + th - 10], outline="#bbb", width=2)
            dr.text((x + 20, y + th // 2 - 30), "西字第005592號\n（館藏缺）", fill="#888", font=font)
            continue
        im = Image.open(IMAGES / f"{r['pid'].removeprefix('pitt:')}_001.jpg").convert("RGB")
        w, h = im.size
        im = im.crop((int(w * 0.345), int(h * 0.72), int(w * 0.67), int(h * 0.91)))  # the 圖略 box on this form
        im.thumbnail((tw - 20, th - 20))
        sheet.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        dr.text((x + 14, y + th + 2), f"西字第{r['licence_no']:06d}號  {r['toponym']}", fill="black", font=font)
        dr.text((x + 14, y + th + 36), f"第{r['section']}段 {r['lot_no']}號 · {r['land_class']} · {r['area_mu']}畝 · 賦{r['tax_yuan']}元", fill="#333", font=small)
    sheet.save(HH / "B_linsen_lin_xiuzhi_parcels.jpg", quality=90)

    print(f"parcels: {len(rows)} | total {sum(r['area_mu'] for r in rows):.2f} mu, {sum(r['tax_yuan'] for r in rows):.2f} yuan")
    for r in rows:
        print(r["licence_no"], r["toponym"], r["section"], r["lot_no"], r["land_class"], r["area_mu"], r["tax_yuan"],
              round(r["tax_yuan"] / r["area_mu"], 3))


if __name__ == "__main__":
    main()
