---
title: "Example draft article — delete or edit me"
description: "A draft showing the article format. It will not appear on the website until you remove the draft flag."
date: 2026-10-15
draft: true
---

## This is a draft

Files in `articles/en/` (and `articles/zh-Hant/`) are drafts while
`draft: true` stays in the front matter — the block between the two
`---` lines at the top of the file.

## How to publish

1. Edit the front matter: set a real `title`, `description` and `date`.
2. Change `draft: true` to `draft: false` (or delete the line).
3. Rebuild: `python3 scripts/build.py`.

The article appears on the Articles page and in `sitemap.xml` in both
languages, as long as a file with the **same filename** exists in the
other language folder.

## Markdown you can use

Headings with `##`, lists, **bold**, *italic*, `inline code`, links
[to xdo.dev](https://xdo.dev) and fenced code blocks:

```bash
python3 scripts/build.py
```

> Blockquotes are supported too.
