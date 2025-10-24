# 엄격 증거(strict-evidence) 검증 사용법(사람용)

이 문서는 로드맵 JSON의 `references[*].evidence` 값을 엄격하게 검사하는 방법을 설명합니다. 목적은 주장-근거의 추적 가능성을 높이고, 환각/모호 인용을 줄이는 것입니다.

## 무엇을 검사하나요?
- 형식 강제
  - 허용: `path:line`, `path#Lline`, `cmd: <command>`
  - 불허: 절대경로(`/...`), 외부 URL(`http://...`), 빈 문자열, 임의 포맷
- 경로 안전성
  - 저장소 내부 상대경로만 허용, 리포 밖으로 벗어나는 경로(`..`) 차단
- 존재 확인
  - 참조 파일이 실제 존재해야 하며, 지정한 라인 수가 파일 길이 이하여야 함

## 언제 쓰나요?
- PR/CI에서 로드맵의 품질 게이트로 사용
- 리뷰 전 로컬에서 빠르게 유효성 확인

## 빠른 사용법(로컬)
- 설치: `python -m pip install -r requirements-dev.txt`
- 단일 파일: `python -m tools.validate_roadmap roadmap.json --strict-evidence`
- 여러 파일: `python -m tools.validate_roadmap **/roadmap*.json --strict-evidence`
- 저장소 루트 지정(선택): `--repo-root .` (기본은 스크립트 기준 상위)

## 예시
- 허용 예시
  - `AGENTS.md:17`
  - `LLM_CHECKLIST.md#L49`
  - `cmd: pytest -q`
- 불허 예시(실패)
  - `README.md` (라인 미지정)
  - `/etc/passwd:1` (절대경로)
  - `https://example.com/page#L12` (외부 URL)
  - `cmd:` (명령어 내용 없음)

## 자주 실패하는 경우와 해결
- “unsupported format” → `path:line` 또는 `path#Lline` 또는 `cmd: ...` 중 하나로 수정
- “file does not exist” → 오타 수정 또는 파일 생성/경로 재확인
- “line N exceeds file length” → 실제 파일 길이 이내의 라인으로 조정
- “external URLs not allowed” → 내부 파일/라인 또는 `cmd:` 스니펫으로 대체

## CI(이미 구성됨)
- 워크플로: `.github/workflows/roadmap-validate.yml`
  - 모든 `roadmap*.json`에 대해 `--strict-evidence`로 검증합니다.
  - 실패 시 PR 체크가 실패하여 병합이 차단됩니다.

## 팁
- 라인 변동에 민감하므로, 문서 대규모 수정 전 PR에서 로드맵도 함께 업데이트하세요.
- 파일 근거가 어렵다면, 재현 가능한 명령 스니펫(`cmd:`)을 우선 사용하고 로그 일부를 `evidence`로 남기세요.

