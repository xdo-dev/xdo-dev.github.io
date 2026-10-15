# xdo website

Static website for **XDO Company** (xdo.dev) — one scrolling company page
plus separate technical-article pages, in **English** and **Traditional
Chinese**, with **light and dark modes**.

Built with plain HTML/CSS/JavaScript and a small Python build script.
No npm, no external fonts, no paid services.

## Quick start

Requirements: Python 3.8 or newer. Nothing else.

```bash
python3 scripts/build.py
python3 -m http.server 8000 --directory site
```

Then open:

```text
English:              http://localhost:8000/
Traditional Chinese:  http://localhost:8000/zh-Hant/
```

On Windows (PowerShell), use `python` instead of `python3` if that is how
Python is installed:

```powershell
python scripts\build.py
python -m http.server 8000 --directory site
```

Always preview through the local server (not by double-clicking the HTML
files) so that relative paths and the language switch work correctly.

## Project structure

```text
xdo-website/
├── content.json              # all company copy, English + Traditional Chinese
├── scripts/build.py           # builds the static site into site/
├── templates/                 # HTML templates used by the build script
├── articles/
│   ├── en/                    # English articles (Markdown)
│   └── zh-Hant/               # Traditional Chinese articles (Markdown)
├── assets/                    # logo, favicon, CSS, JS (copied into site/)
│   └── brand/                 # original logo files as uploaded
├── .github/workflows/deploy.yml
└── site/                      # generated output — do not edit by hand
```

`site/` is regenerated on every build and is listed in `.gitignore`
if you deploy with the included GitHub Actions workflow (it builds the
site on GitHub, so `site/` never needs to be committed).

## Editing the company content

All page text lives in **`content.json`**, split into an `"en"` and a
`"zh-Hant"` section. Edit the text, save, rebuild, refresh.

- Section labels, hero text, services, approach steps, about and contact
  blocks are all plain values in this file.
- Text in `[square brackets]` is a clearly marked placeholder to replace
  (office address, mobile certification name).
- The main CTA ("Contact Us") links to `anna@xdo.dev`.

## The logo

`assets/` contains your logo in several forms:

| File | Use |
|---|---|
| `logo-black.png` | Black wordmark, transparent background — shown in light mode |
| `logo-white.png` | White wordmark, transparent background — shown in dark mode |
| `favicon-32.png`, `favicon-180.png` | Browser tab and iOS home-screen icons |
| `brand/company-logo1.jpg`, `brand/company-logo2-2.jpg` | Your original uploads, kept untouched |

The two PNGs were produced from your two JPGs by removing the solid
background (antialiased edges preserved). The theme switch swaps between
them automatically — no JavaScript changes needed.

To replace the logo later: overwrite `logo-black.png` and `logo-white.png`
(keep the same filenames and roughly square-ish aspect ratio), then
rebuild. Regenerate the favicons too if the mark changes.

## Showing or hiding the articles section

The articles section (nav link, "Read our articles" button, article
pages, and their sitemap entries) is controlled by one switch at the
top of `content.json`:

```json
"site": {
  "articles_enabled": false,
  ...
}
```

- `false` — the website has no article section at all. Article pages are
  not generated, the nav link and hero button are removed, and the
  sitemap excludes them. Your Markdown files in `articles/` stay in the
  project untouched.
- `true` — everything comes back on the next build.

Set the flag, rebuild, done. It is currently set to `false` (hidden).

## Writing articles

Articles are Markdown files with a small front-matter header:

```markdown
---
title: "Your article title"
description: "One-sentence summary shown on the article index."
date: 2026-10-15
draft: true
---

## First heading

Body text...
```

- `draft: true` keeps the article off the website. Set `draft: false`
  (or delete the line) and rebuild to publish.
- Supported Markdown: `##`/`###` headings, paragraphs, bullet and
  numbered lists, **bold**, *italic*, `code`, fenced code blocks,
  links, and `> quotes`.
- Save English articles in `articles/en/`, Traditional Chinese in
  `articles/zh-Hant/`. Give translated versions of the same article the
  **same filename** so the language switch links them.
- The build script prints how many articles were published and how many
  drafts were excluded.

## Deploying to GitHub Pages

