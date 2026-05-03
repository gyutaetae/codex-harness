# harness

Codex CLI 기반 자율 구현 하네스. 사용자의 한 줄 요구를 받아 단계별 sub-agent가
artifact를 통해 결과를 전달하며 직렬로 구현까지 끝내는 파이프라인.

## 파이프라인

```
요구 한 줄
   ↓
[1. initial-plan]   요구사항 / 구현 디테일 / 제약 / 완료 기준
   ↓ artifact: 01-initial-plan.md
[2. clarify]        9단계: feasibility → tech-stack → user-flow → ui → api
   ↓                       → data → architecture → tech-decisions → final-doc
   │                (사용자 프롬프트는 매 단계 자동 기록)
   ↓ artifact: 02-clarify.md + prompts/clarify/01~09-*.md
[3. context-gather] 빈 코드베이스면 스킵
   ↓ artifact: 03-context.md
[4. plan]           task-created.md 규격에 따라 task/phase 파일 생성
   ↓ artifact: tasks/{id}-{name}/index.json + phase{N}.md
[5. generate]       scripts/run_phases.py 가 codex 직렬 실행
   ↓
[6. evaluate]       단순 MVP면 스킵
   ↓ artifact: 05-evaluate.md
```

## 디렉토리

```
.codex/skills/plan-and-build/
  SKILL.md            ← 전체 흐름 (orchestrator가 따름)
  agents/             ← stage별 sub-agent prompt 6개

prompts/
  task-created.md     ← plan stage가 따르는 task/phase 생성 규격

scripts/
  run_phases.py       ← codex 직렬 실행 runner
  gen_docs_diff.py    ← phase 0 후 docs-diff.md 자동 생성
  _utils.py

tasks/
  index.json
  {id}-{name}/
    index.json
    artifacts/        ← 각 stage의 출력
    prompts/clarify/  ← clarify 9단계 사용자 프롬프트 원문
    phase{N}.md       ← codex가 실행할 phase 파일
    phase{N}-output.json
    docs-diff.md      ← 자동 생성

docs/                 ← phase 0가 갱신/생성하는 프로젝트 문서
```

## 사용

orchestrator(IDE의 코딩 에이전트)에게 한 줄 요구를 던진다:

```
하네스 시작: <요구사항>
```

orchestrator가 SKILL.md를 따라 stage 1~4까지 사용자와 함께 진행하고, stage 5에서
runner를 실행한다:

```bash
python scripts/run_phases.py {id}-{name}
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `CODEX_BIN` | `codex` | codex CLI 경로 |
| `CODEX_MODEL` | `gpt-5-codex` | 사용할 모델 |
| `PHASE_TIMEOUT` | `1800` | 각 phase 최대 실행 시간 (초) |
| `SKIP_GIT` | `0` | `1`이면 git 커밋 시도 안 함 |

## GitHub에 올리기 (`gyutaetae/harness`)

이 PC에는 `gh` 로그인이 없어 자동 푸시는 못 했다. **gyutaetae 계정 PAT**으로 한 번에 생성+푸시:

```powershell
cd C:\Users\kym70\OneDrive\Desktop\harness
$env:GH_TOKEN = "<PAT>"   # repo 권한 (classic) 또는 fine-grained Contents+Metadata
python scripts/publish_to_github.py
```

기본값: 소유자 `gyutaetae`, 레포 이름 `harness`, 브랜치 `main`. 바꾸려면 `GITHUB_OWNER`, `GITHUB_REPO`, `DEFAULT_BRANCH` 환경 변수 사용.

## 요구사항

- Python 3.10+ (`from __future__ import annotations` 사용으로 3.9에서도 동작은 함)
- codex CLI (`codex exec` 지원 버전)
- (옵션) git — 자동 커밋 사용 시
