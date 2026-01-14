# Wonryeol Helper

디아블로4용 자동화 도우미 프로그램 (Windows 전용)

## 기능

### 1. 벨리알 탭 (아이템 줍기)
- 특정 색상의 아이템 텍스트 자동 감지
- 제외 색상 설정 (잘못 클릭 방지)
- 부드러운 마우스 이동 (144fps급)
- 검색 영역 설정

### 2. 신화장난꾸러기 탭
- 인벤토리 자동 정리
- 신화 장난꾸러기 아이템만 즐겨찾기
- 나머지 아이템 자동 버리기
- numpy 기반 초고속 색상 스캔

### 3. 아이템 버리기/팔기/먹기 탭
- 핫키로 빠른 아이템 관리

### 4. Home 탭 (대시보드)
- 모든 기능 한눈에 관리
- 전체 시작/중지
- 오버레이 제어
- 월드 보스 타이머
- 자동 업데이트

## 설치 방법

### 방법 1: EXE 실행 (권장)
GitHub Releases에서 `WonryeolHelper.exe` 다운로드 후 실행

### 방법 2: 소스 실행
```bash
pip install -r requirements.txt
python color_clicker_modern.py
```

## 자동 업데이트
- 프로그램 실행 시 자동으로 새 버전 확인
- 업데이트가 있으면 자동 다운로드 및 적용

## 필요 라이브러리
- pyautogui
- keyboard
- Pillow
- pywin32
- customtkinter
- mss
- numpy

## 라이선스
MIT License

## 면책 조항
이 프로그램은 교육 및 개인 사용 목적으로 제작되었습니다. 게임 이용 약관을 확인하고 책임감 있게 사용하세요.
