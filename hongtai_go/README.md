# Hongtai Go Studio

AI 바둑 기보 분석과 유튜브 방송 화면 제작을 위한 Windows 프로그램입니다.

## 실행

1. Python 3 설치
2. KataGo와 모델을 `D:\KataGo`에 설치
3. `run.bat` 실행
4. 브라우저에서 자동으로 열린 화면 사용

## 현재 버전

v0.8.2는 기존 v0.8.1 기능을 새 저장소 구조로 옮긴 **구조 전환 버전**입니다.

- SGF 불러오기 및 드래그앤드롭
- 3초 자동 재생
- 착수음과 초읽기
- 밝은 방송형 UI
- 녹화 모드
- KataGo AI 분석

## 실제 실행 파일 위치

- 백엔드 시작: `backend/app.py`
- 프론트 화면: `frontend/index.html`
- 주요 UI 로직: `frontend/js/app.js`
- 주요 스타일: `frontend/css/main.css`
- KataGo 설정: `config/analysis_hongtai.cfg`

`backend/sgf`, `backend/katago`, `backend/audio`, `backend/api`의 일부 파일은 이후 모듈 분리를 위한 준비 파일입니다. 현재 동작 코드는 `backend/app.py`와 `frontend/js/app.js`에 보존되어 있습니다.
