# Soroban Kids Trainer (Python)

Desktop app to teach kids mental math using the Japanese Soroban abacus. The app shows a timed sequence of operations and lets children solve using a visual, interactive Soroban.

## Features
- Interactive Soroban with snap beads (1 top bead + 4 lower beads per column)
- Timed operation sequences (+4, +5, -3, ...)
- Levels: Beginner, Intermediate, Advanced, Speed
- Start / Pause / Reset
- Score tracking (correct, wrong, total time)
- Learn Soroban page with guided basics

## Requirements
- Python 3.10+
- PySide6

## Install
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run
```bash
python main.py
```

## Project Structure
- `main.py`: app entry point
- `src/app.py`: app bootstrap
- `src/ui/`: main window and pages
- `src/widgets/`: Soroban widget
- `src/core/`: exercise generator
- `src/models/`: settings and level presets

## Notes
- Default language is English. Add localization later if needed.
- Progress is saved locally in the user home directory: `~/.soroban_kids_trainer/progress.json` (Windows: `C:\\Users\\YourName\\.soroban_kids_trainer\\progress.json`).