1. Create a public repository named **`xdo-dev.github.io`** under the
   `xdo-dev` organization (Settings → New repository). This special name
   serves the site at `https://xdo-dev.github.io/`.
2. Push this project's files to the `main` branch:

   ```bash
   git init -b main
   git add .
   git commit -m "xdo website"
   git remote add origin https://github.com/xdo-dev/xdo-dev.github.io.git
   git push -u origin main
   ```

3. In the repository: Settings → Pages → Build and deployment →
   Source: **GitHub Actions**. The included workflow
   (`.github/workflows/deploy.yml`) builds the site and deploys it on
   every push to `main`.

Because the workflow builds the site on GitHub, `site/` is never
committed — keep it in `.gitignore`.

### Custom domain xdo.dev

After the site is live at `xdo-dev.github.io`:

1. Repository Settings → Pages → Custom domain: enter **`xdo.dev`** and
   save. One domain is entered here — the other variant is handled by
   DNS and GitHub's automatic redirects, not by entering it again
   ([managing a custom domain](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site)).
2. At your DNS provider add:
   - apex `A` records → `185.199.108.153`, `185.199.109.153`,
     `185.199.110.153`, `185.199.111.153` (IPv6 `AAAA` equivalents
     `2606:50c0:8000::153` … `2606:50c0:8003::153` are also published)
   - `www` CNAME → **`xdo-dev.github.io`** — the docs require pointing
     it at the Pages default hostname, not at the apex domain
3. With correct records for both, GitHub Pages automatically redirects
   `www.xdo.dev` → `xdo.dev`
   ([about custom domains](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/about-custom-domains-and-github-pages)).
   (GitHub generally recommends a `www` subdomain as the primary custom
   domain; if you prefer `www.xdo.dev` as primary, enter that in step 1
   and the apex redirects to it instead.)
4. Enable **Enforce HTTPS** once the certificate is issued.

Update `content.json` → `site.domain` if the domain ever changes
(it drives canonical URLs, the sitemap, and `robots.txt`).

### GitHub Pages commercial-use caveat

GitHub's Pages usage limits state that Pages "is not intended for or
allowed to be used as a free web-hosting service to run your online
business, e-commerce site, or any other website that is primarily
directed at either facilitating commercial transactions or providing
commercial software as a service (SaaS)"
([GitHub Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)).
Because this website promotes paid cybersecurity services, review that
policy before relying on GitHub Pages for the final business site. The
generated `site/` folder is a plain static site and can be deployed to
any other host (Cloudflare Pages, Netlify, S3 + CloudFront, etc.)
without changes.

## Analytics

Analytics is intentionally left unconfigured — no tracking provider
was added silently. When you choose one, paste its snippet into the
three template files (`templates/home.html`,
`templates/article-list.html`, `templates/article.html`) just before
`</body>`, and rebuild. Check the provider's policy for cookie banners
in your jurisdictions.

## Launch checklist

- [ ] Replace `[Office address — to be provided]` in `content.json`
      (two places per language) when available
- [ ] Confirm the exact name of the mobile certification and replace
      the `[Mobile certification — ...]` placeholder
- [ ] Review the "About assessment documentation" wording and the
      engagement-process copy with your team
- [ ] Delete or replace `articles/*/example-draft.md`
- [ ] Confirm both languages and both themes in a mobile-width browser
- [ ] Verify the emails, GitHub link, and custom domain DNS
- [ ] Extract into a **new folder** — this is a rebuilt replacement
      package; do not overwrite any edits you made in your old copy

## Troubleshooting

**Build fails with `PermissionError` / "Access is denied" on Windows.**
This build script does not delete the `site` folder wholesale — it
removes only files it knows it generated (via `site/.build-manifest.json`),
so the earlier rmtree problem should not recur. If you still see an
access error: stop the preview server (Ctrl+C), close any terminal or
Explorer window showing `site/`, and run the build again.

**Language switch shows a page in the wrong language.** Translated
articles must share the same filename in `articles/en/` and
`articles/zh-Hant/`. Missing translation falls back to the other
language's article index.

**Changes not visible.** Hard-refresh (Ctrl+F5) — the browser may cache
`style.css` or `main.js`.
