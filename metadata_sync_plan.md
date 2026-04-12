# Base Music File Metadata Sync Feature Plan

## 목표
하나의 'Base Music File'(기준 음원 파일)에서 메타데이터를 추출하여, 태그가 없는 여러 타겟 음원 파일들에 일괄 적용하는 새로운 기능 구현. 
기존 파이프라인(오디오 변환 로직 등)을 그대로 활용하되, 특정 트리거가 감지되면 메타데이터 구성 방식만 분기를 타도록 설계함.

## 주요 기능 및 구동 방식

1. **트리거 감지 (동작 분기)**
   - 앨범 디렉토리를 처리할 때 하위에 `base music example` 형태의 폴더와 기준 음원 파일(base music file)이 존재하는지 검사함.
   - 존재한다면 해당 앨범은 **Base Sync 모드**로 동작.

2. **Base Music File 메타데이터 추출**
   - 타겟 파일: `base music example` 하위의 음원 파일.
   - 타겟 태그: `Album Cover Image`(앨범 아트), `Artist`(아티스트), `Year`(연도), `Genre`(장르), `Comment/Description`(설명), `Album Artist`(앨범 아티스트), `Disc Number`(디스크 번호), `Album`(앨범명)
   - 위 기준 파일에서 메타데이터를 읽어 메모리(`consolidated` 등)에 캐싱.

3. **타겟 파일 공통 Prefix(접두사) 일반화 및 제거**
   - 앨범 디렉토리 내의 변환 대상 파일 목록의 파일명(확장자 제외)을 비교하여 공통된 Prefix(접두사)를 파악.
   - 각 파일명에서 공통 Prefix를 제거함.

4. **파일명 기반 Track Number & Title 추출**
   - Prefix가 제거된 문자열을 정규표현식(Regex)으로 파싱하여 `{track number}`와 `{title}`을 분리 (`01. Title`, `02_Title`, `3 Title` 등).
   - 예외 처리: `Title` 정보 없이 트랙 번호만 있거나, 트랙 번호가 없는 경우는 Nullable/기본값 할당 처리.

5. **기존 변환 유지 및 메타데이터 주입**
   - flac, wav ➡️ mp3 형식 변환은 `MusicFormatter`의 기존 프로세스(`_convert_and_tag`)를 그대로 활용.
   - 단, 태깅 단계(`apply_metadata`)에서 *기존 오디오 파일의 태그를 읽거나 Last.fm을 호출하는 대신*, **Base 파일에서 추출한 공통 메타데이터 + 정규식으로 얻어낸 고유 트랙 번호 및 제목**을 조합하여 주입.

## 구조 설계 및 수정 방안

- **기존 진입점 및 흐름 유지:**
  - `run.py`나 `run_batch.py`에서 별도의 스크립트를 파지 않고, `MusicFormatter.process_album`과 `.prepare_album` 단계에서 분기를 설계.
- **`MusicFormatter` / `MetadataManager` 로직 확장:**
  - `LibraryScanner` 또는 `MusicFormatter`에서 `base music example` 폴더 유무 확인.
  - 상태값(예: `is_base_sync_mode`)을 설정.
  - Base 음악 파일은 오디오 변환 대상(`files` 리스트)에서 제외하고 메타데이터 참조용으로만 분리.
  - `MetadataManager`: `get_formatted_filename` 및 `apply_metadata` 함수 내부에서 `is_base_sync_mode=True`일 경우 전용 로직을 타도록 분기문(`if`) 구성.
- **새로운 유틸리티 추가 (`src/utils/` 등):**
  - `filename_parser.py`: 여러 파일명의 공통 Prefix 도출 및 정규식을 활용한 트랙/타이틀 분리 유틸리티.

## 개발 단계 (Work Breakdown)
1. **분석 및 정규식 설계:** 
   - 파이썬의 `os.path.commonprefix`를 응용하여 파일명 공통 접두사 추출 함수 개발.
   - `{track}`과 `{title}`을 분리할 강건한 정규표현식 작성.
2. **MusicFormatter 및 Scanner 수정:** 
   - 앨범 스캔/분석 시 `base music example` 하위 구조 감지 및 Base 파일 추출 로직 작성. 타겟 파일 리스트에서 Base 폴더 내부를 제외시킴.
3. **MetadataManager 분기 개발:** 
   - Base 파일에서 지정된 태그들을 읽어들이는 기능 구현 (`mutagen` 활용).
   - Sync 모드일 때 Last.fm API 등 기존 절차를 우회하고, 수집된 Base 데이터와 파싱된 트랙/타이틀을 병합하여 ID3 형식으로 주입하도록 수정.
4. **테스트 및 검증:**
   - flac/wav 원본 파일들을 이용해 `base music example`이 존재할 때 변환(mp3) 후 메타데이터가 정상적으로 입혀지는지 검증.
