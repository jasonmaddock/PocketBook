"""
Temporary secrets loader.
Move these into environment variables before running in any real environment.
"""

import os
from pathlib import Path


def _load_env_file(filename: str = ".env"):
    """Lightweight loader for key=value lines in .env placed beside this file."""
    env_path = Path(__file__).resolve().parent / filename
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


_load_env_file()

GOCARDLESS_SECRET_KEY = os.getenv("GOCARDLESS_SECRET_KEY", "")
GOCARDLESS_SECRET_ID = os.getenv("GOCARDLESS_SECRET_ID", "")
ALLOW_DUMMY = os.getenv("POCKETBOOK_ALLOW_DUMMY_SECRETS")

if not (GOCARDLESS_SECRET_KEY and GOCARDLESS_SECRET_ID):
    # Default to dummy values for tests/dev; real API calls will fail until env vars are set.
    GOCARDLESS_SECRET_KEY = GOCARDLESS_SECRET_KEY or "DUMMY"
    GOCARDLESS_SECRET_ID = GOCARDLESS_SECRET_ID or "DUMMY"
    if not ALLOW_DUMMY:
        print(
            "Warning: GoCardless credentials are missing. "
            "Set GOCARDLESS_SECRET_KEY and GOCARDLESS_SECRET_ID for real API calls "
            "or export POCKETBOOK_ALLOW_DUMMY_SECRETS=1 to silence this."
        )
