---
description: How to run unit tests and check coverage
---

# Unit Testing Workflow

This workflow provides instructions on how to run the unit test suite and monitor code coverage for the `MusicAutoFormatter` project.

## 1. Environment Setup
Ensure that dependencies are installed:
```bash
uv sync --dev
```

## 2. Run All Tests
To run the entire test suite:
// turbo
```bash
uv run pytest tests/
```

## 3. Run Tests with Coverage
To run tests and see which lines are still missing coverage:
// turbo
```bash
uv run pytest --cov=src --cov-report=term-missing tests/
```

## 4. Run Specific Module Tests
To run tests for a specific module (e.g., metadata):
// turbo
```bash
uv run pytest tests/metadata/
```

## 5. Guidelines
- **Isolation**: Use `unittest.mock` or `pytest-mock` to isolate tests from the filesystem and network.
- **Temporary Data**: Use the `tmp_path` fixture for tests that require real file operations.
- **Adding Tests**: When adding a new class in `src/path/to/module.py`, create a corresponding test file in `tests/path/to/test_module.py`.
