# 타이틀 하단 `그리고 터피` — 005

사용자 요청에 따라 도입 타이틀의 `and Tuffy`를 `그리고 터피`로 교체했다. 터피는 이 NES 게임 원문에서 제리의 **조카**다. 상단 `톰과 제리`와 캐릭터 그림은 기존 검증본 004 그대로 유지한다.

## 자산과 구현

원본 하단 PNG를 `extracted/title_subtitle_005/`에 추출하고, 이를 참조해 `image_gen.imagegen`으로 한글 이미지를 생성했다. 생성 원본은 `assets/title/subtitle_kr_ai_005_generated.png`, 프롬프트·출처·해시·변환 사양은 `subtitle_provenance_005.json`이다. 문구의 독립 2차 의미 검토는 `subtitle_text_005.json`에 기록했다.

고정된 생성 PNG를 밝기 120 기준으로 마스크화하고 bbox `(395,184,1777,541)`를 잘라 LANCZOS 136×28로 변환한다. 밝기 128 기준 이진화 후 216×32 캔버스 `(40,2)`에 배치한다. 기존 속성과 팔레트에 맞춰 밝은 인덱스를 선택한다. 재빌드는 생성형 서비스를 다시 호출하지 않는다.

타일 49개를 기존 하단 전용 슬롯 `$43..$73`에 넣는다. 004의 주 로고는 `$01..$42`만 사용하므로 픽셀·타일맵 모두 동일하게 보존된다. 이전 004가 Tuffy와 공유하던 패턴을 보존하기 위해 썼던 `$43/$44`도 이번에는 한글 하단 자산이 소유한다.

| 최종 쓰기 구간 | 의미 |
| --- | --- |
| `0x2023C..0x202C2` | 004에서 검증한 주 로고 타일맵 그대로 |
| `0x202C3..0x2032E` | `그리고 터피` 타일맵 27×4 |
| `0x2C820..0x2CC3F` | 004 주 로고 66타일 그대로 |
| `0x2CC40..0x2CF4F` | 하단 한글 49타일 |

004 대비 실제 변경은 **545바이트**, 원본 대비 전체 변경은 **1,284바이트**다. 코드·헤더·파일 크기는 그대로다.

## 빌드와 정적 검사

주 진입점은 `python .\scripts\build_title_subtitle.py`다. 내부에서 원본을 검증하고 `build_title.py`로 004를 재현한 뒤 그 해시를 확인한다. 최종 쓰기 네 구간은 불변 원본의 기대 해시·바이트를 검증한 다음 합친다.

전체 8,192 CHR 타일의 무수정 왕복, 보호 바이트와 주 로고 동일성, 최종 하단 디코드 픽셀, IPS 재적용 동일성을 통과했다. 같은 진입점을 다시 실행해 ROM/IPS 해시 동일성도 확인했다. 증거는 `build/title_kr_ai_005/build_report.json`, `expected_writes.json`이다.

## 실제 실행 검사

Mesen 2.2.1, 실행 파일 SHA-256 `a4a18b59c5d1bcaaedd1ad59b48daec89a3a710f0581765c9da7f5029e5f0084`. 프로젝트 전용 testRunner를 사용했다. 004의 보존 증거와 동일한 설정·프레임·입력으로 비교했다.

- 무입력: 120/300/600/900/1100/1800/2400/3600프레임.
- 3600프레임 START: 3600/3650/3750/3900/4200/4500프레임.
- 같은 START 이후 4600프레임 리셋: 4500/4600/4900/5200/5800/8200프레임.
- 총 20쌍 중 하단 로고가 있는 도입부 5쌍만 하단 사각형 `(40,188)..(208,232)` 안에서 변했다. 나머지 15쌍은 전체 화면 픽셀이 동일했다.
- 모든 쌍에서 내부 RAM·OAM·팔레트·속성 데이터가 동일했다.
- PPU 하단 타일맵 적재 결과와 활성 래스터 CHR이 최종 ROM과 일치했다.

증거: `qa/title_005/verification.json`, `comparison_005.png`, `VISUAL_REVIEW.md`. 확대 이미지는 실제 실행 PNG의 단순 최근접 확대다. 전체 플레이·실기·오디오·다른 에뮬레이터 검증은 수행하지 않았다.

## 산출물과 해시

- ROM: `build/title_kr_ai_005/Tom_Jerry_KR_title_ai_005.nes` — SHA-256 `4c20f312f5326d738c570ccfeb4c51c0aba1356151173215c7c13d03cd0c906a`.
- IPS: `dist/Tom_Jerry_KR_title_ai_005.ips` — SHA-256 `b4bdedc9248676ef5fff5e741799eac2e5cd426379561cbe230afdf34b5c15d7`.
- 실제 도입 PNG: `build/title_kr_ai_005/intro_kr_runtime.png`.
- 생성 PNG: SHA-256 `914c51c586c3df65e8e4efb2f7e792f2f524d9d827a2e45429b0de05a2e7bf81`.

원본과 004 ROM/IPS, 기존 일본어 추출 원문과 초안은 보존했다. 005 IPS는 원본 일본판에 적용하며, 004 패치본에 겹쳐 적용하지 않는다.

## 재현 명령

게임 폴더, Python 3.12.10/Pillow 12.3.0 기준이다. 기본 Mesen 경로는 `H:/Mesen/Mesen.exe`이며 `--emulator`로 바꿀 수 있다. 이전과 실행 파일 해시가 달라지면 결과를 혼합하지 않는다.

```powershell
python .\scripts\build_title_subtitle.py
python .\scripts\verify_subtitle_qa.py
```

두 번째 명령은 이번 보존 증거를 재검사한다. 새 캡처는 이전 경로를 덮어쓰지 않고 새 `--out`을 사용한다.

```powershell
python .\scripts\run_capture.py --rom .\build\title_kr_ai_005\Tom_Jerry_KR_title_ai_005.nes --out .\qa\subtitle_rerun_survey --frames 120,300,600,900,1100,1800,2400,3600 --raster
python .\scripts\run_capture.py --rom .\build\title_kr_ai_005\Tom_Jerry_KR_title_ai_005.nes --out .\qa\subtitle_rerun_gameplay --frames 3600,3650,3750,3900,4200,4500 --start 3600
python .\scripts\run_capture.py --rom .\build\title_kr_ai_005\Tom_Jerry_KR_title_ai_005.nes --out .\qa\subtitle_rerun_reset --frames 4500,4600,4900,5200,5800,8200 --start 3600 --reset 4600
```

새 캡처를 검증할 때는 `verify_subtitle_qa.py`의 후보 경로를 명시적으로 바꾸고 004 비교 기준과 기존 증거는 유지한다.
