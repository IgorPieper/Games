# RTS

A simple fan-made real-time strategy prototype inspired by the Warcraft series. This project is not affiliated with Blizzard Entertainment and does not use original assets, trademarks, or code from those games.

## Features

- Playable 2D version in `rts_2d.py`.
- Experimental 3D version in `rts_3d.py`.
- Race selection, base building, resource gathering, unit production, and combat.
- Larger map, camera controls, minimap, classic RTS-style UI, and basic enemy logic.

## How to Run

### 1. Install dependencies

From the project folder, create a virtual environment and install the required packages:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Start the 2D or 3D version

The easiest way on Windows is to use the included PowerShell launchers:

```powershell
.\run_rts_2d.ps1
.\run_rts_3d.ps1
```

You can also run the games directly with Python:

```powershell
python rts_2d.py
python rts_3d.py
```

## Requirements

- Python 3.10+
- Dependencies listed in `requirements.txt`

## Status

This is a prototype meant for further development. The code focuses on playability, quick mechanics testing, and RTS system experiments.
