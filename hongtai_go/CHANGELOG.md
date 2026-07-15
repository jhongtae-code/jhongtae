# Changelog

## v0.8.2

### Changed
- GitHub 관리용 표준 디렉터리 구조로 재편
- 프론트엔드를 `frontend/`로 이동
- Python 서버를 `backend/app.py`로 이동
- KataGo 분석 설정을 `config/`로 이동
- 루트 실행 파일을 `run.py`, `run.bat`로 통일

### Preserved
- v0.8.1의 SGF 재생, 착수음, 초읽기, 녹화 모드, KataGo 분석 기능 유지

## v0.8.1

### Fixed
- 시작 시 AI THINKING 오버레이가 계속 표시되는 문제 수정

## v0.8

### Added
- 대국 모드와 방송 모드
- AI THINKING 및 3·2·1 초읽기
- REC 표시

### Fixed
- ESC로 전체화면 종료 후 녹화/전체화면 버튼이 사라지는 문제 수정
