---
description: Testing guidelines for Music Auto Formatter
---

# Music Auto Formatter Testing Workflow

When testing or running batch commands for the `MusicAutoFormatter`, you MUST adhere to the following rules to ensure safe and predictable output.

1. **Test Directory Constraint**
   Always run tests using the `test_data` folder. Do not run tests on real user libraries or production root directories by default.

2. **Input Path**
   Always use `test_data/input` as the source directory for any formatting operations.

3. **Output Path**
   Direct output to a dedicated testing output directory inside the workspace or `test_data`, such as `test_data/output`.

## Example Testing Command

Use `uv run` to ensure dependencies correspond to the project environment:

// turbo
```bash
uv run python run_batch.py test_data/input --keep-source -o test_data/output
```
