# 家户文书识读规范（归户用）

目标：读懂同一家户/同一宗族的一组契约文书，抽取结构化要素，重建"人—地块—交易"的时间链，追踪产业如何代际转移。

## 输入

- `data/households/clusters.json`：每组的文书清单（pid、nid、馆方标题、馆方日期、目录中的中文年号日期、盒/夹号、页数）。
- `data/images/index.json`：以 nid 为键，含每页的本地图像路径 `file` 和 IIIF 服务地址 `service`。
- 本地图像（优先用）：`students_documents_export/images/<条码>_<NNN>.jpg`，长边 2500px；条码 = pid 去掉 `pitt:`，NNN 为三位页码。全部 407 页与记录的对应表见 `data/pitt_land_records_pages.csv`。
- 备用：`data/images/<pid>/<pid>-NNNN.jpg`（宽 1600px，只覆盖部分文书）。

## 看图方法

1. 先用 Read 工具看整页，判断文书类型和版面。
2. 手写小字或长卷一定要放大：**只在本地裁切**（2026-10-07 起 Pitt 网站对脚本请求返回人机验证页，不得绕过，也不要再请求远程 IIIF）：
   ```
   python -c "from PIL import Image; im=Image.open('IN.jpg'); w,h=im.size; im.crop((int(w*X),int(h*Y),int(w*(X+W)),int(h*(Y+H)))).resize((int(w*W*2),int(h*H*2))).save('data/households/_crops/<pid>/<page>_<X>_<Y>.jpg')"
   ```
   X/Y/W/H 为 0–1 的比例，例：右半张 X=0.5,Y=0,W=0.5,H=1。竖排文字从右往左读。本地分辨率不够时标 □ 或 [?]，并注明"需原图核对"。
3. 红色印章、骑缝章、契尾、印花税票也要看，常写着官署名、年份、编号。

## 每件文书输出的字段（JSON）

```json
{
  "pid": "pitt:…", "nid": 0, "page_count": 1,
  "doc_type": "賣契|賣斷契|典契|找貼契|盡契|退契|鬮書/分關|管業執照|糧戶執照|串票/納稅收據|契尾|官契紙|推收/過戶單|驗契憑證|土地所有權狀|其他",
  "doc_type_evidence": "原文中表明类型的字样，如『立賣斷契』『糧戶執照』",
  "date_original": "原文日期", "date_gregorian": "公历（农历年末跨年要注明）",
  "date_vs_metadata": "与馆方日期一致/不一致（说明）",
  "parties": [
    {"name": "…", "role": "立契人/賣主/承買人/典主/業主/戶名/納戶/中人/代筆/在見/知見/保人/經手/官員",
     "relation_stated": "原文写明的亲属关系，如『胞弟』『堂兄』『侄』『母』；没写就填 null",
     "evidence": "原文片段"}
  ],
  "property": {
    "kind": "田/山/屋/店/地基/園/墳地…", "toponym": "土名", "location": "都/圖/鄉/村/保/坐落",
    "boundaries": {"東": null, "西": null, "南": null, "北": null},
    "size": "畝分厘/種子/坵/間 原文", "tax_or_rent": "糧額/租額 原文", "parcel_ids": "字號/段號/地號"
  },
  "title_origin": "产权来源原文，如『祖遺』『父遺鬮分』『自置』『承買某人』",
  "price": {"amount": null, "unit": null, "currency": null, "original_text": null},
  "clauses": ["先盡親房", "不敢找贖", "永遠管業", "推收過戶", "…"],
  "official_marks": "官印/契尾/印花/编号等，能读出的写原文",
  "transcription": "尽量全文转录，保留繁体和异体；不能识读的字用 □；没把握的字后面加 [?]；每列一行",
  "legibility": "high|medium|low",
  "confidence": 0.0,
  "notes": "其他发现，包括与馆方标题不符之处"
}
```

## 每组的综合分析（写进同一个 JSON 的 `synthesis`，并另写一份 Markdown）

1. **人物表**：姓名、出现在哪些文书（pid）、角色、原文写明的亲属关系、按字辈推测的辈分（推测必须标明"推测"）。
2. **地块表**：根据土名、四至、地号、面积，判断哪些文书指向同一块地。
3. **时间链**：按时间排列每一次产权变动——谁 → 谁、什么地块、什么方式（继承/分家/买卖/典当/登记/纳税）、价格、双方关系。
4. **代际转移的结论**：这一家户的产业如何一代代转移；哪些是家族内部流转，哪些流出家族。
5. **无法确定的问题**：读不清、证据不足的地方要明说。
6. **元数据问题**：馆方标题、日期、角色、地名与原件不符之处。

## 规则

- 不编造。原文写明的和推测的要严格分开；每个结论都注明依据的 pid。
- 保留原文繁体字，不要转成简体。
- 只写自己这一组的输出文件，不改动其他文件。
