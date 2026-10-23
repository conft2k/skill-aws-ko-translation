---
name: skill-aws-ko-translation
description: Translate AWS documentation (user guides, API references, blog posts, whitepapers, workshops) from English into Korean in the style of the official AWS Korean docs, keeping code, identifiers, links and Markdown structure intact and checking the result against the source. Use when asked to translate AWS content into Korean ("한국어로 번역", "번역해줘", "translate to Korean") from a docs.aws.amazon.com URL, a Markdown file or pasted text, or to review or fix an existing Korean translation of AWS content.
---

# skill-aws-ko-translation

Translate English AWS content into Korean under the rules in
`references/translation-rules.md`, then prove the translation against the source with
`scripts/check_translation.py`. The rules decide every wording question; the checker
catches what a careful read still misses (a changed code line, a dropped link, a
rewritten URL, a broken table).

The skill is installed at `~/.claude/skills/skill-aws-ko-translation/`. Run its scripts
by that path. The checker needs only Python; the fetcher needs two packages, run with
`uv run --with beautifulsoup4 --with markdownify python ...`.

## Workflow

### 1. Get the source as a Markdown file

The checker compares two files, so the source is always a file on disk.

- **Markdown file**: use it as is.
- **URL** (docs.aws.amazon.com or another AWS page): fetch it.

  ```bash
  uv run --with beautifulsoup4 --with markdownify python -I \
    ~/.claude/skills/skill-aws-ko-translation/scripts/fetch_aws_doc.py URL -o <slug>.en.md
  ```

  `<slug>` is the last path segment of the URL without `.html`. Save in the current
  directory unless the user names another place. Skim the result against the page; the
  fetcher keeps headings, lists, tables, links, note boxes and code blocks, but a page
  with unusual markup can lose a piece.
- **Pasted text**: write it to `source.en.md` in the scratchpad directory.

Translation output goes next to the source: `x.md` → `x.ko.md`, `<slug>.en.md` →
`<slug>.ko.md`. Never overwrite the source.

### 2. Read the rules

Read `references/translation-rules.md` in full before writing a single sentence. It
fixes the sentence endings, the term table, the note-box labels and UI verbs, what stays
in English, the particle rule after English tokens, and the exact format of the
`<!-- 검수 필요: ... -->` marker.

### 3. Build the term sheet

Go through the whole source once and list every term that needs a decision: AWS
service names (kept as written), terms from the rules' term table, console UI labels,
and anything new. Fix one Korean rendering per term, and mark the terms you cannot
confirm for a `검수 필요` marker. The sheet is what keeps a long document consistent
from its first section to its last; it stays in your working notes, not in the output.

### 4. Translate

Write the translation file in one pass for a short document, section by section (one
`##` at a time, appending to the file) for a long one, applying the term sheet
throughout. The output file holds the translation only — no preface, no notes, no
summary; the sole additions are first-mention pairings the term table asks for and
`검수 필요` markers.

### 5. Check against the source

```bash
python3 -I ~/.claude/skills/skill-aws-ko-translation/scripts/check_translation.py SOURCE.md TRANSLATION.md
```

- **ERROR**: a rule is broken (code, inline code, URL, shortcode, front matter value,
  heading levels or table columns changed, or a misplaced review marker). Fix the
  translation, never the source, and re-run.
- **WARN**: a signal worth a look — a `~하십시오`, `~다.` or `~요.` ending, `당신`, a
  line that still reads as English, an inline code span or URL the source lacks. Fix
  the real ones; a warning that is correct as written (a quoted English UI string, a
  product name line) stays.
- **REVIEW**: lists every `검수 필요` marker.

The step is done when the checker reports **0 errors** and every warning has been
fixed or judged correct.

### 6. Report

Reply in Korean with: the output path, the checker's final count line, every `검수 필요`
marker (line and reason) so the user knows what to verify, and any warning you left in
place with the reason. For pasted text, also show the translation in the reply.

## Reviewing an existing translation

When the user hands over a Korean translation to review or fix, do steps 1, 2 and 5
with their source and translation, then read both side by side for what the checker
cannot see: meaning dropped or added, terms that drift between sections, UI labels and
note-box labels off the standard, particles after English tokens. Report findings with
line numbers, most serious first; edit the translation only when asked to fix it.
