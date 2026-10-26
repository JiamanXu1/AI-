#!/usr/bin/env python3
"""Convenience adapter for the package-local Codex semantic-annotation runner."""

from __future__ import annotations

import runpy
from pathlib import Path


RUNNER = Path(__file__).resolve().parents[1] / "semantic_annotation" / "run_semantic_annotation.py"

if __name__ == "__main__":
    runpy.run_path(str(RUNNER), run_name="__main__")
