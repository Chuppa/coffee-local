"""Run lifecycle tests in a pinned official HA environment, not fabricated stubs."""
from pathlib import Path
import subprocess
ROOT = Path(__file__).resolve().parents[1]
IMAGE = 'ghcr.io/home-assistant/home-assistant:2026.10.2@sha256:33afb0659d786213264c2211f8d91c5fe87461c56eba6a3a546eb05fc71e89f4'
subprocess.run(['docker', 'run', '--rm', '--entrypoint', 'python', '-v', f'{ROOT}:/repo:ro', IMAGE, '/repo/coffee-tools/ha_lifecycle.py'], check=True)
