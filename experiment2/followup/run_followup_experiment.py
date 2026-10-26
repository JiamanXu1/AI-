#!/usr/bin/env python3
"""Launch the F/N/R/C provider adapter with this folder's local study inputs."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "api" / "run_followup_experiment.py"
if not RUNNER.is_file():
    raise SystemExit(f"找不到 F/N/R/C API 运行器：{RUNNER}")
sys.argv[0] = str(RUNNER)
runpy.run_path(str(RUNNER), run_name="__main__")
