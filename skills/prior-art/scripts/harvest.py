#!/usr/bin/env python3
"""Harvest a reference UI page into .ref/<name>/ for design study.

Saves:
  page.html      - the page, stylesheet/img URLs rewritten to local copies
  css/           - all linked and @import'ed stylesheets
  assets/        - fonts and images referenced by the page or its CSS
  tokens-raw.md  - auto-extracted custom properties, font stacks, colors
  MANIFEST.md    - what was saved, what failed, source URLs

Stdlib only. Individual asset failures are expected (CDN auth, 403) and
recorded in the manifest rather than aborting the harvest.

Usage:
  python3 harvest.py https://linear.app --out .ref
  python3 harvest.py https://stripe.com/pricing --name stripe-pricing --out .ref
"""

import argparse
import gzip
import hashlib
import re
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
ASSET_EXTS = (".woff2", ".woff", ".ttf", ".otf", ".png", ".jpg", ".jpeg",
              ".webp", ".avif", ".gif", ".svg", ".ico")
MAX_ASSET_BYTES = 5 * 1024 * 1024
TIMEOUT = 25


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip",
    })
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b"\x1f\x8b":
            try:
                data = gzip.decompress(data)
            except OSError:
                pass
        return data


class PageScanner(HTMLParser):
    """Collect stylesheet hrefs, inline <style> text, and <img> srcs."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stylesheets = []
        self.images = []
        self.inline_css = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "link":
            rel = (a.get("rel") or "").lower()
            as_attr = (a.get("as") or "").lower()
            href = a.get("href")
            if href and ("stylesheet" in rel or (rel == "preload" and as_attr == "style")):
                self.stylesheets.append(href)
        elif tag == "img":
            src = a.get("src")
            if src and not src.startswith("data:"):
                self.images.append(src)
        elif tag == "style":
            self._in_style = True

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.inline_css.append(data)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "page"


def default_name(url: str) -> str:
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc.split(":")[0]
    host = re.sub(r"^www\.", "", host)
    name = slugify(host)
    path = parts.path.strip("/")
    if path:
        name += "-" + slugify(path)[:40]
    return name


def local_asset_name(url: str) -> str:
    base = Path(urllib.parse.urlsplit(url).path).name or "asset"
    base = re.sub(r"[^A-Za-z0-9._-]", "_", base)[:80]
    digest = hashlib.sha1(url.encode()).hexdigest()[:8]
    return f"{digest}-{base}"


def find_css_urls(css_text: str):
    """Yield (raw_match, url) for url(...) references inside CSS."""
    for m in re.finditer(r"url\(\s*(['\"]?)([^'\"\)]+)\1\s*\)", css_text):
        yield m.group(0), m.group(2).strip()


def find_imports(css_text: str):
    for m in re.finditer(
            r"@import\s+(?:url\(\s*)?['\"]?([^'\"\)\s;]+)['\"]?\s*\)?[^;]*;",
            css_text):
        yield m.group(1)


def extract_tokens(css_corpus: str) -> str:
    props = {}
    for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;}{]+)", css_corpus):
        props.setdefault(m.group(1), m.group(2).strip()[:120])
    fonts = Counter(
        m.group(1).strip()[:100] for m in
        re.finditer(r"font-family\s*:\s*([^;}{]+)", css_corpus, re.I))
    colors = Counter(re.findall(
        r"#[0-9a-fA-F]{3,8}\b|(?:rgba?|hsla?|oklch|oklab)\([^)]*\)", css_corpus))

    lines = ["# Auto-extracted tokens (raw)",
             "",
             "Frequency dump from harvested CSS. Curate into tokens.md.",
             "",
             f"## Custom properties ({len(props)})", ""]
    for k in sorted(props)[:400]:
        lines.append(f"- `{k}: {props[k]}`")
    if len(props) > 400:
        lines.append(f"- ... {len(props) - 400} more (grep the css/ files)")
    lines += ["", "## Font stacks (by frequency)", ""]
    for stack, n in fonts.most_common(15):
        lines.append(f"- {n}x `{stack}`")
    lines += ["", "## Color literals (top 40 by frequency)", ""]
    for color, n in colors.most_common(40):
        lines.append(f"- {n}x `{color}`")
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url")
    ap.add_argument("--name", help="folder name under --out (default: from URL)")
    ap.add_argument("--out", default=".ref", help="archive root (default: .ref)")
    ap.add_argument("--max-assets", type=int, default=40)
    args = ap.parse_args()

    url = args.url if "://" in args.url else "https://" + args.url
    name = args.name or default_name(url)
    dest = Path(args.out) / name
    (dest / "css").mkdir(parents=True, exist_ok=True)
    (dest / "assets").mkdir(exist_ok=True)

    failures = []
    saved = []

    print(f"harvest: {url} -> {dest}")
    try:
        html_text = fetch(url).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"FATAL: could not fetch page: {e}", file=sys.stderr)
        print("Hint: sandboxed/blocked network? Use the WebFetch fallback in "
              "references/ui-harvest.md.", file=sys.stderr)
        sys.exit(1)

    scanner = PageScanner()
    scanner.feed(html_text)

    # --- stylesheets (linked + one level of @import) ---
    css_texts = {}           # local relative path -> text
    css_url_to_local = {}
    queue = [(u, urllib.parse.urljoin(url, u)) for u in scanner.stylesheets]
    seen = set()
    idx = 0
    while queue:
        raw_ref, abs_url = queue.pop(0)
        if abs_url in seen:
            continue
        seen.add(abs_url)
        try:
            text = fetch(abs_url).decode("utf-8", errors="replace")
        except Exception as e:
            failures.append(f"css {abs_url}: {e}")
            continue
        idx += 1
        local = f"css/{idx:02d}-{local_asset_name(abs_url)}"
        if not local.endswith(".css"):
            local += ".css"
        css_texts[local] = text
        css_url_to_local[raw_ref] = local
        css_url_to_local[abs_url] = local
        for imp in find_imports(text):
            queue.append((imp, urllib.parse.urljoin(abs_url, imp)))

    # --- assets referenced by CSS and by <img> tags ---
    asset_map = {}  # absolute url -> local name under assets/
    budget = args.max_assets

    def grab_asset(abs_url: str):
        nonlocal budget
        if abs_url in asset_map or budget <= 0:
            return asset_map.get(abs_url)
        path_ext = Path(urllib.parse.urlsplit(abs_url).path).suffix.lower()
        if path_ext not in ASSET_EXTS:
            return None
        try:
            blob = fetch(abs_url)
        except Exception as e:
            failures.append(f"asset {abs_url}: {e}")
            return None
        if len(blob) > MAX_ASSET_BYTES:
            failures.append(f"asset {abs_url}: skipped ({len(blob)//1024} KB > cap)")
            return None
        local = local_asset_name(abs_url)
        (dest / "assets" / local).write_bytes(blob)
        asset_map[abs_url] = local
        budget -= 1
        saved.append(f"assets/{local}")
        return local

    for local_css, text in list(css_texts.items()):
        base_url = next((u for u, l in css_url_to_local.items()
                         if l == local_css and "://" in u), url)
        for raw, ref in find_css_urls(text):
            if ref.startswith("data:"):
                continue
            local = grab_asset(urllib.parse.urljoin(base_url, ref))
            if local:
                text = text.replace(raw, f"url(../assets/{local})")
        css_texts[local_css] = text
        (dest / local_css).write_text(text, encoding="utf-8")
        saved.append(local_css)

    for src in scanner.images[: max(budget, 0)]:
        local = grab_asset(urllib.parse.urljoin(url, src))
        if local:
            html_text = html_text.replace(src, f"assets/{local}")

    # --- rewrite stylesheet references in the page copy ---
    for ref, local in css_url_to_local.items():
        if ref in html_text:
            html_text = html_text.replace(ref, local)
    (dest / "page.html").write_text(html_text, encoding="utf-8")
    saved.insert(0, "page.html")

    # --- tokens ---
    corpus = "\n".join(css_texts.values()) + "\n" + "\n".join(scanner.inline_css)
    (dest / "tokens-raw.md").write_text(extract_tokens(corpus), encoding="utf-8")
    saved.append("tokens-raw.md")

    # --- manifest ---
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# Harvest manifest — {name}", "",
             f"- Source: {url}", f"- Harvested: {stamp}",
             f"- Stylesheets: {len(css_texts)} (inline <style> blocks: "
             f"{len(scanner.inline_css)}, included in token extraction)",
             f"- Assets saved: {len(asset_map)} (cap {args.max_assets})",
             "", "## Files", ""]
    lines += [f"- {p}" for p in saved[:200]]
    if failures:
        lines += ["", f"## Failures ({len(failures)}) — usually fine, retry only "
                      "what matters", ""]
        lines += [f"- {f}" for f in failures[:100]]
    lines += ["", "## Notes",
              "- JS-rendered content is not captured; page.html may look "
              "skeletal locally. CSS + tokens are the durable value. "
              "Use a browser tool for screenshots (see ui-harvest.md).", ""]
    (dest / "MANIFEST.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"done: {len(css_texts)} css, {len(asset_map)} assets, "
          f"{len(failures)} failures -> {dest}/MANIFEST.md")


if __name__ == "__main__":
    main()
