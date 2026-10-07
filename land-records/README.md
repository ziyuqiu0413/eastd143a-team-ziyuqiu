# Land Records：匹兹堡大学中国土地文书的识读与归户

*Reading and household reconstruction of the University of Pittsburgh "Chinese Land Records" collection (EAL.2011.01, 1584–1978, mostly Fujian).*

数据源：<https://digital.library.pitt.edu/collection/chinese-land-records>

## 目前的进展

- **元数据**：全部 235 条记录（234 件文书和 1 份档案目录）已抓取并整理成表格。另外解析了档案目录里 240 条中文年号日期，发现 3 处年号换算错误。
- **图像对应表**：407 张图和记录一一对应，页数全部吻合。
- **家户归户**（研究目标：追踪产业如何一代代转移）：
  - 林森县林修枝（1947 年管业执照 9 张）已完成识读和分析；另与同县另外 9 件文书做了比较，发现同村邻户，并反推出赋额税率。
  - 建阳刘氏（7 件，1782–1935）已完成，结论是这 7 件不属于同一家族。
  - 永泰黄氏（57 页完粮收据）已完成：同一笔税在兄弟名下换来换去，收据上看不到代际转移。
  - 闽侯林万开已完成：1891 年三兄弟分家阄书；与林修枝组对读，可接出一条 1875–1947 的代际链（推测）。
  - 陈氏两组暂停。详见 [`data/households/SCOPE.md`](data/households/SCOPE.md)。
- **演示网页**：[`app/`](app/) 是只在本机运行的静态页面，包括馆藏概览、凭证谱系、家户归户、林修枝的九坵地和原件对读。启动方法见 [`app/README.md`](app/README.md)。

总体计划见 [`PLAN.md`](PLAN.md)，阶段汇报见 [`PROGRESS.md`](PROGRESS.md)。

## 目录

| 路径 | 内容 |
|---|---|
| `PLAN.md` | 项目计划，含参考的 GitHub 和 Hugging Face 项目 |
| `data/fetch_pitt_land_records.py` | 元数据抓取：Drupal `?_format=json` 和 IIIF manifest |
| `data/pitt_land_records.csv` | 235 条记录，已拆出卖方、买方、业主、地点和官印类别 |
| `data/pitt_land_records_linked.csv` | 同上，另加本地图像路径 |
| `data/pitt_land_records_pages.csv` | 每页图像一行（407 行） |
| `data/pitt_finding_aid_items.csv` | 档案目录 240 条，含中文年号日期和盒号、夹号 |
| `data/pitt_land_records_raw.json` | 抓取的原始 JSON |
| `data/households/READING_GUIDE.md` | 家户文书识读规范，含字段定义 |
| `data/households/B_*`、`B2_*` | 林修枝组：OCR 全文、要素表、分析、同县比较 |
| `data/households/F_*` | 建阳刘氏组 |
| `data/households/A_*` | 永泰黄氏组（上下两部分，以及合并裁定 `A_yongtai_huang_synthesis.md`） |
| `data/households/C_*` | 闽侯林万开组（含 1891 年分家阄书） |
| `app/` | 演示网页（数据由 `analysis/export_app_data.py` 生成） |
| `PROGRESS.md` | 阶段进展汇报 |
| `data/households/all_*.csv` | 各组合并后的文书表、人物表、产权事件表 |
| `pipeline/` | 图像对应（00）和 IIIF 下载（01） |
| `analysis/` | 林修枝组输出脚本、各组合并脚本 |

## 图像不在仓库里

馆方标注图像版权为 "Copyright Undetermined"，图像总量也有 200MB 以上，所以**仓库里不放任何图像**，包括裁切图。复现时请：

- 把课程提供的图像放到 `land-records/students_documents_export/images/<条码>_<三位页码>.jpg`，然后运行 `python pipeline/00_link_local_images.py`；
- 或者通过 Pitt 的 IIIF 服务查看原图（每条记录的 `url` 字段）。注意：该网站对脚本的大量请求会弹出人机验证，请勿绕过。

## 识读说明

- 转录保留繁体和异体字。〔〕表示手写或戳记填写的内容，□ 表示无法识读，[?] 表示没有把握。
- 家户分析严格区分"原文写明"和"推测"，每个结论都注明依据的 pid。
- 识读由 AI 完成，部分关键读数经过人工对照原件抽查。引用前请对照原件核对。
