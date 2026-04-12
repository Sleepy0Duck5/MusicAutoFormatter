---
name: unit-testing
description: Standardized procedure for executing and managing unit tests in MusicAutoFormatter.
---

# Unit Testing Skill

This skill allows Gemini (Antigravity) to reliably execute unit tests, interpret coverage reports, and maintain the test suite for the `MusicAutoFormatter` project.

## Core Commands
- **Run all tests**: `uv run pytest tests/`
- **Check coverage**: `uv run pytest --cov=src --cov-report=term-missing tests/`
- **Module testing**: `uv run pytest tests/<module_name>/`

## Environment Variables
The `pythonpath` is already configured in `pyproject.toml`, so `uv run pytest` can be run directly from the root.

## Troubleshooting
If `pytest` fails with `INTERNALERROR`, check for global mocks of `pathlib.Path` or other built-in modules. Prefer patching specific module imports (e.g., `src.core.formatter.Path`) or using the `tmp_path` fixture.

## Maintenance
- Every new feature in `src/` must have a corresponding test in `tests/`.
- Maintain overall code coverage above 60%.
- Ensure tests use mocks for external network (httpx) and binary dependencies (ffmpeg).
