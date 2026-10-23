# skill-aws-ko-translation

AWS 영문 문서(사용 설명서, API 레퍼런스, 블로그, 백서, 워크샵)를 AWS 한국어 공식 문서
문체로 번역하는 [Claude Code](https://claude.com/claude-code) skill입니다.

- 번역 규칙: [`references/translation-rules.md`](references/translation-rules.md)
  ([doc-aws-ko-translation-rules](https://github.com/conft2k/doc-aws-ko-translation-rules)의
  `README.md`와 같은 내용)
- 입력: docs.aws.amazon.com URL, Markdown 파일, 붙여 넣은 텍스트
- 출력: 원문 옆의 `*.ko.md`. 원문은 덮어쓰지 않습니다.
- 검사: 번역이 끝나면 원문과 대조해 코드·인라인 코드·URL·쇼트코드·front matter·제목
  레벨·표 구조가 바뀌지 않았는지 확인하고, 문체(`~하십시오`, 해라체, 해요체, "당신")와
  `<!-- 검수 필요: ... -->` 표시를 보고합니다.

## 구성

| 경로 | 내용 |
|---|---|
| `SKILL.md` | Claude가 따르는 작업 순서 |
| `references/translation-rules.md` | 번역 규칙 전체 |
| `scripts/fetch_aws_doc.py` | AWS 문서 URL을 Markdown으로 변환 (`uv run --with beautifulsoup4 --with markdownify`) |
| `scripts/check_translation.py` | 원문과 번역 대조 검사 (표준 라이브러리만 사용) |

## 설치

`~/.claude/skills/skill-aws-ko-translation`에 이 저장소가 보이면 됩니다.

```bash
gh repo clone conft2k/skill-aws-ko-translation ~/dev/skill-aws-ko-translation
ln -sfn ~/dev/skill-aws-ko-translation ~/.claude/skills/skill-aws-ko-translation
```

## 사용 예

```text
https://docs.aws.amazon.com/AmazonS3/latest/userguide/create-bucket-overview.html 한국어로 번역해줘
workshop/content/01-setup.md 번역해줘
이 번역본 규칙대로 됐는지 검토해줘: setup.en.md / setup.ko.md
```

검사 스크립트만 따로 돌릴 수도 있습니다.

```bash
python3 scripts/check_translation.py source.en.md source.ko.md
```

## 규칙 수정

규칙의 원본은 doc-aws-ko-translation-rules 저장소입니다. 그쪽을 고친 뒤 이 저장소로
복사해서 커밋합니다.

```bash
cp ~/dev/doc-aws-ko-translation-rules/README.md references/translation-rules.md
```
