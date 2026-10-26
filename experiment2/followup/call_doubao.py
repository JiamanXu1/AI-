#!/usr/bin/env python3
"""Compatibility entry point for the multi-turn F/N/R/C questionnaire on Doubao."""
import sys

from run_followup_experiment import main


if __name__ == "__main__":
    # Doubao and DeepSeek now share the same question IDs, follow-up history,
    # evidence bank, and coding template. Use run_followup_experiment.py directly
    # when selecting a provider explicitly.
    sys.argv[1:1] = ["--provider", "doubao"]
    sys.exit(main())
