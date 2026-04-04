from __future__ import annotations

from pathlib import Path
import sys


API_ROOT = Path(__file__).resolve().parents[2]

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

