#!/usr/bin/env python3
"""Compatibility launcher for experiment2's complete three-identity runner."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "run_three_identity_full_thread.py"
if not RUNNER.is_file():
    raise SystemExit(f"找不到完整身份实验运行器：{RUNNER}")
sys.argv[0] = str(RUNNER)
runpy.run_path(str(RUNNER), run_name="__main__")
