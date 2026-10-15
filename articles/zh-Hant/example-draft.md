---
title: "範本草稿文章 — 請刪除或修改"
description: "示範文章格式的草稿。只要移除 draft 標記，文章就會發佈到網站。"
date: 2026-10-15
draft: true
---

## 這是一份草稿

只要檔案開頭（兩條 `---` 之間）保留 `draft: true`，
`articles/en/` 與 `articles/zh-Hant/` 內的檔案都視為草稿，
不會出現在網站上。

## 如何發佈

1. 修改開頭資訊：填上正式的 `title`、`description` 與 `date`。
2. 把 `draft: true` 改為 `draft: false`（或刪除該行）。
3. 重新建置：`python3 scripts/build.py`。

只要另一個語言資料夾內存在**相同檔名**的檔案，文章就會以兩種語言
顯示在文章頁與 `sitemap.xml`。

## 可用的 Markdown

支援 `##` 標題、清單、**粗體**、*斜體*、`行內程式碼`、連結
[to xdo.dev](https://xdo.dev) 與程式碼區塊：

```bash
python3 scripts/build.py
```

> 也支援引言區塊。
