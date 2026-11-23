"""Vercel entry point: expose the Flask demo app as a serverless function."""

import sys
from pathlib import Path

# Vercel runs this file from api/, so make the repo root importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from demo.app import app  # noqa: F401
