# v1.0을 번역·폰트·타이틀 입력에서 재빌드하기

현재 `main`은 완성 IPS를 적용하는 경로와 별도로 **번역 JSON·Galmuri7·선택한 생성형 타이틀 PNG·변환 코드에서 v1.0 ROM/IPS를 만드는 경로**를 포함합니다. 원본 ROM만 별도로 제공하면 됩니다. 기존 작업 폴더, 공유 `Font` 폴더, 에뮬레이터나 생성형 이미지 서비스는 빌드에 필요하지 않습니다.

## 실행

완전 빌드 소스는 v1.0 배포 후 `main`에 추가했습니다. 과거 v1.0 태그의 자동 Source code ZIP 대신 현재 저장소를 `git clone`해 사용하세요.

Python 3.12 환경에서 저장소를 복제한 후 다음을 실행합니다.

```powershell
python -m pip install -r source/requirements.txt
python build.py --source "G:\경로\Tom & Jerry (Japan).nes"
```

다른 출력 경로를 지정하려면 `--output "G:\경로\Tom_Jerry_KR_v1.0.nes"`를 추가합니다. 같은 이름의 다른 파일은 덮어쓰지 않습니다. 지원 원본의 크기·해시가 다르면 출력을 만들지 않습니다.

기본 결과:

- `output/Tom_Jerry_KR_v1.0.nes`
- `output/Tom_Jerry_KR_v1.0.ips`
- `output/Tom_Jerry_KR_v1.0.build.json`

| 구분 | SHA-256 |
| --- | --- |
| 헤더 포함 일본판 원본, 262,160바이트 | `aaeceb811865b9f4736670b55cbfd4a3deae5d26374e9d10d744fc44055b524f` |
| 재빌드 ROM = 정식 v1.0 적용 결과 | `304b67fb63ad9145fb4cb61335cfdcc46c656a7b63d106be0a45db5258a9f004` |
| 재빌드 IPS = 공개 v1.0 IPS | `70a12bf0a48367ee1922693cfe94ce0b185c1b49d61416e3200aa8bc64e6e0d9` |

## 포함된 입력과 검증

`source/assets/text`는 승인된 번역·줄바꿈 입력, `source/assets/fonts`는 고정한 글꼴과 OFL, `source/assets/title`은 실제 빌드에 쓰는 생성형 타이틀 원본과 출처입니다. `source/extracted/text_survey_001/japanese_catalog.json`은 원문 위치·문자·해시를 보존한 작은 텍스트 카탈로그이며 ROM/메모리/원작 폰트 덤프가 아닙니다. `source/config/source_rom.json`은 지원 원본을 식별합니다.

`source/BUILD_INPUTS.json`으로 입력을 검증하고, 004 → 005 → 008을 원본에서 재생성합니다. 최종 결과와 새 IPS가 공개 v1.0과 일치해야 성공합니다. 공개된 IPS는 결과 비교에만 쓰며 새 ROM을 생성하는 입력으로 적용하지 않습니다. 원본과 중간 ROM·Expected Write 자료는 로컬 무시 경로에 생성되고 Git에는 포함하지 않습니다.

시트/TTF 글자 대조·98종 문자 예산·셀 범위·스크립트 종료 위치·Expected Write·보호 범위·IPS 재적용을 검사합니다. 생성형 이미지는 다시 생성하지 않고 버전 관리된 PNG를 변환합니다. `source/docs/history/`에 작업 경위와 과거 검증 범위를 보존합니다.

재빌드는 새 게임 플레이 검증이 아닙니다. 기존 증거는 동일 바이트의 도입부 정상 부팅·첫 스테이지 진입·진단 엔딩 표시 범위이며 정상 플레이 엔딩·전체 플레이는 여전히 미검증입니다. 과거 캡처/메모리 덤프·에뮬레이터·실패 후보 같은 작업 캐시는 이 재빌드에 필요하지 않습니다.

`BUILD_INPUTS.json`은 고정 v1.0 입력의 체크섬 목록입니다. 후속 번역/그림을 수정할 때는 변경 버전의 입력 원장·기대 결과와 영향을 받은 검증을 함께 갱신해야 합니다.
