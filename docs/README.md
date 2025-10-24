# 문서 인덱스

- HOWTO: LLM 로드맵 작성 가이드 — `docs/HOWTO_ROADMAP_AUTHORING.md`
- HOWTO: 엄격 증거(strict-evidence) 검증 — `docs/HOWTO_STRICT_EVIDENCE.md`
- LLM 사용 중 확인된 문제 목록 — `docs/LLM_KNOWN_ISSUES.md`
- HOWTO: Incident→Decision→Plan Delta→Roadmap 루프 — `docs/HOWTO_INCIDENT_TO_ROADMAP_LOOP.md`

설명
- LLM에게 로드맵 작성을 위임할 때 사용할 프롬프트/체크리스트/스키마/샘플의 위치와 절차를 안내합니다.
- 저장 위치
  - 스키마: `assets/schemas/roadmap.schema.json`
  - 체크리스트: `assets/prompts/roadmap/authoring_checklist.md`
  - 프롬프트: `assets/prompts/roadmap/authoring_prompt.txt`
  - 샘플: `assets/templates/roadmap.sample.json`
  - 운영 루프 프롬프트: `assets/prompts/loop/*.txt`
  - 의사결정/델타 스키마: `assets/schemas/decision.schema.json`, `assets/schemas/plan-delta.schema.json`

업데이트 방법
- 새 HOWTO 문서를 추가할 때 이 인덱스를 함께 갱신하세요.
