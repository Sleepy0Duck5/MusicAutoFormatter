# 고도화된 metadata.json 동기화 시스템 구현 계획서

## ✨ 목표
`metadata.json`의 유연성을 극대화하여, 기준 음악 파일(Base Music File) 유무에 상관없이 파일명 파싱, 태그 동적 삽입, 출력 파일명 커스터마이징을 완벽하게 제어할 수 있는 고도화된 Sync 시스템을 구현합니다.

---

## 🛠 주요 구조 및 제약 사항

### 1. Base Sync 모드 진입 조건 완화
- 기존: `metadata sync` 폴더 내에 **음악 파일이 존재해야만** Sync 모드가 켜짐.
- 변경: `metadata sync` 폴더 내에 **음악 파일이 없어도 `metadata.json`만 존재**한다면 Sync 모드로 진입.

### 2. 설정의 우선순위 (Priority)
태그 정보와 파일명 결정은 다음의 우선순위로 덮어씌워집니다:
1. **`metadata.json`의 `output` 규칙** (가장 우선)
2. **기준 음악 파일 (Base Music File)** (존재하는 경우)
3. **포매팅 대상 원본 파일 자체의 원본 태그 및 파일명**
*   **주의**: `metadata.json`의 `output`에 특정 필드가 명시되어 있지 않다면, 2번(기준 음악 파일) 정보를 따릅니다. 만약 기준 음악 파일마저 없다면, 3번(원본 대상 파일)의 기존 정보가 손실 없이 그대로 유지됩니다.

### 3. 표준화된 metadata.json 구조 (snake_case)
가독성 및 파이썬 명명 규칙에 맞추어 키값은 언더스코어를 사용한 `snake_case`로 통일합니다.

**예시 `metadata.json`**:
```json
{
	"input": {
		"file_name": "NA-ブルーアーカイブ Blue Archive OST %track%%sep-optional%%title-optional%"
	},
	"output": {
		"file_name": "%track%. %title%",
		"title": "%title%",
		"fallback_title": "Theme %track%",
		"artist": "%artist%",
		"year": "%year%",
		"track": "%track%",
		"genre": "%genre%",
		"comment": "%comment%",
		"album_artist": "%album_artist%",
		"composer": "%composer%",
		"disc_number": "%disc_number%"
	}
}
```

### 4. 동적 변수 치환 시스템 (Variable Substitution)
`metadata.json`의 `output` 필드 값은 다음과 같이 원본 대상 파일의 태그값 혹은 파싱된 정보로 동적 치환됩니다.
*   `%track%`: `FilenameParser`로 파일명에서 찾아낸 트랙 번호 (혹은 원본 파일의 원래 트랙)
*   `%title%`: `FilenameParser`로 파일명에서 찾아낸 제목 (없을 경우 fallback)
*   `%artist%`, `%year%`, `%genre%`, `%album_artist%` 등: 원본 오디오 파일 자체에 들어있는 원본 태그 정보
*   **파일 이름 커스텀**: `output.file_name` 필드에 `%track%. %title%`과 같이 원하는 포맷을 지정하여, 최종 출력될 파일명(확장자 제외)의 형식을 완벽하게 통제할 수 있습니다.

---

## 💻 단계별 구현 계획

### 1단계: `formatter.py` 진입 조건 리팩토링
- `_find_base_file()` 메서드를 개선하여, 음악 파일뿐만 아니라 `metadata.json` 파일이 있는지 확인하거나 이 책임을 `MetadataManager`로 위임합니다.
- `metadata sync` 폴더 경로 자체를 인지하도록 로직을 수정합니다.

### 2단계: `SyncConfig` (`src/metadata/sync_config.py`) 확장
- JSON 파싱 시 `output` 영역의 모든 키오 밸류(`file_name`, `artist`, `year` 등)를 읽어서 딕셔너리로 저장합니다.
- `render_template(template_str, variables_dict) -> str` 형태의 메서드를 추가하여, `"%artist% - %title%"` 같은 문자열을 실제 값으로 바꿔주는 엔진을 작성합니다.

### 3단계: `MetadataManager` 처리 로직 개선
- `set_base_sync_mode()`: 베이스 음악 파일이 없는 경우, 파일명 파싱만 진행하고 공통 태그/아트 추출은 건너뛰도록 처리합니다.
- **변수 추출기 도입**: `process_file()` 단계 시에 원본 오디오 파일에서 태그 값(artist, album, year 등)을 가볍게 읽어냅니다. 이를 파싱된 `track`, `title`과 병합하여 `variables_dict` 객체를 만듭니다.
- **태그 강제 주입**: 변환 전후 메타데이터를 입힐 때, `SyncConfig`가 생성해낸 렌더링된 결과값들을 기반으로 기존 ID3/FLAC 태그를 덮어씁니다.

### 4단계: 파일명 생성기 연동
- `get_formatted_filename()` 메서드가 `SyncConfig`의 `output.file_name` 템플릿을 지원하도록 수정합니다. 지정된 경우 기본 형식(`01. Title`) 대신 렌더링된 템플릿을 반환합니다.
