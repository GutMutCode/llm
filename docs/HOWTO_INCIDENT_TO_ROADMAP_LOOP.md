# HOWTO: Incident → Decision → Plan Delta → Roadmap 루프(사람/LLM 공용)

이 문서는 로드맵 진행 중 발생하는 예기치 못한 문제를 LLM에게 위임하여 “해결책 탐색 → 결정 → 계획 변경 → 로드맵 반영”을 반복 가능하게 운영하는 방법을 설명합니다.

파일 한눈에 보기
- 스키마: `assets/schemas/decision.schema.json`, `assets/schemas/plan-delta.schema.json`
- 프롬프트: `assets/prompts/loop/01_*`, `02_*`, `03_*`, `04_*`
- 샘플: `assets/templates/decision.sample.json`, `assets/templates/plan-delta.sample.json`
- 도구: `tools/validate_decision.py`, `tools/validate_plan_delta.py`, `tools/roadmap_apply_delta.py`

사전 준비
- 개발 도구 설치: `python -m pip install -r requirements-dev.txt`

운영 절차
1) Intake & Explore(탐색)
   - LLM에 `assets/prompts/loop/01_intake_and_option_explore.txt`를 사용해 사건(incident) 설명을 제공
   - 결과물을 `decisions/ADR-<date>-<seq>.json`으로 저장(상태: proposed)
   - 검증: `python -m tools.validate_decision decisions/ADR-*.json`
2) Decision Gate(결정)
   - 선택할 옵션 id와 승인 여부를 입력으로 `assets/prompts/loop/02_decision_gate.txt` 사용
   - 같은 파일을 업데이트(상태: approved/rejected/needs-info, next_step 포함)
   - 검증: `python -m tools.validate_decision decisions/ADR-*.json`
3) Plan Delta(계획 변경)
   - 승인된 결정 JSON + 현재 로드맵(JSON)을 LLM에 제공하여 `assets/prompts/loop/03_plan_delta.txt` 실행
   - 산출물: `deltas/plan-delta-<decision-id>.json` (원자 연산 add/update/remove/reorder/set_next_step)
   - 검증: `python -m tools.validate_plan_delta deltas/plan-delta-*.json`
4) Integrate(적용/재검증)
   - 적용: `python -m tools.roadmap_apply_delta --roadmap roadmap.json --delta deltas/plan-delta-*.json`
   - 검증: `python -m tools.validate_roadmap --strict-evidence roadmap.json`

증거(Strict Evidence)
- 모든 사실(원인/위험/명령/파일)은 `path:line` 또는 `cmd:` 형식의 증거로 남깁니다.
- 예: `AGENTS.md:17`(명령), `LLM_CHECKLIST.md:49`(LLM 한계), `cmd: pytest -q`

우선순위/배치
- 우선순위는 로드맵의 `plan[]` 순서로 표현하며, 필요 시 `assets/prompts/loop/04_prioritize_and_integrate.txt`로 별도 `reorder` 델타를 생성합니다.

CI 연동
- `.github/workflows/decision-delta-validate.yml`가 `decisions/*.json`, `deltas/*.json`을 자동 검증합니다.

문제 해결 팁
- 델타가 커질 경우 작업 묶음을 쪼개 `ops`를 작은 단위로 구성하세요.
- 적용 전/후에 `tools/validate_roadmap.py --strict-evidence`로 스키마와 증거를 동시에 확인하세요.

