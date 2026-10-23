"""Compare a Korean translation against its English Markdown source.

Usage:
    python check_translation.py SOURCE.md TRANSLATION.md

Checks what the translation rules require to stay unchanged, plus a few style
signals. ERROR lines break the rules and must be fixed; WARN lines need a look;
REVIEW lines list every <!-- 검수 필요: ... --> marker. Exit status is 1 when
there is at least one ERROR. Standard library only.
"""

import re
import sys
from collections import Counter

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
INLINE_CODE = re.compile(r"(`+)(.+?)\1")
LINK_URL = re.compile(r"\]\(\s*<?([^)\s>]+)>?(?:\s+[\"'][^)]*[\"'])?\s*\)")
REF_URL = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.M)
SHORTCODE = re.compile(r"\{\{[<%].*?[%>]\}\}")
HEADING = re.compile(r"^(#{1,6})\s")
TABLE_SEP = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
COMMENT = re.compile(r"(?:^|\s)(#|//)(?=\s|$)")
DIRECTIVE = re.compile(
    r"^\s*(#!|#cloud-config|# ?syntax=|# ?-\*-|#\s*(noqa|type:|pylint:|fmt:)|"
    r"//\s*(@ts-|eslint-|prettier-|go:|nolint))"
)
REVIEW = re.compile(r"<!--\s*검수 필요:(.*?)-->")
FRONT_MATTER_TEXT_KEYS = {"title", "description", "summary", "linkTitle", "alt"}

problems = []


def report(level, line, msg):
    problems.append((level, line, msg))


