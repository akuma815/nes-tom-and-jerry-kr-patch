# 톰과 제리 작업 폴더 정리 인계 — 2026-10-16

사용자가 원본 ROM도 재입수할 수 있으며 Git으로 재빌드할 수 있는 파일은 모두 삭제해도 된다고 요청했다. 기존 보존 규칙에 대한 이번 요청을 적용했다.

## 정리 결과

`G:\Downloads\Korean Traslate Project\Games\Tom & Jerry` 전체를 삭제했다. 삭제 전 파일 2,372개, 132,991,440바이트를 크기·SHA-256으로 확인했고 재분석 지점은 없었다. 원본 ROM·중간 후보·로컬 QA 덤프·에뮬레이터 복사본·작업 캐시·작업 Git 복제를 포함한다. 원본을 따로 백업하지 않았다. 게임 폴더 밖의 다른 게임, 공유 Font/Tools, 사이트 작업 폴더는 삭제 대상으로 삼지 않았다.

후속 검증용 임시 복제의 정리 결과는 `clone_deletion.json`, 최종 두 경로 부재 확인은 `cleanup_final.json`에 기록한다. 이 인계와 작은 감사 기록은 작업 폴더 밖의 `docs/tom_jerry_cleanup_20261016`에 남긴다.

## 삭제 조건을 어떻게 충족했는가

처음 공개 Git에는 IPS와 적용 도구만 있어서 전체 소스 빌드 입력이 부족했다. 따라서 번역 JSON·글꼴과 OFL·고정 생성형 타이틀 PNG·출처·지원 원본 프로필·타일/텍스트/타이틀 변환 코드를 공개 Git `main`에 보완했다. 원본 ROM이나 메모리/원작 그래픽 덤프는 Git에 올리지 않았다.

완전 소스 재빌드 검증 커밋: **`29ba1ac0e5e3e14b7de19e2c0e762f8705776b51`**.

기존 폴더 밖에 Git을 새로 복제하고, 별도 원본 ROM만 제공해 `python -I -B build.py --source ...`를 실행했다. Git의 21개 고정 빌드 입력에서 새 ROM/IPS를 만들었으며 기존 008·공개 v1.0과 바이트 단위로 일치했다. 완성 IPS를 적용하는 경로로 대신하지 않았다. 잘못된 원본 거부도 확인했다.

| 구분 | SHA-256 |
| --- | --- |
| 별도 준비할 일본판 원본, 헤더 포함 262,160바이트 | `aaeceb811865b9f4736670b55cbfd4a3deae5d26374e9d10d744fc44055b524f` |
| 소스 재빌드 ROM = 정식 v1.0 | `304b67fb63ad9145fb4cb61335cfdcc46c656a7b63d106be0a45db5258a9f004` |
| 새로 생성한 IPS = 공개 IPS | `70a12bf0a48367ee1922693cfe94ce0b185c1b49d61416e3200aa8bc64e6e0d9` |
| 그대로 유지한 공개 배포 ZIP | `aeed79d1bab180dce29d2e482c2fca679e91670efde1c663bf749da64c75731a` |

## 복구 명령

Python 3.12 환경에서 **현재 main**을 복제한다. 완전 빌드 소스는 v1.0 배포 후 main에 추가했으므로 과거 v1.0 태그의 자동 Source code ZIP 대신 다음 경로를 사용한다.

```powershell
git clone https://github.com/akuma815/nes-tom-and-jerry-kr-patch.git
cd nes-tom-and-jerry-kr-patch
python -m pip install -r source/requirements.txt
python build.py --source "G:\원본 경로\Tom & Jerry (Japan).nes"
```

결과는 `output/Tom_Jerry_KR_v1.0.nes`, `.ips`, `.build.json`이다. 공유 Font 폴더·기존 작업 폴더·에뮬레이터·이미지 생성 서비스가 없어도 빌드된다. 원본 해시가 다르면 실패한다. 기존 ROM이나 다른 파일을 덮어쓰지 않는다.

[상세 공개 빌드 안내](https://github.com/akuma815/nes-tom-and-jerry-kr-patch/blob/main/docs/BUILD_FROM_SOURCE.md) · [정식 v1.0 릴리즈](https://github.com/akuma815/nes-tom-and-jerry-kr-patch/releases/tag/v1.0) · [등록된 페이지](https://akuma815.github.io/)

## 기록과 한계

- `rebuild_verification.json`: 실제 새 원격 Git 복제의 전체 소스 빌드·동일성 검증.
- `project_delete_plan.json`: 삭제 전 각 파일의 해시·크기·정확한 상대 경로.
- `project_deletion.json`: 검증한 대상의 실제 삭제 결과.
- `cleanup.ps1`: 허용한 정확한 경로·재분석 지점·파일 목록/해시·프로세스를 확인한 뒤 네이티브 PowerShell로 삭제.

Git에 남긴 것은 재빌드 입력, 핵심 작업 문서·검증 요약, 실제 공개 캡처다. 과거 실패 후보·전체 메모리 덤프·에뮬레이터 바이너리·임시 캡처 전부를 Git에 보존했다는 뜻은 아니다. 정식 결과의 소스 재빌드 가능성과 오래된 조사 캐시의 보존 여부를 구분한다.

새 에뮬레이터/게임 플레이 검증은 수행하지 않았다. 기존 v1.0의 정상 도입·첫 스테이지 진입·진단 엔딩 표시 근거만 그대로이며 정상 플레이 엔딩·전체 플레이는 여전히 미검증이다. 릴리즈 ZIP·태그와 사이트 등록은 바꾸지 않았다.

다음 행동 하나: **다시 작업할 때 위 명령으로 Git을 복제하고 지원 원본 ROM을 제공해 재빌드한다.**
