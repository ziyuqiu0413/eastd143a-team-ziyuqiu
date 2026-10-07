"""Export everything the demo page needs into app/data.js (window.APP_DATA = {...}).

Run after analysis/merge_households.py whenever household results change:
    python analysis/merge_households.py && python analysis/export_app_data.py
Images are referenced by relative path (../students_documents_export/images/...) and never copied.
"""
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA, HH, APP = ROOT / "data", ROOT / "data" / "households", ROOT / "app"
IMG = "../students_documents_export/images"


def read_csv(p):
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def img(pid, page=1):
    return f"{IMG}/{pid.removeprefix('pitt:')}_{int(page):03d}.jpg"


def first_year(s):
    m = re.search(r"\d{4}", s or "")
    return int(m[0]) if m else None


# ---------- 1. collection overview ----------
def overview():
    rows = [r for r in read_csv(DATA / "pitt_land_records.csv") if r["genre"] == "records (documents)"]
    periods = [("明", 0, 1644), ("清", 1644, 1912), ("民國", 1912, 1949), ("1949後", 1949, 2100)]
    by_period = {p: Counter() for p, *_ in periods}
    by_decade = defaultdict(Counter)
    for r in rows:
        y = first_year(r["edtf_date"])
        kind = r["doc_kind"] if r["doc_kind"] in ("Government", "Personal") else "Other"
        if y is None:
            continue
        by_decade[y // 25 * 25][kind] += 1
        for p, a, b in periods:
            if a <= y < b:
                by_period[p][kind] += 1
    places = Counter()
    fuzhou = ("閩侯", "閩縣", "侯官", "林森", "閩邑")
    for r in rows:
        pz = r["place_zh"] or ""
        if any(k in pz for k in fuzhou):
            places["福州周邊（閩縣・侯官・閩侯・林森）"] += 1
        elif "福建" in pz:
            m = re.search(r"福建[省聲]?(.+?[縣邑])", pz)
            places[(m[1] if m else "福建（縣不詳）")] += 1
        elif not pz or pz.lower() in ("unknown", "n/a") or "unknown" in pz.lower():
            places["地點不詳"] += 1
        else:
            places["福建省外"] += 1
    years = [first_year(r["edtf_date"]) for r in rows if first_year(r["edtf_date"])]
    pairs = [(r["seller_zh"].strip(), r["buyer_zh"].strip()) for r in rows
             if (r.get("seller_zh") or "").strip() and (r.get("buyer_zh") or "").strip()]
    same = sum(s[0] == b[0] for s, b in pairs)
    return {
        "n_docs": len(rows), "n_pages": sum(int(r["pages_in_iiif"] or 0) for r in rows),
        "year_min": min(years), "year_max": max(years), "n_dated": len(years),
        "by_period": [{"period": p, **by_period[p]} for p, *_ in periods],
        "by_quarter_century": [{"start": k, **v} for k, v in sorted(by_decade.items())],
        "places": places.most_common(),
        "gov_share": round(sum(r["doc_kind"] == "Government" for r in rows) / len(rows), 3),
        "same_surname": {"same": same, "pairs": len(pairs)},
    }


# ---------- 2. genealogy of title documents (curated, each checked against the image) ----------
GENEALOGY = [
    ("清", 1761, "紅契", "pitt:31735064607538", 1, "許瓊栢賣山埔土窨契",
     "民間立契，經縣衙鈐印納稅，成為「紅契」。乾隆二十六年，價銀三十兩。"),
    ("清", 1805, "契尾", "pitt:31735064607660", 1, "劉咸安買劉盛章房",
     "布政使司頒發的完稅憑證，黏在原契之後；建陽劉氏三件契尾都按 3% 收稅。"),
    ("清", 1887, "白契", "pitt:31735064607470", 1, "王錦發賣斷店屋與堂兄",
     "未經官府鈐印的民間契約。賣的是祖遺分得的店屋，買主是堂兄。"),
    ("民國", 1923, "納戶執照", "pitt:31735066237581", 3, "黃遠容戶地丁銀收據",
     "永泰縣知事發給的完納地丁銀收據。戶名長年沿用「黃遠容」，看不出代際轉移。"),
    ("民國", 1945, "田賦征實收據", "pitt:31735066266481", 1, "黃生官田賦征實征借",
     "抗戰時期田賦改徵實物，並「征借」糧食，約定日後抵賦、不付谷息。"),
    ("民國", 1947, "土地管業執照", "pitt:31735066266226", 1, "林修枝・白龍厝前",
     "土地陳報後一坵一照，載段號、地目等則、面積、賦額，並附圖略。"),
    ("民國", 1947, "官印賣契本契", "pitt:31735066267935", 1, "陳朝寳賣田",
     "縣政府與田賦糧食管理處印發的官契紙。賣價二十五萬元法幣，契稅 6%。"),
    ("1949年後", 1953, "土地房產所有證", "pitt:31735066267661", 1, "川南區榮縣藍福良",
     "依《土地改革法》第三十條頒發，頂端印毛澤東像。"),
]

# ---------- 3. households (summaries written from findings checked against the originals) ----------
HOUSEHOLDS = {
    "C_minhou_lin_wankai": {
        "title": "閩侯／侯官　林萬開", "span": "1875–1913", "status": "done",
        "lede": "九件文書是林萬開一家的產權檔案：先從族人手中買進、承典田產，1891 年三兄弟拈鬮分家，1913 年再把舊契拿去民國驗契。",
        "points": [
            ("原文", "1891 年鬮書：「立鬮書林萬開偕弟萬拱萬欽」，「將承父遺物業及手置田園……除撥長子長孫份外……按照福祿壽三房勻作三股均分拈鬮為定」。"),
            ("原文", "族內流入：族兄應香賣斷（1875），族叔春發賣田根（1882），堂兄秋溥轉典白龍田面五號（1884）。"),
            ("原文", "萬開早年買進的田，1891 年分別歸入長子長孫份和福房，和祖遺產業一起被分——家長置產屬於全家。"),
            ("原文", "1913 年兩件是民國驗契契單，呈驗的就是 1875 年那張原契，不是新交易。"),
            ("待核", "館方標題有誤：1888 年契尾寫「業戶林萬開買林秋溥田」，方向弄反；「官方政府」實為承典人姓官；「王聯鄧」是中證王聯登。"),
        ],
    },
    "CB_chain": {
        "title": "跨組鏈　林萬開 → 林修枝", "span": "1875–1947", "status": "inferred",
        "lede": "兩組原本各自獨立的文書，土名與面積對上了：林修枝很可能是林萬開長房的後人。這是本項目唯一一條跨越清末到民國後期的代際鏈。",
        "points": [
            ("原文", "1891 年鬮書「長子長孫份下」：井嘴 1 畝 3 分、馬路下 1 畝 2 分、坑裡 1 畝。"),
            ("原文", "1947 年林修枝的管業執照：馬路下田 1.20 畝（第 5 段第 19 號），坑裡 1.10 畝；其餘土名還有馬坑、白龍。"),
            ("推測", "同一土名、面積相同，地點同在侯官（即後來的閩侯、林森縣）——推測是同一塊地，由長房傳到林修枝手上。"),
            ("局限", "原文沒有寫林修枝與林萬開的關係；1913 年到 1947 年之間的分家、繼承文書館藏裡沒有。"),
        ],
        "events": [
            {"date": "1875年12月（光緒元年）", "from": "林應香", "to": "林萬開", "mode": "賣斷馬路下・井嘴根面全田，官丈 2.33 畝", "price": "錢 108 千文", "relation": "族兄（原文）", "evidence": "pitt:31735064607785"},
            {"date": "1891年（光緒十七年八月）", "from": "萬開・萬拱・萬欽三兄弟", "to": "長子長孫份", "mode": "鬮書分家：井嘴 1.3 畝、馬路下 1.2 畝、坑裡 1 畝", "price": "", "relation": "兄弟分家（原文）", "evidence": "pitt:31735064607645"},
            {"date": "1913年12月（民國二年）", "from": "", "to": "業戶林萬開", "mode": "舊契呈驗、領驗契契單：草市都馬坑 2.3 畝", "price": "", "relation": "", "evidence": "pitt:31735064607694"},
            {"date": "1947年4月（民國三十六年）", "from": "", "to": "林修枝", "mode": "土地管業執照：馬路下 1.20 畝、坑裡 1.10 畝", "price": "", "relation": "同土名同面積（推測同一塊地）", "evidence": "pitt:31735066266176 pitt:31735066266218"},
        ],
    },
    "B_linsen_lin_xiuzhi": {
        "title": "林森縣　林修枝", "span": "1947", "status": "done",
        "lede": "九張《土地管業執照》，一坵一照、連號發給。林修枝名下共 6.83 畝，水田佔 76%，另有三塊屋基。",
        "points": [
            ("原文", "九張執照同在民國三十六年四月發給，執照號西字第 5584–5593（缺 5592）。"),
            ("原文", "同村王鐘鈞的執照號是 5598、5599；兩家「馬路下」的田地號相連（第 5 段第 19、20 號）。"),
            ("推算", "多張執照反推 1947 年賦率：每畝壹等中則 0.65 元、壹等下則 0.60 元、貳等上則 0.50 元。"),
            ("局限", "表格沒有「來歷」欄，單看執照看不出前手；但與林萬開的 1891 年鬮書對讀，可推出馬路下、坑裡兩坵的來歷（見「跨組鏈」）。"),
        ],
    },
    "B2_linsen_huang": {
        "title": "林森縣扈[?]嶼鄉　黃生官・黃克動", "span": "1945–1947", "status": "done",
        "lede": "同一份產業先出現在田賦收據上，兩年後出現在管業執照上，面積前後一致。",
        "points": [
            ("原文", "黃生官：1945 年收據記田 5 畝 2 分，1947 年執照記 5.20 畝（壹等中則，賦額 3.38 元）。"),
            ("原文", "黃克動的收據和執照上，代理人、代表人都是黃生官。"),
            ("推測", "兩人應是一家（父子或兄弟），原文沒有寫明關係。"),
        ],
        "events": [
            {"date": "1945（民國34年下期）", "from": "", "to": "黃生官", "mode": "田賦征實征借收據", "price": "", "relation": "", "evidence": "pitt:31735066266481"},
            {"date": "1946（民國35年下期）", "from": "", "to": "黃克動（代理人黃生官）", "mode": "田賦收據・本年度豁免半數", "price": "", "relation": "代理人（原文）", "evidence": "pitt:31735066266432"},
            {"date": "1947", "from": "", "to": "黃克動（代表人黃生官）", "mode": "土地管業執照", "price": "", "relation": "代表人（原文）", "evidence": "pitt:31735066237771"},
            {"date": "1947", "from": "", "to": "黃生官", "mode": "土地管業執照・田 5.20 畝", "price": "賦額 3.38 元", "relation": "", "evidence": "pitt:31735066266333"},
        ],
    },
    "F_jianyang_liu": {
        "title": "建陽縣　劉氏", "span": "1782–1935", "status": "done",
        "lede": "七件文書不屬同一家族，但其中藏著三段寫明親屬關係的族內流轉。",
        "points": [
            ("原文", "1797–1805：劉盛章把水北永興社的朽房屋地基賣給「本族」咸安、道建，增找紋銀八兩，再投稅領契尾。"),
            ("原文", "1910：劉嘉命把祖遺、分家分到的坪基菜園賣給「本村堂孫」劉源森，族內跨兩代。"),
            ("原文", "1935：曾祖劉廷極道光年間置的祀田，由四個曾孫共同持有；舊契毀於太平天國戰亂，按縣驗契辦法補立新契。"),
            ("局限", "館方把「建陽、劉姓、有官印」的單件排在一起，不能連成一條 1782–1935 年的家族鏈。"),
        ],
    },
    "A_yongtai_huang": {
        "title": "永泰縣　黃氏", "span": "1917–1931", "status": "done",
        "lede": "57 頁全是完糧收據，沒有一件契約。8 個戶名的稅總是同批繳清，同一筆稅還會換到另一個兄弟名下。",
        "points": [
            ("原文", "1924 年 12 月一批連號收據（842、849–860 號）一次補清民國 11、12 年欠糧，涉及遠容、乞容、同華、同德、同義、國興多戶。"),
            ("原文", "精確到「毫」的同一筆稅「伍分伍釐柒毫」：1920 年記在黃同華名下，1922–23 年記在黃同義名下，1926 年又回到黃同華名下。"),
            ("推測", "收據上的戶名只是繳納標籤，在兄弟之間流動，不等於業主；稅由一人統一代辦。"),
            ("推測", "「遠→同→國」像三代字輩，但原件沒有親屬稱謂，哪一輩在前也無法確定。"),
            ("局限", "全部收據沒有推收、過戶字樣，稅額長期不變；官府收據上看不到產權的代際轉移。"),
        ],
        "events": [
            {"date": "1920", "from": "", "to": "黃同華", "mode": "納戶執照・伍分伍釐柒毫", "price": "", "relation": "", "evidence": "pitt:31735066237623"},
            {"date": "1922–1923（1924年12月補繳）", "from": "", "to": "黃同義", "mode": "納戶執照・伍分伍釐柒毫（同一筆稅）", "price": "", "relation": "同一稅額換名（推測同一戶）", "evidence": "pitt:31735066237581"},
            {"date": "1924年12月", "from": "", "to": "遠容・乞容・同華・同德・同義・國興", "mode": "一批連號收據，補繳民國11、12年欠糧", "price": "", "relation": "一人代辦（推測）", "evidence": "pitt:31735066237581 pitt:31735066237599"},
            {"date": "1926", "from": "", "to": "黃同華", "mode": "納戶執照・伍分伍釐柒毫（同一筆稅回到同華名下）", "price": "", "relation": "", "evidence": "pitt:31735066266747"},
            {"date": "1931", "from": "", "to": "黃乞容 等", "mode": "改用「糧戶執照」版頭", "price": "", "relation": "", "evidence": "pitt:31735066266721"},
        ],
    },
}


def households():
    timeline = read_csv(HH / "all_timeline.csv") if (HH / "all_timeline.csv").exists() else []
    out = []
    for key, h in HOUSEHOLDS.items():
        events = h.get("events") or [
            {k: e[k] for k in ("date", "from", "to", "mode", "price", "relation", "evidence")}
            for e in timeline if e["cluster"] == key
        ]
        out.append({"key": key, **{k: v for k, v in h.items() if k != "events"}, "events": events})
    # groups finished later appear automatically, flagged as not yet checked
    for f in sorted(HH.glob("*.json")):
        cluster = json.loads(f.read_text(encoding="utf-8")).get("cluster", "")
        if cluster and cluster not in HOUSEHOLDS and cluster not in [o["key"] for o in out]:
            out.append({"key": cluster, "title": cluster, "span": "", "status": "unchecked",
                        "lede": "識讀剛完成，尚未對照原件抽查。", "points": [],
                        "events": [{k: e[k] for k in ("date", "from", "to", "mode", "price", "relation", "evidence")}
                                   for e in timeline if e["cluster"] == cluster]})
    return out


# ---------- 4. Lin Xiuzhi parcels ----------
def parcels():
    rows = read_csv(HH / "B_linsen_lin_xiuzhi_parcels.csv")
    size = {(p["pid"], p["page"]): (int(p["width"]), int(p["height"])) for p in read_csv(DATA / "pitt_land_records_pages.csv")}
    return [{
        "licence": int(r["licence_no"]), "pid": r["pid"], "toponym": r["toponym"], "section": r["section"],
        "lot": r["lot_no"], "cls": r["land_class"], "mu": float(r["area_mu"]), "tax": float(r["tax_yuan"]),
        "img": img(r["pid"]), "size": size[(r["pid"], "1")],
        "crop": [0.345, 0.72, 0.67, 0.91],  # x1, y1, x2, y2 of the 圖略 box on this form
    } for r in rows]


# ---------- 5. reader ----------
def reader():
    meta = {r["pid"]: r for r in read_csv(DATA / "pitt_land_records.csv")}
    docs = []
    for f in sorted(HH.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if "docs" not in data:
            continue
        for d in data["docs"]:
            m = meta.get(d["pid"], {})
            n = int(m.get("pages_in_iiif") or d.get("page_count") or 1)
            page_tx = {int(p["page"]): p.get("transcription") or "" for p in d.get("pages") or [] if "page" in p}
            pages = [{"img": img(d["pid"], i), "tx": page_tx.get(i) or (d.get("transcription") if i == 1 else "") or ""}
                     for i in range(1, n + 1)]
            docs.append({
                "pid": d["pid"], "cluster": data.get("cluster", f.stem), "title": m.get("title", ""),
                "date": str(d.get("date_gregorian") or m.get("edtf_date") or ""),
                "date_original": str(d.get("date_original") or ""), "doc_type": d.get("doc_type") or "",
                "confidence": d.get("confidence"), "url": m.get("url", ""), "pages": pages,
            })
    return docs


def main():
    APP.mkdir(exist_ok=True)
    pages_index = {r["pid"] for r in read_csv(DATA / "pitt_land_records_pages.csv")}
    gen = []
    for era, year, kind, pid, page, label, note in GENEALOGY:
        assert pid in pages_index, pid
        gen.append({"era": era, "year": year, "kind": kind, "pid": pid, "img": img(pid, page), "label": label, "note": note})
    data = {"overview": overview(), "genealogy": gen, "households": households(),
            "parcels": parcels(), "reader": reader()}
    (APP / "data.js").write_text("window.APP_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"app/data.js written | households {len(data['households'])} | reader docs {len(data['reader'])} "
          f"| pages {sum(len(d['pages']) for d in data['reader'])}")


if __name__ == "__main__":
    main()
