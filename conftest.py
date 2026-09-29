"""Cấu hình Pytest tự động nạp thư mục gốc dự án vào sys.path."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
