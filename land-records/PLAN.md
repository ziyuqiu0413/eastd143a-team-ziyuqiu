# 从红契到土改证：匹兹堡大学中国土地文书的 AI 识读与产权流转分析

> 黑客松项目计划（草案 v0.1，2026-10-07）
> 数据源：[Pitt ULS · Chinese Land Records](https://digital.library.pitt.edu/collection/chinese-land-records)（EAL.2011.01，234 件文书，1584–1978，福建为主）

---

## 1. 一句话目标

把 234 件只有一行标题的地契图像，变成**可检索、可核对、可分析的结构化契约数据库**，并用它回答：
**产权凭证如何随政权更替（清 → 民国 → 新中国）而变化？一个家户的产业如何在亲族之间流转？**

## 2. 现状（已完成的前期工作）

| 已有 | 文件 | 说明 |
|---|---|---|
| 元数据全量抓取 | `data/pitt_land_records.csv` / `_raw.json` | 235 行；已拆出卖方/买方/业主/地点/官印类别 |
| 档案目录条目 | `data/pitt_finding_aid_items.csv` | 240 条，含中文年号原文日期、盒/夹号 |
| 抓取脚本 | `data/fetch_pitt_land_records.py` | Drupal `?_format=json` + IIIF manifest |
| 样图 | `data/samples/*.jpg` | 清红契、清白契、民国管业执照、1953 土改证 |

已知数据特征：约 407 张图像（平均 1.7 页/件）；Government（有官印）172 / Personal 60；福州周边占 38%；同姓交易占 32%；至少 7 组"同一家户"文书群；年号换算错误 3 处。

**关键缺口：没有任何全文转录和契约要素字段（价格、面积、四至、中人等）。** 这就是本项目要补的。

## 3. 研究问题

1. **凭证谱系**：从清代红契/白契 → 民国土地管业执照 → 1950 年代土地房产所有证，文书格式、官印比例、国家登记介入程度如何变化？
2. **家户与亲族**：在 7 组家户档案中，产业如何流转？亲族内部交易（"先尽亲房"）的比例与时代变化？
3. **方法问题**：当前开源视觉语言模型（VLM）识读手写竖排契约的准确率有多高？哪些字段最难？

## 4. 技术路线

改编自 `historical-corpus-pipeline` 技能（原流程面向已 OCR 的印刷文本，这里改为**图像优先**）：

```
IIIF 图像 ──→ ① 识读(OCR/VLM) ──→ ② 契约要素抽取(JSON) ──→ ③ 归一化与链接 ──→ ④ 数据库 + 检索
   │              │ 人工金标准集评测          │ 年号/地名/人名/币制           │
   │              └──→ 校对工作台             └──→ 家户归户（产权链）          └──→ ⑤ 可视化 + 问答 + 数据质量报告
   └──→ 红色官印检测（OpenCV，零成本校验 Government/Personal 标签）
```

### ① 识读：先评测，再全量

**先建金标准集**：分层抽 24 件（清手写 8、民国 8、1949 后 8，含 4 张样图），人工逐字转录 → 用字符错误率（CER）评测候选模型。

| 候选 | 来源 | 许可 | 适用理由 |
|---|---|---|---|
| Qwen3-VL-8B / 4B-Instruct | [HF](https://huggingface.co/Qwen/Qwen3-VL-8B-Instruct) · [GitHub](https://github.com/QwenLM/Qwen3-VL) | Apache-2.0 | 中文 VLM 主力，可直接输出 JSON；8B 需约 20GB 显存，4B 可降配 |
| PaddleOCR-VL（0.9B） | [HF](https://huggingface.co/PaddlePaddle/PaddleOCR-VL) · [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR) | Apache-2.0 | 轻量版面+识别，适合印刷表格类（执照、土改证） |
| dots.ocr | [HF](https://huggingface.co/dots-studio/dots.ocr) · [GitHub](https://github.com/studio-dots-ai/dots.ocr) | — | 单模型版面解析，表格结构强 |
| DeepSeek-OCR | [HF](https://huggingface.co/deepseek-ai/DeepSeek-OCR) | MIT | 对照组 |
| TongGu-VL-2B | [HF](https://huggingface.co/SCUT-DLVCLab/TongGu-VL-2B-Instruct) | Apache-2.0 | 古文专用小模型，测繁体/异体字 |
| 商用 API（Claude / GPT / Gemini 视觉） | — | 付费 | 无 GPU 时的基线；407 张图量很小，成本可控 |

参考基准与先例：
- [EvaHan 2026](https://aclanthology.org/2026.lt4hala-1.31/)：首届古籍 OCR+版面评测，手写测试集最佳字符准确率 95.71%（计异体字）→ 我们的预期上限参照。
- [bytedance/AncientDoc](https://github.com/bytedance/AncientDoc)：VLM 古籍文档基准（OCR→翻译→问答），可借用评测设计。
- [mengyuchun/evahan2026-ocr](https://github.com/mengyuchun/evahan2026-ocr)：Qwen2.5-VL + LoRA 古籍 OCR → 若时间充裕可做微调。
- 训练数据候选：[ENC-PSL/evahan-ultraglyph](https://huggingface.co/datasets/ENC-PSL/evahan-ultraglyph)（CC-BY-4.0，历史文献 OCR）。

**策略**：印刷表格类（民国执照、土改证，约 60 件）准确率高，先做；手写契约走"模型初稿 + 人工校对"。

### ② 契约要素抽取

逐件调用 LLM（**单件处理优于批量**，避免 JSON 格式漂移），按固定 schema 输出：

```json
{
  "doc_type": "卖断契|典契|找贴契|分关书|管业执照|土地房产所有证|税契/契尾|其他",
  "date_original": "乾隆貳拾陸年辛巳歲拾月", "date_gregorian": "1761",
  "grantor": ["許瓊栢"], "grantee": ["吳省忠"],
  "witnesses": [{"name": "官盛清", "role": "說合/中人"}], "scribe": "…",
  "object": {"kind": "山埔/田/屋/店", "toponym": "土名…", "boundaries": {"東":"…","西":"…","南":"…","北":"…"},
             "area": "…", "rent_or_tax": "…"},
  "price": {"amount": 30, "unit": "兩", "currency": "銀"},
  "clauses": ["先盡親房", "不敢找贖", "…"],
  "seal": true, "confidence": 0.0
}
```

- 金额常用大写数字/苏州码子 → [weakish/suzhou-numerals](https://github.com/weakish/suzhou-numerals) 解码。
- 交叉校验：抽取出的人名必须与馆方标题中的卖方/买方/业主一致，不一致则标红待查。
- 古文 NER 作对照（可选）：[ethanyt/guwen-ner](https://huggingface.co/ethanyt/guwen-ner)、[SIKU-BERT/sikuroberta](https://huggingface.co/SIKU-BERT/sikuroberta)。
- 契约格式参照：[台湾历史数字图书馆 THDL](https://dh-abstracts.library.virginia.edu/works/982)（21,399 件全文地契）、[Harvard Ming-Qing Documents · Deeds from Fujian](https://scalar.fas.harvard.edu/ming-qing-documents/ii17-deeds-from-fujian)（Harvard 课程资源，可做阅读指南和标注规范）。

### ③ 归一化与链接

| 对象 | 方法 | 工具 |
|---|---|---|
| 年号日期 | 年号 → 公历，农历年末跨年单独标注；与馆方日期比对 | [6tail/lunar-python](https://github.com/6tail/lunar-python)、[sxtwl](https://github.com/yuangu/sxtwl_cpp) |
| 历史地名 | 闽县/侯官/闽侯/林森县 → 同一地理实体，带时间区间 | [CHGIS](https://github.com/cga-harvard/chgis)（Harvard）、[CHGIS MCP Server](https://github.com/huajibing/CHGIS_MCP_Server) |
| 人名 | 繁简/拼音统一（如 CHEN/CHENG 混用），同名消歧 | 规则 + 人工 |
| 家户归户 | 卖方→买方→后续业主，串成产权链 | networkx |
| 人物库 | 契约当事人多为平民，CBDB 命中率预计很低，仅抽查 | [cbdb_sqlite](https://github.com/cbdb-project/cbdb_sqlite) |

### ④ 数据库与检索

- SQLite：`documents`、`pages`（IIIF 链接）、`transcriptions`、`parties`、`parcels`、`transactions`。日期字段沿用技能里的 `date_not_before / date_not_after / date_certainty` 设计。
- 全文检索：FTS5 + jieba（加入"賣斷、找貼、土名、四至"等契约词典）。
- 向量检索：[BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)（文本）；可选 [Qwen3-VL-Embedding-2B](https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B)，实现"以图搜契"。

### ⑤ 展示与产出

1. **对照阅读器**：[Mirador](https://github.com/ProjectMirador/mirador) 直接读取 Pitt 的 IIIF manifest（不需要转存图像），旁边显示转录和要素字段；用 [Annotorious](https://github.com/annotorious/annotorious) 圈出印章、中人签押。
2. **凭证谱系时间轴**：红契/白契/执照/土改证随年份的构成变化。
3. **家户产权网络**：7 组家户的交易链。用原生 SVG 绘制（技能经验：不要依赖 D3 的事件回调），或导出给 [Gephi](https://github.com/gephi/gephi)。
4. **地图**：福建各县分布，带历史政区。
5. **问答（可选）**：RAG 检索增强问答，每条回答必须引用具体契约编号。
6. **数据质量报告**：反馈给 Pitt 图书馆，包括 3 处年号换算错误、地名错字、角色误标、拼音不一致。

校对工作台可选 [Label Studio](https://github.com/HumanSignal/label-studio)，或参考 [donkey-scribe 古籍OCR校录工作台](https://github.com/eglantine-shell/donkey-scribe)。

## 5. 日程（假设 3 天、3–4 人；时间更长时把"扩展"项提前）

| 时间 | 数据/工程 | 识读/LLM | 历史/校对 | 前端 |
|---|---|---|---|---|
| **第 1 天** | 下载 407 张 IIIF 图；建 SQLite；红色官印检测 | 跑 3–4 个候选模型 | 转录 24 件金标准集；制定标注规范 | 搭 Mirador 对照阅读器原型 |
| **第 2 天** | 年号/地名归一化；归户 | 选定模型全量识读；要素抽取 | 校对印刷类 + 高价值家户档案 | 时间轴、网络图 |
| **第 3 天** | 评测报告（CER、字段 F1） | 问答（可选） | 写研究发现；数据质量报告 | 整合演示、部署 GitHub Pages |
| **扩展** | 数据集发布到 HF | LoRA 微调（参考 evahan2026-ocr） | 全量人工校对 | 地图、以图搜契 |

**最小可行版本（MVP）= 金标准评测 + 全量初稿转录 + 要素表 + 对照阅读器 + 凭证谱系图。** 问答、地图、微调都是加分项。

## 6. 评测指标

- 识读：金标准集上的 CER，按手写/印刷、清/民国/1949 后分别统计。
- 抽取：字段级 F1（当事人、日期、价格、面积、四至、契约类型）。
- 归一化：年号换算与馆方日期一致率；地名与 CHGIS 的匹配率。
- 一致性：官印检测结果与 Government/Personal 标签的吻合率。

## 7. 风险与对策

| 风险 | 对策 |
|---|---|
| 手写草书识别率低 | 先做印刷类，保证 MVP；手写类走人工校对，并如实报告 CER |
| 没有 GPU | 用 4B/2B 小模型或商用 API；407 张图量很小 |
| 版权"未定" | **不转存图像**；只发布元数据和我们自己的转录，图像通过 Pitt IIIF 链接引用 |
| 样本小（234 件），统计说服力有限 | 定位为个案和方法示范，不做全国性推论；可与 THDL 等大库对照 |
| LLM 编造字段 | 强制输出 `confidence` 和原文片段；与馆方标题交叉校验；人工抽检 |

## 8. 仓库结构（建议）

```
hackthon/
├─ PLAN.md
├─ data/                 # 已有：元数据、目录、样图、抓取脚本
├─ pipeline/
│  ├─ 01_download_iiif.py
│  ├─ 02_seal_detect.py
│  ├─ 03_transcribe.py   # 多模型可切换
│  ├─ 04_extract.py      # 要素 JSON
│  ├─ 05_normalize.py    # 年号/地名/人名/归户
│  └─ 06_build_db.py
├─ eval/
│  ├─ gold/              # 24 件人工转录
│  └─ score.py           # CER + 字段 F1
├─ app/                  # 静态站：Mirador + 时间轴 + 网络图
└─ docs/data_quality_report.md
```

发布：GitHub 仓库 `et28335/<项目名>`（先设私有）；HF 数据集只发元数据和转录。

## 9. 待定决策

- [ ] 黑客松时长、人数、提交形式（演示站 / 论文 / 幻灯片）
- [ ] 算力：本地 GPU 型号，或使用哪家 API、预算多少
- [ ] 研究问题侧重：凭证谱系（制度史） vs 家户产权链（社会经济史） vs 模型评测（方法）
- [ ] 项目名与仓库公开时间
