---
description: How to run the application using uv
---

# Running with uv

When running or testing the Music Auto Formatter, you MUST use `uv run` to ensure that the correct dependencies are used from the project's virtual environment.

## Commands

### Run for a single album
// turbo
```bash
uv run python run.py "path/to/album" -o "output_dir"
```

### Run for multiple albums (batch)
// turbo
```bash
uv run python run_batch.py "path/to/input_root" -o "output_root"
```

### Keep source files
Add the `--keep-source` flag to prevent the tool from deleting the original files after successful processing.
```bash
uv run python run.py "path/to/album" --keep-source
```
