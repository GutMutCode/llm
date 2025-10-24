# LLM 로드맵 작성 가이드(사람용)

이 문서는 사람이 LLM에게 “로드맵 작성”을 위임할 때, 저장소에 추가된 템플릿/체크리스트/스키마를 어떻게 사용하는지 단계별로 설명합니다. 결과물은 항상 JSON(스키마 준수)로 받아 팀에서 바로 검토/버전관리할 수 있습니다.

## 파일 한눈에 보기
- 스키마: `assets/schemas/roadmap.schema.json` — 로드맵 JSON의 구조와 제약을 정의합니다.
- 체크리스트: `assets/prompts/roadmap/authoring_checklist.md` — LLM이 따라야 할 규칙(MUST/SHOULD), 필드 길이 제한, 증거 인용 방법.
- 프롬프트: `assets/prompts/roadmap/authoring_prompt.txt` — 그대로 복사/붙여넣기 해서 LLM에게 지시할 기본 프롬프트.
- 샘플: `assets/templates/roadmap.sample.json` — 완성된 예시(JSON만 포함). 비교/참고용.

## 빠른 시작(LLM에게 로드맵 작성시키기)
1) 프롬프트 복사: `assets/prompts/roadmap/authoring_prompt.txt` 내용을 LLM 입력창에 붙여넣습니다.
2) 환경값 확인: 프롬프트 하단의 Environment 블록(파일시스템/네트워크/승인/민감데이터/시간)을 현재 작업 상황에 맞게 수정합니다.
3) “JSON만 출력”을 재강조: LLM이 코드블록 또는 평문으로 JSON만 출력하도록 유도합니다(프롬프트에 이미 포함됨).
4) 결과 저장: LLM이 출력한 JSON을 예: `roadmap.json` 으로 저장합니다.
5) 샘플 대조: `assets/templates/roadmap.sample.json` 과 구조를 비교해 빠르게 sanity check 합니다.

## 검증 스크립트 사용법(사람/CI 공통)
- 로컬 실행
  - `python -m pip install -r requirements-dev.txt`
  - `python -m tools.validate_roadmap roadmap.json`
  - 여러 파일/글롭 지원: `python -m tools.validate_roadmap **/roadmap*.json`
- 무엇을 검사하나요?
  - 스키마 적합성: `assets/schemas/roadmap.schema.json` 기준
  - 추가 규칙: `references` 최소 3개 존재 여부
- 엄격 증거 검사(옵션): `--strict-evidence`
  - `references[*].evidence` 형식 강제: `path:line`, `path#Lline`, 또는 `cmd: ...`
  - 파일 경로는 저장소 내부 상대경로만 허용(절대경로/URL 금지), 해당 라인이 실제 존재해야 함
  - 예) 허용: `AGENTS.md:17`, `LLM_CHECKLIST.md#L49`, `cmd: pytest -q`
- 종료코드
  - 0: 통과, 1: 검증 실패, 2: 스키마 로드/의존성 오류

## CI 연동(이미 구성됨)
- GitHub Actions: `.github/workflows/roadmap-validate.yml`
  - 샘플 파일과 저장소 내 `roadmap*.json` 전부를 검증하며 `--strict-evidence` 옵션을 사용
  - 실패 시 PR 체크가 붉게 표시되어 병합이 차단됨

## 체크리스트 핵심(LLM이 반드시 지켜야 할 것)
- 출력 형식: “JSON만” 출력. 스키마(`assets/schemas/roadmap.schema.json`)를 반드시 만족.
- 목적/범위/지표: 간결(지표 1–3개). 과도한 장문 금지.
- 증거 인용: 모든 사실 주장에는 파일 경로나 명령 출력 일부를 근거로 포함(`path:line` 권장). 예: `AGENTS.md:17`.
- 계획 항목 수: 5–12개. 각 항목은 측정 가능한 성공 기준(1–3개)과 검증 절차(테스트/로그)를 포함.
- LLM 한계 반영: 컨텍스트 길이, 환각 방지, 결정적 진행(“next_step” 1개) 등을 `meta.llm_limitations`에 명시.
- 보안/비밀: 실제 키는 금지. `.example` 파일만 커밋 참조.

자세한 규칙은 `assets/prompts/roadmap/authoring_checklist.md` 를 참고하세요.

## 스키마(간단 해설)
로드맵 JSON은 다음 최상위 키를 가집니다.
- `meta`: 생성 정보와 LLM 한계 반영 필드.
- `inputs`: 목적/범위/성공지표, 환경 제약(파일시스템/네트워크/승인/민감도/시간 등).
- `plan`(배열): 5–12개의 작업 단위. 각 항목은 `goal`, `success_criteria`, `deliverables`, `validation(증거 캡처 명령)`, `risk_level` 등을 포함.
- `validation`: 전체 수준의 린트/테스트/커버리지/로그 정책 요약.
- `risks`: 리스크/영향/대응/트리거.
- `release`: 변경 요약, 마이그레이션, 롤백, 문서 업데이트 경로.
- `references`: 주장과 증거(파일 경로/라인 또는 명령 출력) 매핑.
- `open_questions`: 남은 질문/가정.
- `next_step`: 지금 당장 수행할 1개 단계와 간단한 프롬프트.

필수 필드 및 값 제약은 스키마 파일(`assets/schemas/roadmap.schema.json`)에 정의되어 있습니다.

## 생성물 검토 체크(사람 검수용)
- [ ] JSON만 포함되었는가? 불필요한 주석/문자열 없음
- [ ] 필수 키(`meta/inputs/plan/validation/risks/release/next_step`) 존재
- [ ] `inputs.success_metrics` 1–3개, 간결/측정 가능
- [ ] `plan` 항목 수 5–12개, 각 항목 `success_criteria` 1–3개, `validation.evidence`에 실제로 실행 가능한 명령이 기재됨
- [ ] `references` 최소 3개 이상, `path:line` 또는 명령 출력 일부 포함
- [ ] `meta.llm_limitations`에 컨텍스트 제한/환각 방지/결정적 진행/기억 로깅/도구 교차검증이 기술됨
- [ ] `next_step`이 정확히 1개 단계만 지시하며 모호하지 않음

## 팀 워크플로 제안
- 버전관리: 생성된 `roadmap.json`을 PR에 포함시키고, 설명란에 주요 성공지표와 `next_step`을 붙입니다.
- 규칙 정렬: PR에서 `AGENTS.md`의 커밋/PR 가이드를 준수합니다(Conventional Commits, 스크린샷/로그 첨부 등).
- 변경 추적: 로드맵이 갱신될 때마다 `references`와 `open_questions`를 업데이트해 의사결정 근거를 남깁니다.

## 자주 있는 문제와 해결
- 문제: LLM이 설명 문장까지 함께 출력함 → 해결: 프롬프트 첫 줄에 “JSON만 출력”을 재강조하고, 코드블록 없이 출력하도록 지시.
- 문제: 스키마 필수 키 누락 → 해결: `assets/templates/roadmap.sample.json`과 대조 후 필드 추가.
- 문제: 증거 인용 없음 → 해결: 관련 근거를 파일 경로/라인으로 추가(예: `LLM_CHECKLIST.md:49`).
- 문제: 계획 항목 과다/장문 → 해결: 5–12개로 줄이고 각 필드 1–2문장 이내로 축약.

## 참고
- 체크리스트 근거: `LLM_CHECKLIST.md`
- 저장소 규칙/명령: `AGENTS.md`
