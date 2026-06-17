# Classic Finder Agent Kit

한국어 번역문, 기억나는 문장, 강의노트식 표현에서 출발해 원전 후보를 여러 언어로 역추적하고, 공개적으로 사용할 수 있는 판본인지 검증한 뒤, 인용과 한국어 번역 작업지까지 만드는 AI 에이전트용 연구 키트입니다.

공개 고전 원전과 공개 학술문헌을 여러 자료원에서 교차 검색하고, 권리 상태를 확인한 뒤, 서지 인용과 한국어 번역 작업지까지 만드는 자족형 작업 디렉토리로 사용할 수 있습니다.

어디선가 본 시험 선택지, 어디선가 본 명언, 대충 입력해도 알아서 분해하고, 교차검토해서 출처를 여러 후보군에 걸쳐서 추적합니다.

이 키트는 Codex, Claude Code, Claude Cowork, Antigravity, Gemini 계열 에이전트처럼 "프로젝트 폴더의 지침 파일을 읽고 스크립트를 실행하는" 환경에서 쓰기 좋게 구성했습니다.

- 박승수 / Seungsoo Gordon Park, Seoul, South Korea.

## 무엇을 하는 도구인가

1. 한국어 문장을 그대로 받습니다.
2. 핵심어, 동의어, 개념어를 뽑습니다.
3. 영어, 프랑스어, 독일어, 라틴어, 그리스어, 한문 등 가능한 검색어로 확장합니다.
4. 검색 결과를 원전, 고전 번역본, 현대 번역본, 주석, 2차 해설로 나눕니다.
5. 유력 후보를 최대 5개까지 제시합니다.
6. 판본, URL, 안정 식별자, 권리 상태를 확인합니다.
7. 인용과 한국어 번역 작업지를 만듭니다.

## AI 에이전트에 붙여 쓰기

이 폴더를 Codex, Claude Code, Gemini CLI, Antigravity 같은 에이전트 작업 폴더로 열면 됩니다. 에이전트는 `AGENTS.md`와 `instructions/` 안의 지침을 먼저 읽고, 필요한 스크립트를 순서대로 실행합니다.

예를 들어 이런 식으로 요청할 수 있습니다.

```text
"인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다"의 원전을 찾아줘.
원어 원전, 공개 번역본, 권리 상태, 한국어 번역 작업지까지 만들어줘.
```

출력물은 기본적으로 `results/`에 저장됩니다.

## 빠른 시작: 한국어 문장에서 원전 후보 찾기

한국어 번역문이나 기억 속 문장에서 원전 후보를 역추적할 때:

```bash
python scripts/expand_korean_keywords.py "인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다" --author "Rousseau" --work "Social Contract"
python scripts/expand_multilingual_queries.py "인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다" --author "Rousseau" --work "Social Contract"
python scripts/reverse_trace_multilingual.py "인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다" --author "Rousseau" --work "Social Contract"
python scripts/make_trace_report.py results/reverse_trace_results.json
```

## 빠른 시작: 알려진 원전 처리하기

저자, 작품명, 장절이 비교적 분명한 경우:

```bash
python scripts/search_all.py "Thomas Hobbes Leviathan Chapter 17" --limit 5
python scripts/resolve_work.py results/search_results.json "Leviathan Chapter 17"
python scripts/build_manifest.py "https://en.wikisource.org/wiki/Leviathan_(1651)/Chapter_17"
python scripts/extract_text.py "https://en.wikisource.org/wiki/Leviathan_(1651)/Chapter_17"
python scripts/make_citation.py results/extracted_text.json
python scripts/translate_ko.py results/extracted_text.json
```

## 로컬 환경 점검

이 키트는 외부 파이썬 패키지를 요구하지 않지만, 실제 Python 3.10 이상 런타임은 필요합니다. Windows에서 `python`이 Microsoft Store 실행 별칭으로 잡히면 스크립트가 실행되지 않을 수 있습니다. 이 경우 Python을 설치한 뒤 Windows 설정의 앱 실행 별칭에서 `python.exe`, `python3.exe` 별칭을 끄세요.

PowerShell에서 먼저 점검할 수 있습니다.

```powershell
.\scripts\check_environment.ps1
```

