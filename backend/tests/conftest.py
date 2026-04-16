"""Test configuration and fixtures for FinEngine."""

import sys
from pathlib import Path

# Ensure the backend directory is in the Python path
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
