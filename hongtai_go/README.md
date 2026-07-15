# Hongtai Go Studio

AI 기반 바둑 명국 분석 및 방송용 제작 프로그램

---

# Project

Hongtai Go Studio는
SGF 기보를 불러와 KataGo AI로 분석하고
유튜브 방송용 화면을 제공하는 Windows 프로그램입니다.

목표

- AI 명국 분석
- KataGo 자동 분석
- 방송용 UI
- OBS 녹화 지원
- AI 해설
- AI 하이라이트 자동 추출

---

# Environment

OS
- Windows 10 / Windows 11

Python
- Python 3.13+

KataGo
- v1.16.5

GPU
- OpenCL 지원 GPU
- AMD RX560 이상 권장

---

# Folder Structure

D:\KataGo
    katago.exe
    analysis_example.cfg
    kata1-b18c384nbt-s9996604416-d4316597426.bin.gz

D:\Hongtai_Go_Studio

---

# Version History

## v0.1

- 프로젝트 시작
- 기본 UI
- 바둑판 표시

---

## v0.2

- 1920x1080 방송 화면
- OBS 녹화 모드

---

## v0.3

- 레이아웃 수정
- 화면 비율 개선

---

## v0.4

- KataGo 연동 시작
- 자동 분석 UI 추가
- 3초 자동 재생

---

## v0.5

- Python 서버
- KataGo 설정
- AI 분석 준비

---

## v0.5.2

### Fixed

- 실행하기.bat 인코딩 문제 수정
- Python 실행 오류 수정
- 브라우저 자동 실행 개선

---

## v0.6

### Added

- SGF Drag & Drop
- SGF Parser 개선
- 초기 배치(AB/AW) 지원
- 따냄 처리
- 샘플 기보 추가

---

## v0.7

### UI

- 밝은 테마 적용
- 원목 바둑판

### Sound

- 착수음 추가
- 착수음 ON/OFF

---

## v0.8

### New

- 방송모드
- 대국모드
- AI THINKING
- 초읽기
- REC 표시

### Fixed

- ESC 종료 후 버튼 사라짐 수정
- Fullscreen 복구
- Board Resize

---

## v0.8.1

### Fixed

- AI THINKING Overlay가 시작 시 계속 표시되는 버그 수정
- hidden/display 충돌 해결
- 방송모드 정상 동작

---

# Known Bugs

현재 알려진 문제

- AI 분석 속도 개선 필요
- 승률 그래프 애니메이션 개선 예정
- SGF Parser 일부 변형 포맷 테스트 필요

---

# Roadmap

## v0.9

- KataGo Analysis Engine 완성
- 승률 그래프 자동 생성
- AI 추천수
- PV 표시

---

## v1.0

- AI 자동 해설
- AI 하이라이트 추출
- Today's AI Game
- OBS Recording Studio
- EXE 배포

---

Copyright

HongtaiTV

2026
