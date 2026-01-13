# Color Clicker Pro

디아블로4용 색상 인식 자동 클릭 프로그램 (Windows 전용)

## 기능

### 1. 아이템 줍기 탭
- 특정 색상의 아이템 텍스트 자동 감지
- 제외 색상 설정 (잘못 클릭 방지)
- 부드러운 마우스 이동 (144fps급)
- 검색 영역 설정

### 2. 신화장난꾸러기 탭
- 인벤토리 자동 정리
- 신화 장난꾸러기 아이템만 즐겨찾기
- 나머지 아이템 자동 버리기
- numpy 기반 초고속 색상 스캔

## 설치 방법

### 방법 1: 소스 실행 (권장)
```bash
pip install -r requirements.txt
python color_clicker_modern.py
```

또는 `install_and_run.bat` 더블클릭

### 방법 2: EXE 빌드
`build_modern.bat` 실행 → `dist/ColorClickerPro.exe` 생성

> ⚠️ **참고**: EXE 파일은 PyInstaller + 자동화 라이브러리 조합으로 인해 일부 백신에서 오탐지될 수 있습니다. 소스 코드를 직접 확인하시면 악성 코드가 없음을 확인할 수 있습니다.

## 필요 라이브러리
- pyautogui
- keyboard
- Pillow
- pywin32
- customtkinter
- mss
- numpy

## 사용법

1. 프로그램 실행
2. 타겟 색상 추가 (화면 추출 또는 직접 입력)
3. 검색 영역 설정
4. 트리거 키 설정
5. 시작 버튼 클릭
6. 트리거 키로 활성화/비활성화

## 라이선스
MIT License - 자유롭게 사용, 수정, 배포 가능

## 면책 조항
이 프로그램은 교육 및 개인 사용 목적으로 제작되었습니다. 게임 이용 약관을 확인하고 책임감 있게 사용하세요.
