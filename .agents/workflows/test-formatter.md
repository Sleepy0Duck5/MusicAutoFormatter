---
description: MusicAutoFormatter의 단일 및 일괄 처리 기능을 테스트 데이터 및 원본 삭제 기능을 포함하여 검증합니다.
---

### 1. 테스트 데이터 준비 (Prepare Test Data)
원본 데이터를 `input` 폴더로 복사하여 테스트 중 원본이 손실되지 않도록 합니다.
// turbo
if (Test-Path "test_data/input") { Remove-Item -Recurse -Force "test_data/input/*" } else { New-Item -ItemType Directory -Path "test_data/input" }
// turbo
Copy-Item -Recurse -Force "test_data/original/*" "test_data/input/"

### 2. 단일 앨범 테스트 (Single Album Test)
특정 앨범 폴더 하나를 대상으로 포맷팅 및 **원본 삭제** 기능을 검증합니다.
// turbo
uv run run.py "test_data/input/[Album_Folder_Name]" -o "test_data/output_single_delete"

### 3. 일괄 처리 테스트 (Batch Processing Test)
여러 앨범이 포함된 상위 폴더를 대상으로 일괄 포맷팅 및 **원본 삭제** 기능을 검증합니다.
// turbo
uv run run_batch.py "test_data/input" -o "test_data/output_batch_delete"

### 4. 결과 확인 (Verification)
`test_data/input` 디렉토리가 비워졌는지, 그리고 `output` 폴더들에 결과물이 잘 생성되었는지 확인합니다:
- `test_data/input` 내의 원본 파일들이 삭제되었는지 확인.
- `output` 폴더들에 파일명이 정상적으로 정리되어 저장되었는지 확인.
- 로그 파일에서 `Deleting source file` 메시지가 있는지 확인.
