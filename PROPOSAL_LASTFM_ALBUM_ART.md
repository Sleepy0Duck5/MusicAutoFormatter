# [Proposal] Last.fm API를 통한 앨범 아트 자동 검색 도입

현재 본 프로젝트는 원본 오디오 파일의 태그와 로컬 폴더의 이미지 파일만으로 앨범 아트를 검색합니다. 이 제안서는 로컬 검색이 모두 실패했을 경우 **Last.fm API**를 세 번째 단계(Fallback)로 사용하여 앨범 아트를 자동으로 다운로드하고 적용하는 기능을 제안합니다.

## 1. 개요
- **목적**: 로컬에 이미지가 없는 경우 온라인 데이터베이스(Last.fm)에서 최적의 이미지를 찾아 자동 보관.
- **주요 기능**:
    - `artist`, `album` 정보를 기반으로 Last.fm API 조회.
    - 가장 큰 사이즈(`extralarge` 또는 `mega`)의 이미지 URL 추출.
    - 이미지 다운로드 및 기존 `ImageProcessor`를 통한 최적화(800x800).

## 2. 세부 구현 계획

### A. 새로운 컴포넌트 추가 (`src/metadata/lastfm_client.py`)
- **`LastFmClient` 클래스**:
    - 목적: Last.fm API 통신 담당.
    - 사용 API: `album.getInfo` (필수 파라미터: `artist`, `album`).
    - 의존성: HTTP 요청을 위해 `httpx` 라이브러리 추가 권장.
    - 리턴값: 다운로드된 이미지의 `bytes` 데이터와 `mime_type`.

### B. 기존 코드 수정
1.  **`src/metadata/metadata_processor.py`**:
    - `MetadataManager.apply_metadata` 로직에서 `cover_finder.find()` 결과가 없을 경우, `self.lastfm_client.get_album_art(artist, album)`를 호출하도록 수정.
2.  **`src/core/constants.py`**:
    - `LASTFM_API_ENDPOINT`: "https://ws.audioscrobbler.com/2.0/"
    - `LASTFM_API_KEY`: API 키를 환경 변수(`os.getenv("LASTFM_API_KEY")`)나 설정값에서 불러오도록 추가.
3.  **`pyproject.toml`**:
    - 의존성에 `httpx` 추가 (`uv add httpx`).

### C. 로직 흐름 (업데이트본)
1.  **Level 1**: 원본 오디오 태그(ID3, FLAC, MP4)에서 이미지 추출.
2.  **Level 2**: 로컬 폴더(부모 폴더 포함)에서 `cover.jpg` 등 이미지 파일 검색 (Fuzzy 매칭 포함).
3.  **Level 3 (New)**: `Level 1, 2` 실패 시, 분석된 `Artist`, `Album` 태그를 이용해 Last.fm API 호출.

## 3. 고려 사항
- **API 키 관리**: 사용자가 직접 Last.fm API 키를 발급받아 설정해야 하므로, 설정 방법 가이드가 필요함.
- **네트워크 예외 처리**: 타임아웃, API 한도 초과(Rate Limit), 결과 없음 등의 상황에 대한 안정적인 예외 처리.
- **캐싱 (선택 사항)**: 동일한 앨범을 여러 트랙 처리할 때 반복적인 API 호출을 방지하기 위한 메모리 내 캐싱.

## 4. 필요한 라이브러리 설치
```bash
uv add httpx
```
