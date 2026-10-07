# 读契工具数据格式 / Deed annotation schema

每张契纸一个 JSON 文件：`reader/data/<id>.json`，`<id>` 是图片编号（不含 `_001.jpg`）。
图片在仓库根目录的 `images/` 文件夹。

```jsonc
{
  "id": "31735064607470",
  "image": "31735064607470_001.jpg",
  "width": 2500, "height": 1132,              // 图片像素尺寸
  "source_url": "https://digital.library.pitt.edu/islandora/object/pitt%3A31735064607470",
  "title":   { "zh": "光緒十三年王錦發賣斷店屋契", "en": "Deed of absolute sale of a shop-house by Wang Jinfa, 1887" },
  "date":    { "original": "光緒拾叁年叁月拾捌日", "western": "1887", "zh": "光绪十三年三月十八日", "en": "18th day, 3rd month, 13th year of Guangxu (1887)" },
  "type":    { "zh": "賣斷契（白契）", "en": "Deed of absolute sale (unstamped private deed)" },
  "place":   { "zh": "閩邑（閩縣）橫山鋪", "en": "Hengshan ward, Min County (Fuzhou)" },
  "summary": { "zh": "两三句白话概述……", "en": "Two or three sentences…" },
  "flow": ["draft", "witness", "payment", "tax", "verify", "keep"],   // 这张契纸能体现的流转步骤（见下表）
  "regions": [
    {
      "id": "r1",
      "category": "seller",                     // 见下方类别表
      "label":   { "zh": "立契人（卖主）", "en": "Seller" },
      "bbox": [0.86, 0.02, 0.12, 0.40],         // [x, y, w, h]，占整张图宽高的比例 (0–1)，左上角为原点
      "original": "立賣斷契王錦發",              // 原文转录（繁体，保持原字）；读不出的字用 □，没把握的字后加 [?]
      "modern_zh": "立这份卖断契的人是王锦发。",   // 白话解释
      "english": "The person drawing up this deed of absolute sale is Wang Jinfa.",
      "confidence": "high",                     // high | medium | low —— 对转录和解释的把握
      "note": ""                                // 待核事项、术语解释等（可空）
    }
  ],
  "full_text": "全文转录（繁体，按原文列序，从右到左；每列之间用 / 分隔）",
  "review": { "status": "ai-draft", "notes": "" }   // 校对后改为 "reviewed"
}
```

## region 类别 `category`

| 值 | 中文 | 说明 |
|---|---|---|
| `title` | 契名 | 如「賣斷契」「契尾」「典按契單」 |
| `seller` | 立契人／卖主／出典人 | |
| `buyer` | 买主／承典人／业户 | |
| `property` | 标的 | 田、屋、店及其坐落 |
| `boundary` | 四至 | 东南西北界址 |
| `price` | 价银 | 契价、税银 |
| `reason` | 立契缘由 | 如「今因要用」「乏銀應用」 |
| `clause` | 担保条款 | 如「不明不干买主之事」「永遠為業」「不敢言贖」 |
| `date` | 立契日期 | 年号纪年 |
| `middleman` | 中人／见证人 | 中友、在見、公親、知契、證人 |
| `scribe` | 代笔 | |
| `seal` | 官印／钤印 | 识读印文；读不出就描述形制 |
| `tax` | 税契信息 | 契尾、税银、验契编号 |
| `official` | 官方文字 | 印刷的章程、告示 |
| `other` | 其他 | 如契首吉语「為永保千秋」、批注、编号 |

## 流转步骤 `flow`

| 值 | 中文 | English |
|---|---|---|
| `draft` | 立契：卖主请代笔写契 | Drafting |
| `witness` | 中人见证、画押 | Witnessing & signing |
| `payment` | 交银、交业 | Payment & handover |
| `tax` | 投税：到县衙纳契税，粘契尾、盖官印 | Tax registration |
| `verify` | 验契：民国政府要求旧契重新登记 | Republican re-verification |
| `keep` | 买主收执，世代保存 | Kept by the buyer |