def split_front_matter(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return lines[1:i], i + 1
    return [], 0


def parse(text):
    """Split a document into fenced code blocks and prose lines (with line numbers)."""
    lines = text.splitlines()
    front, start = split_front_matter(lines)
    blocks, prose = [], []
    i = start
    while i < len(lines):
        m = FENCE.match(lines[i])
        if m:
            marker, info = m.group(1), m.group(2).strip()
            body, j = [], i + 1
            while j < len(lines):
                close = FENCE.match(lines[j])
                if close and close.group(1)[0] == marker[0] and len(close.group(1)) >= len(marker) and not close.group(2).strip():
                    break
                body.append(lines[j])
                j += 1
            blocks.append({"line": i + 1, "info": info, "body": body})
            i = j + 1
            continue
        prose.append((i + 1, lines[i]))
        i += 1
    return front, blocks, prose


def front_matter_map(front):
    out = {}
    for line in front:
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def check_front_matter(src, dst):
    s, d = front_matter_map(src), front_matter_map(dst)
    for key in s.keys() - d.keys():
        report("ERROR", 1, f"front matter key missing: {key}")
    for key in d.keys() - s.keys():
        report("ERROR", 1, f"front matter key added: {key}")
    for key in s.keys() & d.keys():
        if key not in FRONT_MATTER_TEXT_KEYS and s[key] != d[key]:
            report("ERROR", 1, f"front matter value changed for '{key}': {s[key]!r} -> {d[key]!r}")


def code_part(line):
    m = COMMENT.search(line)
    return (line[: m.start()].rstrip(), True) if m else (line.rstrip(), False)


def check_code_blocks(src, dst):
    if len(src) != len(dst):
        report("ERROR", 0, f"code block count differs: source {len(src)}, translation {len(dst)}")
    for s, d in zip(src, dst):
        if s["info"] != d["info"]:
            report("ERROR", d["line"], f"code block language changed: {s['info']!r} -> {d['info']!r}")
        if len(s["body"]) != len(d["body"]):
            report("ERROR", d["line"], f"code block line count differs ({len(s['body'])} -> {len(d['body'])})")
            continue
        for k, (a, b) in enumerate(zip(s["body"], d["body"])):
            if a == b:
                continue
            where = d["line"] + 1 + k
            if DIRECTIVE.match(a):
                report("ERROR", where, f"directive comment changed: {a.strip()!r}")
                continue
            (ca, has_comment), (cb, _) = code_part(a), code_part(b)
            if not has_comment or ca != cb:
                report("ERROR", where, f"code changed: {a.strip()!r} -> {b.strip()!r}")


def prose_text(prose):
    return "\n".join(line for _, line in prose)


def compare_multiset(name, src_items, dst_items, missing_level="ERROR"):
    s, d = Counter(src_items), Counter(dst_items)
    for item, n in (s - d).items():
        report(missing_level, 0, f"{name} missing or changed ({n}x): {item}")
    for item, n in (d - s).items():
        report("WARN", 0, f"{name} not in source ({n}x): {item}")


def find_line(prose, needle):
    for no, line in prose:
        if needle in line:
            return no
    return 0


def check_structure(sp, dp):
    s_levels = [len(m.group(1)) for _, l in sp if (m := HEADING.match(l))]
    d_levels = [len(m.group(1)) for _, l in dp if (m := HEADING.match(l))]
    if s_levels != d_levels:
        report("ERROR", 0, f"heading levels differ: source {s_levels}, translation {d_levels}")
    s_tables = [l.strip().strip("|").count("|") + 1 for _, l in sp if TABLE_SEP.match(l)]
    d_tables = [l.strip().strip("|").count("|") + 1 for _, l in dp if TABLE_SEP.match(l)]
    if s_tables != d_tables:
        report("ERROR", 0, f"tables differ (columns per table): source {s_tables}, translation {d_tables}")


def check_style(dp):
    in_html_comment = False
    for no, line in dp:
        text = REVIEW.sub("", INLINE_CODE.sub("", line))
        if "<!--" in text and "-->" not in text:
            in_html_comment = True
        if in_html_comment:
            in_html_comment = "-->" not in text
            continue
        if "십시오" in text:
            report("WARN", no, "procedure ending '~하십시오': use '~합니다'")
        if re.search(r"(?<![니요])다\.(?![가-힣])", text):
            report("WARN", no, "possible 해라체 ending ('~다.'): use 합쇼체")
        if re.search(r"[가-힣]요\.(?![가-힣])", text) and not re.search(r"(필요|중요|개요|주요)\.", text):
            report("WARN", no, "possible 해요체 ending ('~요.'): use 합쇼체")
        if "당신" in text:
            report("WARN", no, "'당신' for 'you': omit or use '사용자'")
        if "[검수 필요]" in text:
            report("ERROR", no, "review marker must be <!-- 검수 필요: reason -->, not [검수 필요]")
        words = re.findall(r"[A-Za-z]{2,}", text)
        hangul = re.findall(r"[가-힣]", text)
        if len(words) >= 8 and not hangul and not HEADING.match(line) and not line.lstrip().startswith(("[", "!", "|", "<")):
            report("WARN", no, "line looks untranslated")


def check_review_markers(dp):
    for no, line in dp:
        for m in REVIEW.finditer(line):
            report("REVIEW", no, m.group(1).strip())
            if HEADING.match(line):
                report("ERROR", no, "review marker inside a heading")
            before = line[: m.start()]
            if before.count("[") > before.count("]"):
                report("ERROR", no, "review marker inside link text")


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    with open(sys.argv[1], encoding="utf-8") as f:
        src = f.read()
    with open(sys.argv[2], encoding="utf-8") as f:
        dst = f.read()

    sf, sb, sp = parse(src)
    df, db, dp = parse(dst)
    st, dt = prose_text(sp), prose_text(dp)

    check_front_matter(sf, df)
    check_code_blocks(sb, db)
    compare_multiset("inline code", [m.group(2) for m in INLINE_CODE.finditer(st)],
                     [m.group(2) for m in INLINE_CODE.finditer(REVIEW.sub("", dt))])
    compare_multiset("link/image URL", LINK_URL.findall(st) + REF_URL.findall(st),
                     LINK_URL.findall(dt) + REF_URL.findall(dt))
    compare_multiset("shortcode", SHORTCODE.findall(st), SHORTCODE.findall(dt))
    check_structure(sp, dp)
    check_style(dp)
    check_review_markers(dp)

    order = {"ERROR": 0, "WARN": 1, "REVIEW": 2}
    for level, line, msg in sorted(problems, key=lambda p: (order[p[0]], p[1])):
        loc = f"line {line}: " if line else ""
        print(f"{level} {loc}{msg}")
    errors = sum(1 for p in problems if p[0] == "ERROR")
    reviews = sum(1 for p in problems if p[0] == "REVIEW")
    warns = len(problems) - errors - reviews
    print(f"\n{errors} error(s), {warns} warning(s), {reviews} review marker(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
