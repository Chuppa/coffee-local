"""Publish only a tested integration version; never overwrite a tag."""
import json
import os
from pathlib import Path
import subprocess
version = json.loads(Path('custom_components/coffee_local/manifest.json').read_text())['version']
repo, sha = os.environ['REPOSITORY'], os.environ['SOURCE_SHA']
tag = 'v' + version
result = subprocess.run(['gh','api',f'repos/{repo}/git/ref/tags/{tag}'],text=True,capture_output=True)
if result.returncode == 0:
    print('Version already published; bump manifest version to release an update')
    raise SystemExit(0)
if '404' not in result.stderr:
    raise RuntimeError('Cannot inspect version tag')
subprocess.run(['gh','api','--method','POST',f'repos/{repo}/git/refs','-f','ref=refs/tags/'+tag,'-f','sha='+sha],check=True)
subprocess.run(['gh','release','create',tag,'--repo',repo,'--verify-tag','--title','Coffee Local '+version,'--notes','Install and update through HACS as a custom Integration repository. Requires Coffee Local Bridge API v1. Machine firmware acceptance remains required.'],check=True)
