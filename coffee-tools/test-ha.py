"""Run lifecycle tests in a pinned official HA environment, not fabricated stubs."""
from pathlib import Path
import json
import re
import subprocess
ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'ghcr.io/home-assistant/home-assistant:stable'
digest = subprocess.check_output(['docker', 'buildx', 'imagetools', 'inspect', SOURCE,
                                  '--format', '{{.Manifest.Digest}}'], text=True).strip()
if not re.fullmatch(r'sha256:[a-f0-9]{64}', digest):
    raise ValueError('Invalid official stable Home Assistant image digest')
image = SOURCE + '@' + digest
(ROOT / 'work').mkdir(exist_ok=True)
(ROOT / 'work/test-image.json').write_text(json.dumps({'image': image}) + '\n')
print('Testing the exact official stable Home Assistant image: ' + image, flush=True)
subprocess.run(['docker', 'run', '--rm', '--pull=always', '--entrypoint', 'python',
                '-v', f'{ROOT}:/repo:ro', image, '/repo/coffee-tools/ha_lifecycle.py'], check=True)
