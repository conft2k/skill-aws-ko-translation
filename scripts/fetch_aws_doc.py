"""Fetch an AWS documentation page and convert its body to Markdown.

Usage:
    uv run --with beautifulsoup4 --with markdownify python fetch_aws_doc.py URL [-o OUT.md]

Keeps headings, lists, tables, links, fenced code blocks (with language) and
note boxes (as "> **Note**" blockquotes). Page chrome (navigation, feedback
widgets, copy buttons) is dropped. Pages outside docs.aws.amazon.com fall back
to <main>/<article>/<body>.
"""

import argparse
import re
import sys
import urllib.request
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

USER_AGENT = "skill-aws-ko-translation (+https://github.com/conft2k/skill-aws-ko-translation)"
LANG_ALIASES = {"cli": "bash", "cs": "csharp", "js": "javascript", "nohighlight": ""}


def code_language(pre):
    code = pre.find("code")
    for cls in (code.get("class", []) if code else []):
        name = cls.removeprefix("language-")
        if name in LANG_ALIASES:
            return LANG_ALIASES[name]
        if cls.startswith("language-") or cls.isalpha():
            return name
    return ""


def extract_body(soup):
    for selector in ("#main-col-body", "main", "article", "body"):
        node = soup.select_one(selector)
        if node:
            return node
    sys.exit("no content found")


def clean(body, base_url):
    for tag in body.select(
        "script, style, awsui-icon, .code-btn-container, #main-col-footer, "
        ".awsdocs-page-utilities, awsdocs-copyright, awsdocs-thumb-feedback"
    ):
        tag.decompose()
    # Note boxes: <div class="awsdocs-note"><div class="awsdocs-note-title"><h6>Note</h6>...
    for note in body.select("div.awsdocs-note"):
        title = note.select_one(".awsdocs-note-title")
        label = title.get_text(strip=True) if title else "Note"
        if title:
            title.decompose()
        quote = BeautifulSoup("<blockquote></blockquote>", "html.parser").blockquote
        strong = BeautifulSoup(f"<p><strong>{label}</strong></p>", "html.parser").p
        quote.append(strong)
        for child in list(note.children):
            quote.append(child.extract())
        note.replace_with(quote)
    for a in body.select("a[href]"):
        a["href"] = urljoin(base_url, a["href"])
    for img in body.select("img[src]"):
        img["src"] = urljoin(base_url, img["src"])


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url")
    parser.add_argument("-o", "--output", help="write Markdown here instead of stdout")
    args = parser.parse_args()

    req = urllib.request.Request(args.url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.select_one("h1")
    body = extract_body(soup)
    clean(body, args.url)

    md = MarkdownConverter(
        heading_style="ATX", bullets="-", code_language_callback=code_language
    ).convert_soup(body)
    if h1 and not body.select_one("h1"):
        md = f"# {h1.get_text(strip=True)}\n\n{md}"
    md = re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(md)
        print(f"wrote {args.output}", file=sys.stderr)
    else:
        sys.stdout.write(md)


if __name__ == "__main__":
    main()
