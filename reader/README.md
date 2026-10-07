# 读契 · Reading the Deed

一个可以点击的地契阅读工具：在可缩放的契纸图片上框出各个部分（年号、卖主、买主、价银、四至、中人、官印……），点击后显示原文、白话解释和英文翻译，并用小动画说明一张契纸从立契到收执的流转过程。

## 本地运行

浏览器不允许直接打开本地 JSON，需要起一个本地服务器。在**仓库根目录**运行：

```bash
python3 -m http.server 8765
```

然后打开 <http://localhost:8765/reader/>。

## 文件结构

```
reader/
  index.html      页面
  style.css       样式（浅色/深色）
  app.js          逻辑（OpenSeadragon 查看器、标注框、流转动画）
  data/
    SCHEMA.md     标注数据格式说明
    index.json    契纸顺序 + 关联故事
    <id>.json     每张契纸的标注
images/           契纸图片（仓库根目录）
```

## 操作

- 点彩色方框，或用 **← →** 键逐个浏览；**Esc** 回到全图。
- 图例可以按类别隐藏或显示方框。
- 右上角切换 中文 / 双语 / EN。
- 网址会记住当前契纸和区域（如 `#31735064607470/r5`），可以直接分享某个区域。

## 校对

所有标注目前都是 **AI 初稿**（`review.status: "ai-draft"`）。校对时：

1. 优先看 `confidence` 为 `low` / `medium` 的区域，以及 `note` 里以「待核」开头的问题。
2. 改正 `original`（原文）、`modern_zh`（白话）、`english`（英文）；方框位置不准就改 `bbox`（`[x, y, 宽, 高]`，占整张图的比例）。
3. 一张契纸全部核对完后，把 `review.status` 改成 `"reviewed"`，页面上的黄色提示条会变成绿色的「已人工校对」。

## 图片来源

University of Pittsburgh Library System, *Chinese Land Records*。版权状态：Copyright Undetermined。