PowerShell 실행 정책 때문에 막히면 다음처럼 1회성으로 실행하거나, `scripts\check_environment.cmd`를 실행하세요.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check_environment.ps1
```

Python이 설치되어 있지만 PATH에 아직 반영되지 않았다면 실행 파일 경로를 직접 넘길 수 있습니다.

```powershell
.\scripts\check_environment.cmd -Python "C:\Path\To\python.exe"
```

한글이 깨져 보일 때는 파일이 손상된 것이 아니라 콘솔 표시 인코딩 문제일 수 있습니다. PowerShell 7 사용을 권장하며, Windows PowerShell에서는 필요할 때 다음을 먼저 실행하세요.

```powershell
chcp 65001
```

## GitHub 관리 권장

Git 저장소는 이 폴더(`Classic-Finder-Chunokkun`)를 루트로 초기화하는 편이 좋습니다. `results/`, `work/`, `data/`의 실행 산출물은 기본적으로 무시하고, 재사용할 만한 결과만 `examples/`로 옮겨 관리하세요. 이 저장소에는 UTF-8과 줄바꿈 기준을 위한 `.editorconfig`, `.gitattributes`, 생성물 제외를 위한 `.gitignore`, 그리고 GitHub Actions용 smoke test가 포함되어 있습니다.

커밋, push, 태그, GitHub Release를 준비할 때는 `instructions/RELEASE_WORKFLOW.md`를 따릅니다. 기본 원칙은 충분히 검증한 뒤 변경 범위를 설명하고, 사용자가 push 또는 release를 승인했을 때만 원격 저장소에 반영하는 것입니다.

## 디렉토리

```text
Classic-Finder-Chunokkun/
  AGENTS.md                 # Codex 계열 진입 지침
  CLAUDE.md                 # Claude Code/Cowork 진입 지침
  ANTIGRAVITY.md            # Antigravity 계열 진입 지침
  GEMINI.md                 # Gemini 계열 진입 지침
  instructions/             # 공통 작업 지침
    RELEASE_WORKFLOW.md     # 검증, push, 태그, 릴리스 절차
  config/                   # 자료원, 별칭, 권리 판정 규칙
  scripts/                  # 검색, 구조화, 추출, 인용, 번역 작업지, 키워드 확장, 역추적 보고서 생성
  examples/                 # 요청서 예시와 출력 예시
  data/                     # 로컬 보강 데이터 위치
  work/                     # 중간 산출물
  results/                  # 최종 산출물
```

## 기본 원칙

1. 원문을 바로 번역하지 않습니다. 먼저 자료원, 판본, 내부 구조, 권리 상태를 확인합니다.
2. Scribd 같은 업로드 기반 플랫폼은 단서 검색용으로만 씁니다. 실제 인용과 번역은 신뢰 가능한 원문 자료원에서 확정합니다.
3. Wikisource, Project Gutenberg, Internet Archive, HathiTrust, Open Library, Perseus/Scaife, DOAJ, DOAB/OAPEN, Kanseki Repository, CBETA, Chinese Text Project, 한국고전종합DB를 역할별로 분리합니다.
4. 권리 상태는 `public_domain`, `cc_by`, `cc_by_sa`, `cc_by_nc_sa`, `open_access`, `search_only`, `unknown` 중 하나로 표시합니다.
5. 한국어 번역은 문단 또는 장절 단위로 원문과 1:1 대조 가능하게 만듭니다.
6. 한국어 번역문에서 출전을 역추적할 때는 원어 원전, 고전적 번역본, 현대 번역본, 주석, 후대 해석, 현대 해설을 구분합니다.
7. 역추적 결과는 정답 하나가 아니라 최대 5개의 후보군과 불확실성 표시로 제시합니다.

## 권장 작업 순서

```text
search_all -> resolve_work -> build_manifest -> rights_check -> extract_text -> make_citation -> translate_ko
```

역추적 작업:

```text
expand_korean_keywords -> expand_multilingual_queries -> reverse_trace_multilingual -> make_trace_report -> user_selection -> extract_text/build_manifest
```

복잡한 책은 `build_manifest.py`를 반드시 먼저 실행하세요. 예를 들어 Locke의 `Two Treatises of Government`처럼 한 작품 안에 `First Treatise`, `Second Treatise`가 갈라지는 경우, manifest가 길 안내 역할을 합니다.

## 주의

이 키트는 연구와 교육 목적의 자동화 보조 도구입니다. 저작권 판단은 최종 법률 자문이 아니며, 공개 배포나 상업적 이용 전에는 각 자료원의 원문 권리 표시와 이용약관을 다시 확인해야 합니다.
