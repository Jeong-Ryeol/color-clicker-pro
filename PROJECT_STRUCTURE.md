# Wonryeol Helper - 프로젝트 구조 문서

## 개요
- **프로젝트명**: Wonryeol Helper (색상 감지 자동화 도구)
- **버전**: constants.py의 `VERSION` 변수
- **플랫폼**: Windows 전용
- **용도**: 디아블로4 자동화 도우미

---

## 진입점

### main.py (실제 진입점)
```
main.py
├── DPI 인식 설정 (SetProcessDpiAwareness)
├── CustomTkinter 테마 설정 (dark, blue)
├── 라이브러리 검증 (pyautogui, keyboard, PIL, win32api, mss, numpy)
└── ColorClickerApp 실행 (from app import ColorClickerApp)
```

**중요**: PyInstaller 빌드 시 `main.py`를 진입점으로 사용해야 함!

---

## 파일 구조

```
color-clicker-pro/
├── main.py                    # 진입점 (DPI + 테마 + 앱 실행)
├── app.py                     # 메인 클래스 (모든 Mixin 조합)
├── constants.py               # 상수 (VERSION, COLORS, CONFIG_FILE 등)
│
├── features/                  # 기능 모듈 (Mixin 패턴)
│   ├── __init__.py
│   ├── belial.py              # BelialMixin - 색상 감지 자동 클릭
│   ├── inventory.py           # InventoryMixin - 인벤토리 정리
│   ├── discard.py             # DiscardMixin - 아이템 버리기
│   ├── sell.py                # SellMixin - 아이템 팔기
│   ├── consume.py             # ConsumeMixin - 아이템 먹기 V1
│   ├── consume2.py            # Consume2Mixin - 아이템 사기 V2
│   ├── skill_auto.py          # SkillAutoMixin - 자동 스킬 (5개 프리셋)
│   └── quick_button.py        # QuickButtonMixin - 빠른 버튼
│
├── ui/                        # UI 모듈
│   ├── __init__.py
│   ├── main_window.py         # MainWindowMixin - 메인 윈도우 + 탭
│   └── overlay.py             # OverlayMixin - 오버레이 창
│
├── utils/                     # 유틸리티 모듈
│   ├── __init__.py
│   └── updater.py             # UpdaterMixin - 자동 업데이트
│
├── build_modern.bat           # 빌드 스크립트 (이것 사용)
├── requirements.txt           # 의존성 목록
└── color_clicker_config.json  # 설정 파일 (자동 생성)
```

---

## 아키텍처

### Mixin 패턴
`app.py`의 `ColorClickerApp` 클래스가 모든 Mixin을 상속:

```python
class ColorClickerApp(
    ctk.CTk,              # CustomTkinter 기본 클래스
    BelialMixin,          # 색상 감지
    InventoryMixin,       # 인벤토리 정리
    DiscardMixin,         # 버리기
    SellMixin,            # 팔기
    ConsumeMixin,         # 먹기 V1
    Consume2Mixin,        # 먹기 V2
    SkillAutoMixin,       # 자동 스킬
    QuickButtonMixin,     # 빠른 버튼
    OverlayMixin,         # 오버레이
    MainWindowMixin,      # 메인 UI
    UpdaterMixin          # 업데이트
):
```

### Import 관계
```
main.py
└── app.py (ColorClickerApp)
    ├── constants.py
    ├── features/*.py (8개 Mixin)
    ├── ui/*.py (2개 Mixin)
    └── utils/*.py (1개 Mixin)
```

---

## 빌드 방법

### build_modern.bat 사용
```batch
python -m PyInstaller --onefile --noconsole --name "Wonryeol_Helper" ^
    --hidden-import=numpy ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=customtkinter ^
    --hidden-import=mss ^
    --hidden-import=app ^
    --hidden-import=constants ^
    --hidden-import=features ^
    --hidden-import=features.belial ^
    --hidden-import=features.inventory ^
    --hidden-import=features.discard ^
    --hidden-import=features.sell ^
    --hidden-import=features.consume ^
    --hidden-import=features.consume2 ^
    --hidden-import=features.skill_auto ^
    --hidden-import=features.quick_button ^
    --hidden-import=ui ^
    --hidden-import=ui.overlay ^
    --hidden-import=ui.main_window ^
    --hidden-import=utils ^
    --hidden-import=utils.updater ^
    main.py
```

### 빌드 시 주의사항
1. **진입점은 반드시 `main.py`** (app.py 아님!)
2. 모든 로컬 모듈을 `--hidden-import`로 명시해야 함
3. `customtkinter`, `mss` 도 hidden-import 필요
4. 출력: `dist/Wonryeol_Helper.exe`

---

## 의존성 (requirements.txt)

```
pyautogui>=0.9.53      # 마우스/키보드 제어
keyboard>=0.13.5       # 전역 핫키 감시
Pillow>=9.0.0          # 이미지 처리 (색상 추출)
pywin32>=305           # Windows API
customtkinter>=5.2.0   # 모던 UI 프레임워크
mss>=9.0.0             # 화면 캡처
numpy>=1.21.0          # 배열 연산 (색상 비교)
```

---

## 버전 관리

버전은 `constants.py`에서 관리:
```python
VERSION = "1.8.6"
```

버전 변경 시 이 파일만 수정하면 됨.

---

## 기능별 핫키 (기본값)

| 기능 | 핫키 | 파일 |
|------|------|------|
| 벨리알 (색상 감지) | F4 | features/belial.py |
| 인벤토리 정리 | F3 | features/inventory.py |
| 버리기 | F1 | features/discard.py |
| 팔기 | F2 | features/sell.py |
| 먹기 V1 | Mouse5 | features/consume.py |
| 먹기 V2 | F5 | features/consume2.py |
| 스킬 자동 | F6~F10 | features/skill_auto.py |
| 긴급 정지 | F12 | app.py |

---

## 설정 파일

`color_clicker_config.json` - 모든 설정 저장
- 색상 목록, 핫키, 영역 좌표, 딜레이 등
- `app.py`의 `save_config()`, `load_config()` 메서드에서 처리

---

## 자주 하는 작업

### 버전 업데이트
1. `constants.py`의 `VERSION` 수정
2. `build_modern.bat` 실행
3. `dist/Wonryeol_Helper.exe` 배포

### 새 기능 추가
1. `features/` 폴더에 새 Mixin 파일 생성
2. `app.py`의 `ColorClickerApp`에 Mixin 상속 추가
3. `build_modern.bat`에 `--hidden-import` 추가

### UI 탭 추가
1. `ui/main_window.py`의 `setup_ui()`에서 메뉴 버튼 추가
2. `show_content()`에서 탭 콘텐츠 처리 추가

---

## 트러블슈팅

### EXE 실행 시 아무것도 안 뜨고 꺼짐
- 진입점이 `main.py`가 아닌 경우
- hidden-import 누락된 경우
- 해결: build_modern.bat 확인

### 모듈 import 에러
- 모든 로컬 모듈이 hidden-import에 포함되어야 함
- `features`, `ui`, `utils` 패키지와 각 하위 모듈 모두 포함

### 핫키 작동 안 함
- `keyboard` 라이브러리는 관리자 권한 필요할 수 있음
- 다른 프로그램과 핫키 충돌 확인
