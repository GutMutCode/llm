# LLM 운영 루프(Incident → Options → Decision → Plan Delta → Roadmap)

반복적으로 발생하는 “예상치 못한 문제 → 해결책 탐색 → 선택/결정 → 계획 수립 → 로드맵 반영” 패턴을 LLM에게 위임하기 위한 표준 운영 루프와 산출물(스키마)을 정의합니다.

핵심 아이디어
- 산출물을 JSON으로 표준화하고(검증 가능), 각 단계에 전용 프롬프트를 제공해 반복 가능하게 만듭니다.
- 의사결정은 `decisions/*.json`(ADR 스타일), 계획 변경은 `deltas/*.json`(plan-delta)로 관리합니다.
- 델타는 스크립트로 기존 `roadmap.json`에 안전하게 적용하고(schema 재검증), 증거는 `path:line`/`cmd:` 형식으로 남깁니다.

필수 구성요소
- 프롬프트: `assets/prompts/loop/` (01~04 단계별 템플릿)
- 스키마: `assets/schemas/decision.schema.json`, `assets/schemas/plan-delta.schema.json`
- 샘플: `assets/templates/decision.sample.json`, `assets/templates/plan-delta.sample.json`
- 도구: `python -m tools.roadmap_apply_delta --roadmap roadmap.json --delta deltas/plan-delta-*.json`
- 검증: `python -m tools.validate_decision decisions/*.json`, `python -m tools.validate_plan_delta deltas/*.json`

운영 루프(사람 ↔ LLM)
1) Intake & Explore(탐색)
   - 입력: 사건/문제 설명(incident), 현재 로드맵(`roadmap.json` 권장)
   - 프롬프트: `assets/prompts/loop/01_intake_and_option_explore.txt`
   - 출력: `decisions/ADR-<date>-<seq>.json` (상태: proposed, 옵션 목록/증거 포함)
2) Decision Gate(결정 게이트)
   - 입력: 위 결정 JSON + 선택 옵션 id + 승인 여부/보류 사유
   - 프롬프트: `assets/prompts/loop/02_decision_gate.txt`
   - 출력: 같은 파일 업데이트(상태: approved/rejected), `next_step` 포함
3) Plan Delta(계획 변경 산출)
   - 입력: 승인된 결정 JSON + 최신 로드맵 JSON
   - 프롬프트: `assets/prompts/loop/03_plan_delta.txt`
   - 출력: `deltas/plan-delta-<decision-id>.json` (add/update/remove/reorder/set_next_step 연산)
4) Integrate(적용/검증)
   - 적용: `python -m tools.roadmap_apply_delta --roadmap roadmap.json --delta deltas/plan-delta-*.json`
   - 검증: `python -m tools.validate_roadmap --strict-evidence roadmap.json`
   - CI: `.github/workflows/decision-delta-validate.yml`가 decisions/*, deltas/*를 자동 검증

증거와 승인
- 모든 사실 주장은 `references[*].evidence`에 `path:line` 또는 `cmd: ...`로 남깁니다(예: `AGENTS.md:17`, `LLM_CHECKLIST.md:49`).
- 파괴적 변경/보안 민감 변경은 Decision Gate에서 `approval.required=true`로 게이트합니다.

스키마 간 계약
- decision.json: 문제 맥락/옵션/결정/근거/다음 단계(JSON 스키마 준수)
- plan-delta.json: 로드맵 `plan[]`에 대한 원자 연산 모음(add/update/remove/reorder/set_next_step)
- roadmap.json: 기존 스키마(`assets/schemas/roadmap.schema.json`) 그대로 사용; 우선순위는 `plan[]`의 순서로 표현

운영 팁
- 단 한 단계씩(next_step)만 실행 후 재평가(LLM_CHECKLIST.md: “결정적 진행”).
- 델타는 작은 묶음으로 PR화하고, PR 설명에 decisions/deltas 경로와 로그/테스트 증거를 첨부.
- 실패/변경 사유는 decision.json의 `consequences`와 `open_questions`에 누적 기록.

참고
- 구조/명령: `AGENTS.md`
- 로드맵 작성 HOWTO: `docs/HOWTO_ROADMAP_AUTHORING.md`
- 엄격 증거: `docs/HOWTO_STRICT_EVIDENCE.md`

